//! State shared by every connection: account ids and the (single) waiting room, so two clients can play together.
//! Minimal model for multiplayer tests (docs/progress.md section 6): every client that creates or enters a room
//! lands in the same room, slots are given in arrival order, the match starts when `PLAYERS` clients are in.

use std::sync::atomic::{AtomicU32, Ordering};
use std::sync::Mutex;

use tokio::sync::mpsc::UnboundedSender;

pub struct Member {
    pub user_id: u32,
    pub name: String,
    pub slot: u8,
    pub tx: UnboundedSender<Vec<u8>>,
    /// From C->S 92 (match start): two local IPv4 (as sent) and the client's UDP port.
    pub udp: Option<(u32, u32, u16)>,
    /// Waiting-room state sent in 106: team (C->S 89), character (C->S 90), ready (C->S 94 on the own slot).
    pub team: u8,
    pub character: u8,
    pub ready: bool,
    /// Died in the current match (C->S 120 subtype 13).
    pub dead: bool,
}

#[derive(Default)]
pub struct Room {
    pub members: Vec<Member>,
    pub started: bool,
    pub next_bomb_id: u16,
    /// Map chosen in the room (C->S 88): index into the 231 table, `CPlayMapInfoList` index. None = server default.
    pub map: Option<(u32, u16)>,
    /// Slots closed by the room master (C->S 94), bit i = slot i.
    pub closed: u16,
    /// Incremented at every match start (stale end-of-match timers compare it).
    pub match_no: u32,
    /// User id of the room master (first one in; passed on when it leaves).
    pub chief: Option<u32>,
}

pub struct Hub {
    next_user: AtomicU32,
    pub room: Mutex<Room>,
    /// Connections currently in the lobby (sent 395): they get the room list again when the room changes.
    pub lobby: Mutex<Vec<UnboundedSender<Vec<u8>>>>,
}

impl Default for Hub {
    fn default() -> Self {
        Hub { next_user: AtomicU32::new(1000), room: Mutex::new(Room::default()), lobby: Mutex::new(Vec::new()) }
    }
}

impl Hub {
    /// New account id for a login (opcode 1).
    pub fn new_user(&self) -> u32 {
        self.next_user.fetch_add(1, Ordering::SeqCst)
    }

    /// Ids handed out so far (to recognise a user on its later connections).
    pub fn known_users(&self) -> std::ops::Range<u32> {
        1000..self.next_user.load(Ordering::SeqCst)
    }

    /// Send a packet to every member of the room.
    pub fn broadcast(&self, pkt: &[u8]) {
        for m in &self.room.lock().unwrap().members {
            let _ = m.tx.send(pkt.to_vec());
        }
    }

    /// Bit i set = slot i taken (189 mode 1 block).
    pub fn slot_mask(&self) -> u16 {
        self.room.lock().unwrap().members.iter().fold(0, |m, x| m | (1 << x.slot))
    }

    pub fn next_bomb_id(&self) -> u16 {
        let mut r = self.room.lock().unwrap();
        r.next_bomb_id = r.next_bomb_id.wrapping_add(1).max(1);
        r.next_bomb_id
    }
}

impl Hub {
    /// Change one member's waiting-room state and send its 106 to the whole room (the 106 of its own slot also unlocks the
    /// client's buttons: CPrepareStage__On_106 resets this[4777] and calls vf153(1)).
    pub fn update_member(&self, user_id: u32, f: impl FnOnce(&mut Member)) {
        let pkt = {
            let mut r = self.room.lock().unwrap();
            let chief_id = r.chief;
            let Some(m) = r.members.iter_mut().find(|m| m.user_id == user_id) else { return };
            f(m);
            let chief = chief_id == Some(m.user_id);
            crate::packets::room_slot_state(m.slot, chief, m.ready, m.character, m.team)
        };
        self.broadcast(&pkt);
    }

    /// Opcode 88 for the current state: the shared room (if anybody is in it).
    pub fn room_list(&self, room_type: u8) -> Vec<u8> {
        let r = self.room.lock().unwrap();
        let rooms: Vec<crate::packets::RoomEntry> = if r.members.is_empty() {
            vec![]
        } else {
            vec![crate::packets::RoomEntry {
                session: 1,
                room_id: 1,
                name: "Phong 1".into(),
                password: false,
                playing: r.started,
                players: r.members.len() as u8,
                max_players: 8,
                room_type,
            }]
        };
        crate::packets::room_list_with(&rooms)
    }

    /// Send the room list again to everybody in the lobby (drops closed connections).
    pub fn push_room_list(&self, room_type: u8) {
        let pkt = self.room_list(room_type);
        let mut lobby = self.lobby.lock().unwrap();
        lobby.retain(|t| !t.is_closed());
        for t in lobby.iter() {
            let _ = t.send(pkt.clone());
        }
    }
}

pub fn player_name(user_id: u32) -> String {
    format!("tester{}", user_id - 1000 + 1)
}

impl Hub {
    /// End the running match `match_no` (if it is still the current one): 168 with the given ranks, then 173 after `delay` s.
    pub fn finish_match(self: &std::sync::Arc<Self>, match_no: u32, ranks: Vec<(u8, u8)>, delay: f64) -> bool {
        {
            let r = self.room.lock().unwrap();
            if !r.started || r.match_no != match_no {
                return false;
            }
        }
        self.room.lock().unwrap().match_no += 1; // a second decision (death + timeout) is ignored
        self.broadcast(&crate::packets::game_result(&ranks));
        let hub = self.clone();
        tokio::spawn(async move {
            tokio::time::sleep(std::time::Duration::from_secs_f64(delay)).await;
            {
                let mut r = hub.room.lock().unwrap();
                r.started = false;
                for m in r.members.iter_mut() {
                    m.dead = false;
                }
            }
            hub.broadcast(&crate::packets::match_over());
        });
        true
    }
}

impl Hub {
    /// Remove a member from the room (left, kicked or disconnected): S->C 104 {u8 slot, u32 id, u8 0} to everybody still in the
    /// room (`notify_self` also to the leaver: a kicked client shows "BannedByLeader" and goes back to the lobby, CPrepareStage__vf143).
    /// A new master (lowest slot) gets its 106 with the master bit. Returns the freed slot.
    pub fn leave_room(&self, user_id: u32, notify_self: bool) -> Option<u8> {
        let (slot, others, new_chief) = {
            let mut r = self.room.lock().unwrap();
            let i = r.members.iter().position(|m| m.user_id == user_id)?;
            let m = r.members.remove(i);
            let pkt = crate::packets::player_left(m.slot, user_id);
            if notify_self {
                let _ = m.tx.send(pkt.clone());
            }
            let mut new_chief = None;
            if r.members.is_empty() {
                r.started = false;
                r.map = None;
                r.closed = 0;
                r.chief = None;
            } else if r.chief == Some(user_id) {
                let next = r.members.iter().min_by_key(|m| m.slot).unwrap();
                let (id, pkt) = (next.user_id, crate::packets::room_slot_state(next.slot, true, false, next.character, next.team));
                r.chief = Some(id);
                new_chief = Some(pkt);
            }
            let others: Vec<_> = r.members.iter().map(|m| m.tx.clone()).collect();
            for t in &others {
                let _ = t.send(pkt.clone());
            }
            (m.slot, others, new_chief)
        };
        if let Some(p) = new_chief {
            for t in &others {
                let _ = t.send(p.clone());
            }
        }
        Some(slot)
    }
}

