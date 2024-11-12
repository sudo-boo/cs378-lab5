#include "blaster.h"

#include <cstring>

#define MAX_TTL 5

/*
 * DON'T DO THIS, this is just illustrative of how to extend the Node class
 * This broadcasts every packet that it receives that isn't intended for it
 * with a TTL to ensure packets don't last forever
 */

struct BlasterPacketHeader {
private:
    BlasterPacketHeader() = default;

public:
    IPAddress src_ip;
    IPAddress dest_ip;
    size_t ttl;

    BlasterPacketHeader(IPAddress src_ip, IPAddress dest_ip)
        : src_ip(src_ip), dest_ip(dest_ip), ttl(MAX_TTL) { }
    static BlasterPacketHeader from_bytes(uint8_t const* bytes)
    {
        BlasterPacketHeader ph;
        memcpy(&ph, bytes, sizeof(ph));
        return ph;
    }
};

void BlasterNode::send_segment(IPAddress dest_ip, std::vector<uint8_t> const& segment) const
{
    BlasterPacketHeader ph(ip, dest_ip);
    std::vector<uint8_t> packet(sizeof(ph) + segment.size());
    memcpy(&packet[0], &ph, sizeof(ph));
    memcpy(&packet[sizeof(ph)], &segment[0], segment.size());
    broadcast_packet_to_all_neighbors(packet);
}
void BlasterNode::receive_packet(MACAddress src_mac, std::vector<uint8_t> packet, size_t distance)
{
    BlasterPacketHeader ph = BlasterPacketHeader::from_bytes(&packet[0]);
    if (ph.dest_ip == ip) {
        std::vector<uint8_t> segment(packet.begin() + sizeof(ph), packet.end());
        receive_segment(ph.src_ip, segment);
    } else if (ph.ttl == 0)
        log("Packet dropped");
    else {
        ph.ttl--;
        memcpy(&packet[0], &ph, sizeof(ph));
        broadcast_packet_to_all_neighbors(packet);
    }
}
