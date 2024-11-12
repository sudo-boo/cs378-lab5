#include "rp.h"

void RPNode::send_segment(IPAddress dest_ip, std::vector<uint8_t> const& segment) const
{

}

void RPNode::receive_packet(MACAddress src_mac, std::vector<uint8_t> packet, size_t distance)
{
    printf("Received packet from %d at %d with distance %ld\n", src_mac, ip, distance);
}

void RPNode::do_periodic()
{
    printf("Broadcasting\n");
    std::string s = "BROADCAST FROM " + std::to_string(ip);
    std::vector<uint8_t> packet(s.length());
    memcpy(&packet[0], &s[0], s.length());
    broadcast_packet_to_all_neighbors(packet);
    receive_packet(mac, packet, 0);
}
