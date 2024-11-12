from scapy.all import *

# Define the DNS server and the domain to query
dns_server = "8.8.8.8"  # Google's public DNS server for demonstration
domain = "www.google.com"  # Replace with your desired domain

# Craft a DNS query for ANY record (type=255)
dns_query = IP(dst=dns_server)/UDP(dport=53)/DNS(rd=1, qd=DNSQR(qname=domain, qtype=255))

# Send the query and receive the response
print(f"Sending DNS query for ANY record type to {dns_server} for domain {domain}...")
response = sr1(dns_query, verbose=0, timeout=2)

# Check if we got a reply
if response:
    print(f"Received DNS response from {dns_server} for {domain}:")
    response.show()  # Display the details of the response
else:
    print(f"No response received from {dns_server}.")
