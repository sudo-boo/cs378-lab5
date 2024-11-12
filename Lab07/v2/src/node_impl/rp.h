#ifndef RP_H
#define RP_H

#include "../node.h"
#include <vector>
#include <unordered_map>
#include <iostream>

struct RoutingEntry {
    IPAddress next_hop;
    MACAddress next_hop_MAC;
    size_t distance;
    int expiry;
};

class RPNode : public Node {
private:
    std::unordered_map<IPAddress, RoutingEntry> routing_table;
    std::unordered_map<IPAddress, MACAddress> ip_to_mac;
    const int MAX_EXPIRY = 20;
    void print_routing_table() const;
    void remove_expired_entries();
    void parse_and_validate_packet(const std::vector<uint8_t>& packet) const;
    void debug_log(const std::string& message) const;
    std::vector<uint8_t> prepare_table_packet() const;
    void update_routing_table(size_t distance_to_src, const std::unordered_map<IPAddress, RoutingEntry>& new_entries);

public:
    RPNode(Simulation* simul, MACAddress mac, IPAddress ip) : Node(simul, mac, ip) { }

    void send_segment(IPAddress dest_ip, std::vector<uint8_t> const& segment) const override;
    void receive_packet(MACAddress src_mac, std::vector<uint8_t> packet, size_t distance) override;
    void do_periodic() override;
};

#endif // RP_H
