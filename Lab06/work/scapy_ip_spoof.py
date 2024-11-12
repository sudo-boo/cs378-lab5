from scapy.all import *

# Define the target IP and the spoofed source IP
target_ip = "192.168.1.1"   # Any target IP address
spoofed_ip = "1.2.3.4"      # Spoofed source IP address

# Craft a TCP SYN packet
tcp_syn_packet = IP(src=spoofed_ip, dst=target_ip) / TCP(sport=12345, dport=80, flags='S')

# Send the packet
send(tcp_syn_packet, verbose=0)

print(f"SYN packet sent from {spoofed_ip} to {target_ip}.")
