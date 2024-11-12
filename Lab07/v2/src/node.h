#ifndef NODE_H
#define NODE_H

#include <cstdint>
#include <string>
#include <vector>

struct Simulation;

using MACAddress = uint32_t;
using IPAddress = uint32_t;

class Node {
private:
    Simulation* simul;

public:
    virtual ~Node() = default;

    MACAddress const mac;
    IPAddress const ip;
    Node(Simulation* simul, MACAddress mac, IPAddress ip)
        : simul(simul), mac(mac), ip(ip) { }

    /*
     * XXX implement these
     */
    virtual void send_segment(IPAddress dest_ip, std::vector<uint8_t> const& segment) const = 0;
    virtual void receive_packet(MACAddress src_mac, std::vector<uint8_t> packet, size_t distance) = 0;

    /*
     * XXX implement this if you need to do something periodically
     */
    virtual void do_periodic() { };

protected:
    /*
     * use this to send a packet to a neighbor
     * set `contains_segment` to true to indicate to the simulator
     *      that this packet contains a segment
     *      (as opposed to protocol-related packets)
     * for reference see node_impl/naive.cc
     */
    void send_packet(MACAddress dest_mac, std::vector<uint8_t> const& packet, bool contains_segment) const;

    /*
     * use this in your implementation of receive_packet when you receive a segment
     * this will be used to verify that segments are being routed correctly
     * for reference see node_impl/naive.cc
     */
    void receive_segment(IPAddress src_ip, std::vector<uint8_t> const& segment) const;

    /*
     * use this to broadcast to all neighbours
     * set `contains_segment` to true to indicate to the simulator
     *      that this packet contains a segment
     *      (as opposed to protocol-related packets)
     * for reference see node_impl/naive.cc
     */
    void broadcast_packet_to_all_neighbors(std::vector<uint8_t> const& packet, bool contains_segment) const;

    /*
     * use this for debugging (writes logs to a file named "node-`mac`.log")
     */
    void log(std::string) const;
};

#endif // NODE_H
