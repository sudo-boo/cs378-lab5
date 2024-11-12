#ifndef BLASTER_H
#define BLASTER_H

#include "../node.h"

class BlasterNode : public Node {
public:
    BlasterNode(Simulation* simul, MACAddress mac, IPAddress ip) : Node(simul, mac, ip) { }

    void send_segment(IPAddress dest_ip, std::vector<uint8_t> const& segment) const override;
    void receive_packet(MACAddress src_mac, std::vector<uint8_t> packet, size_t distance) override;
};

#endif // BLASTER_H
