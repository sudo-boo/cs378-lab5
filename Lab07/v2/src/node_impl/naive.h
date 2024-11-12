#ifndef NAIVE_H
#define NAIVE_H

#include "../node.h"

class NaiveNode : public Node {
public:
    NaiveNode(Simulation* simul, MACAddress mac, IPAddress ip) : Node(simul, mac, ip) { }

    void send_segment(IPAddress dest_ip, std::vector<uint8_t> const& segment) const override;
    void receive_packet(MACAddress src_mac, std::vector<uint8_t> packet, size_t distance) override;
    void do_periodic() override;
};

#endif // NAIVE_H
