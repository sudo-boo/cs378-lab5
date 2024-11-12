from scapy.all import *

# Define the target IP address (replace with your desired IP)
target_ip = "8.8.8.8"  # Google's public DNS server for demonstration

# Craft the ICMP Echo Request (ping)
icmp_request = IP(dst=target_ip)/ICMP()

# Send the ICMP request and wait for a response
print(f"Sending ICMP Echo Request to {target_ip}...")
response = sr1(icmp_request, timeout=2, verbose=0)

# Check if we received an ICMP Echo Reply
if response:
    print(f"Received ICMP Echo Reply from {target_ip}:")
    response.show()  # Display the details of the received packet
else:
    print(f"No response received from {target_ip}.")
