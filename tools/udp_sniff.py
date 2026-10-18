"""Listen on UDP ports and log every datagram (who sends what to the 'UDP ports' of opcode 15).
usage: python3 tools/udp_sniff.py <log> port [port ...]"""
import socket, select, sys, time
log = open(sys.argv[1], "a", buffering=1)
socks = []
for p in sys.argv[2:]:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("0.0.0.0", int(p)))
    socks.append(s)
while True:
    r, _, _ = select.select(socks, [], [], 1)
    for s in r:
        data, addr = s.recvfrom(65536)
        log.write(f"{time.strftime('%H:%M:%S')} port {s.getsockname()[1]} from {addr} {len(data)}B {data[:64].hex()}\n")
