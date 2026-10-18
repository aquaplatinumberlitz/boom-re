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
}

#[derive(Default)]
pub struct Room {
    pub members: Vec<Member>,
    pub started: bool,
    pub next_bomb_id: u16,
}

pub struct Hub {
    next_user: AtomicU32,
    pub room: Mutex<Room>,
}

impl Default for Hub {
    fn default() -> Self {
        Hub { next_user: AtomicU32::new(1000), room: Mutex::new(Room::default()) }
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

pub fn player_name(user_id: u32) -> String {
    format!("tester{}", user_id - 1000 + 1)
}
