//! usage: boom-server [--ports 3838,4848,5858,6868] [--log logs/server.log]
//! Env (same as tools/fakeserver.py): ROOM_TYPE, MAP_INDEX, AUTO_START, TURN_START, TURN_MODE, GO_START, BEGIN_START,
//! BEGIN_OP, PLAY_START, ALL_MAPS=1 (+ BOOM_DIR, default ~/Downloads/Boom).

use std::io::Write;
use std::path::PathBuf;
use std::sync::{Arc, Mutex};

use boom_server::maps;
use boom_server::session::{self, Config, Log};

#[tokio::main]
async fn main() -> std::io::Result<()> {
    let args: Vec<String> = std::env::args().collect();
    let arg = |k: &str| args.iter().position(|a| a == k).and_then(|i| args.get(i + 1)).cloned();
    let ports: Vec<u16> = arg("--ports")
        .unwrap_or_else(|| "3838,4848,5858,6868".into())
        .split(',')
        .map(|p| p.parse().expect("port"))
        .collect();
    let log_path = PathBuf::from(arg("--log").unwrap_or_else(|| "logs/server.log".into()));
    if let Some(dir) = log_path.parent() {
        std::fs::create_dir_all(dir)?;
    }
    let file = Mutex::new(std::fs::OpenOptions::new().create(true).append(true).open(&log_path)?);
    let start = std::time::Instant::now();
    let log: Log = Arc::new(move |msg: String| {
        let line = format!("{:10.3} {msg}", start.elapsed().as_secs_f64());
        println!("{line}");
        let _ = writeln!(file.lock().unwrap(), "{line}");
    });

    let maps = if std::env::var("ALL_MAPS").as_deref() == Ok("1") {
        let dir = std::env::var_os("BOOM_DIR")
            .map(PathBuf::from)
            .unwrap_or_else(|| PathBuf::from(std::env::var_os("HOME").unwrap_or_default()).join("Downloads/Boom"));
        maps::all_battle_maps(&dir)?
    } else {
        maps::default_maps()
    };
    let cfg = Arc::new(Config::from_env(maps));
    let hub = Arc::new(boom_server::hub::Hub::default());
    log(format!("config {cfg:?}").chars().take(300).collect());

    let mut tasks = Vec::new();
    for port in ports {
        let listener = tokio::net::TcpListener::bind(("0.0.0.0", port)).await?;
        log(format!("listening on {port}"));
        let (cfg, log, hub) = (cfg.clone(), log.clone(), hub.clone());
        tasks.push(tokio::spawn(async move {
            loop {
                if let Ok((sock, _)) = listener.accept().await {
                    tokio::spawn(session::handle(sock, port, cfg.clone(), log.clone(), hub.clone()));
                }
            }
        }));
    }
    for t in tasks {
        let _ = t.await;
    }
    Ok(())
}
