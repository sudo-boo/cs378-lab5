#include "node_work.h"
#include "simulation.h"

#include <chrono>
#include <iostream>
#include <mutex>
#include <queue>
#include <thread>

static size_t constexpr MAX_NODE_LOG_LINES = 20000;

void NodeWork::send_segments()
{
    if (!is_up) {
        outbound.clear();
        return;
    }
    for (auto const& f : outbound) {
        node_mt.lock();
        node->send_segment(f.dest_ip, f.segment);
        node_mt.unlock();
    }
    outbound.clear();
}

void NodeWork::receive_loop()
{
    if (!is_up)
        return;
    while (true) {
        std::unique_lock<std::mutex> ul(inbound_mt);
        inbound_cv.wait(ul, [this] { return inbound.size() > 0 || !recv_on; });
        if (inbound.size() == 0 && !recv_on)
            break;
        while (inbound.size() > 0) {
            PacketReceivedInfo f = inbound.front();
            inbound.pop();
            ul.unlock();
            node_mt.lock();
            node->receive_packet(f.src_mac, f.packet, f.dist);
            node_mt.unlock();
            ul.lock();
        }
    }
}

void NodeWork::periodic_loop()
{
    if (!is_up)
        return;
    while (periodic_on) {
        node_mt.lock();
        node->do_periodic();
        node_mt.unlock();
        std::this_thread::sleep_for(std::chrono::microseconds(100));
    }
}

void NodeWork::launch_recv()
{
    if (!recv_on) {
        recv_on = true;
        inbound = std::queue<PacketReceivedInfo>();
        receive_thread = std::thread(&NodeWork::receive_loop, this);
    }
}
void NodeWork::launch_periodic()
{
    if (!periodic_on) {
        periodic_on = true;
        periodic_thread = std::thread(&NodeWork::periodic_loop, this);
    }
}

void NodeWork::end_recv()
{
    if (recv_on) {
        std::unique_lock<std::mutex> ul(inbound_mt);
        recv_on = false;
        ul.unlock();
        inbound_cv.notify_one();
        receive_thread.join();
    }
}
void NodeWork::end_periodic()
{
    if (periodic_on) {
        periodic_on = false;
        periodic_thread.join();
    }
}

NodeWork::~NodeWork()
{
    end_periodic();
    end_recv();
    delete node;
    delete logger;
}

void NodeWork::add_to_send_segment_queue(std::vector<SegmentToSendInfo> const& o)
{
    if (!is_up)
        return;
    outbound.insert(outbound.end(), o.begin(), o.end());
}
void NodeWork::add_to_send_segment_queue(SegmentToSendInfo o)
{
    if (!is_up)
        return;
    outbound.push_back(o);
}

void NodeWork::receive_packet(MACAddress src_mac, std::vector<uint8_t> const& packet, size_t dist)
{
    std::unique_lock<std::mutex> ul(inbound_mt);
    inbound.push(PacketReceivedInfo { src_mac, dist, packet });
    ul.unlock();
    inbound_cv.notify_one();
}

/*
 * returns false when log limit is exceeded for the first time
 */
bool NodeWork::log(std::string logline)
{
    std::unique_lock<std::mutex> ul(log_mt);
    if (logger == nullptr)
        return true;
    else if (loglineno >= MAX_NODE_LOG_LINES) {
        delete logger;
        logger = nullptr;
        return false;
    }
    (*logger) << '[' << loglineno++ << "] " << logline << '\n'
              << std::flush;
    return true;
}
