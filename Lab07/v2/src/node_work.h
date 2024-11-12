#ifndef NODE_WORK_H
#define NODE_WORK_H

#include "node.h"

#include <condition_variable>
#include <cstdint>
#include <mutex>
#include <ostream>
#include <queue>
#include <thread>

class NodeWork {
public:
    // we need to ensure that `send_segment` and `receive_packet` calls on `node`
    // are synchronised so that the extended implementation does not have to perform
    // locking on data structures
    std::mutex node_mt;
    Node* node;
    bool is_up;

    struct SegmentToSendInfo {
        IPAddress dest_ip;
        std::vector<uint8_t> segment;
        SegmentToSendInfo(IPAddress ip, std::vector<uint8_t> const& segment) : dest_ip(ip), segment(segment) { }
    };

private:
    struct PacketReceivedInfo {
        MACAddress src_mac;
        size_t dist;
        std::vector<uint8_t> packet;
        PacketReceivedInfo(MACAddress src_mac, size_t dist, std::vector<uint8_t> const& packet)
            : src_mac(src_mac), dist(dist), packet(packet) { }
    };

    std::queue<PacketReceivedInfo> inbound;
    std::mutex inbound_mt;
    std::condition_variable inbound_cv;
    std::thread receive_thread;
    void receive_loop();
    bool recv_on;

    std::vector<SegmentToSendInfo> outbound;

    std::thread periodic_thread;
    void periodic_loop();
    bool periodic_on;

    mutable std::mutex log_mt;
    size_t loglineno;
    std::ostream* logger;

public:
    NodeWork(Node* node, std::ostream* logger)
        : node(node), is_up(true),
          recv_on(false), periodic_on(false),
          loglineno(1), logger(logger)
    {
    }
    ~NodeWork();

    void send_segments();
    void launch_recv();
    void launch_periodic();
    void end_recv();
    void end_periodic();

    void add_to_send_segment_queue(std::vector<SegmentToSendInfo> const& outbound);
    void add_to_send_segment_queue(SegmentToSendInfo outbound);

    void receive_packet(MACAddress src_mac, std::vector<uint8_t> const& packet, size_t dist);
    bool log(std::string logline);
};

#endif // NODE_WORK_H
