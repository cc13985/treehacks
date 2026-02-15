#!/usr/bin/env python3
"""Minimal UDP listener on 127.0.0.1:5005. Run this to verify Node-RED is sending.
   Usage: python udp_listener_test.py
   Then in Node-RED: inject APPROACH into your UDP-out node. You should see lines here."""
import socket

UDP_IP = "127.0.0.1"
UDP_PORT = 5005

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))
print(f"Listening on {UDP_IP}:{UDP_PORT}. Inject APPROACH/REFUSE/RELEASE from Node-RED...")
print("-" * 50)
while True:
    data, addr = sock.recvfrom(1024)
    raw = data.decode("utf-8", errors="replace").strip()
    print(f"RECV: {raw!r}  (from {addr})")
