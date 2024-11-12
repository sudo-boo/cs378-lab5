#include "node.h"
#undef send_packet
#undef broadcast_packet_to_all_neighbors

#include "node_impl/blaster.h"
#include "node_impl/naive.h"
#include "node_impl/rp.h"
#include "node_work.h"
#include "simulation.h"

#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <string>
#include <vector>

void Simulation::log(LogLevel l, std::string logline) const
{
    if (grading_view && l != LogLevel::STATS)
        return;
    if (!grading_view && l == LogLevel::STATS)
        return;
    std::lock_guard<std::mutex> lg(log_mt);
    if (grading_view) {
        std::cout << logline << '\n'
                  << std::flush;
        return;
    }
    std::string ll;
    switch (l) {
    case LogLevel::DEBUG:
        ll = "\x1b[34;1m[DEBUG] \x1b[0m";
        break;
    case LogLevel::INFO:
        ll = "\x1b[34;1m[INFO] \x1b[0m";
        break;
    case LogLevel::EVENT:
        ll = "\x1b[32;1m[EVENT] \x1b[0m";
        break;
    case LogLevel::WARNING:
        ll = "\x1b[31;1m[WARNING] \x1b[0m";
        break;
    case LogLevel::ERROR:
        ll = "\x1b[31;1;5m[ERROR] \x1b[0m";
        break;
    case LogLevel::STATS:
        __builtin_unreachable();
    }
    std::cout << ll << logline << '\n'
              << std::flush;
}

void Node::send_packet(MACAddress dest_mac, std::vector<uint8_t> const& packet, char const* caller_name) const
{
    simul->send_packet(this->mac, dest_mac, packet, std::string("do_periodic") == caller_name);
}
void Node::broadcast_packet_to_all_neighbors(std::vector<uint8_t> const& packet, char const* caller_name) const
{
    simul->broadcast_packet_to_all_neighbors(this->mac, packet, std::string("do_periodic") == caller_name);
}
void Node::receive_segment(IPAddress src_ip, std::vector<uint8_t> const& segment) const
{
    simul->verify_received_segment(src_ip, this->mac, segment);
}
void Node::log(std::string logline) const
{
    simul->node_log(this->mac, logline);
}
void Simulation::send_packet(MACAddress src_mac, MACAddress dest_mac, std::vector<uint8_t> const& packet, bool from_do_periodic)
{
    if (nodes.count(dest_mac) == 0) {
        log(LogLevel::ERROR, "Attempted to send to MAC address '" + std::to_string(dest_mac) + "' which is not a MAC address of any node");
        return;
    }

    auto const& b = adj[src_mac];
    auto it = b.find(dest_mac);
    if (it == b.end()) {
        log(LogLevel::ERROR, "Attempted to send to MAC address '" + std::to_string(dest_mac) + "' which is not a MAC address of any neighbour of (mac:" + std::to_string(src_mac) + ")");
        return;
    }

    NodeWork* dest_nt = nodes.at(dest_mac);

    if (!dest_nt->is_up) {
        log(LogLevel::ERROR, "Attempted to send to (mac:" + std::to_string(dest_mac) + ") which is down");
        return;
    }

    total_packets_transmitted++;
    total_packets_distance += it->second;
    if (!from_do_periodic) {
        packets_transmitted++;
        packets_distance += it->second;
    }

    dest_nt->receive_packet(src_mac, packet, it->second);
}
void Simulation::broadcast_packet_to_all_neighbors(MACAddress src_mac, std::vector<uint8_t> const& packet, bool from_do_periodic)
{
    for (auto r : adj.at(src_mac)) {
        MACAddress dest_mac = r.first;

        total_packets_transmitted++;
        total_packets_distance += r.second;
        if (!from_do_periodic) {
            packets_transmitted++;
            packets_distance += r.second;
        }

        nodes.at(dest_mac)->receive_packet(src_mac, packet, r.second);
    }
}
void Simulation::verify_received_segment(IPAddress src_ip, MACAddress dest_mac, std::vector<uint8_t> const& segment)
{
    std::string segment_str(segment.begin(), segment.end());

    auto it = segment_delivered.find({ dest_mac, segment_str });
    if (it == segment_delivered.end()) {
        log(LogLevel::ERROR, "Segment from (ip:" + std::to_string(src_ip) + ") wrongly delivered to (mac:" + std::to_string(dest_mac) + ") with contents:\n\t" + segment_str);
        nr_segments_wrongly_delivered++;
    } else {
        std::string logline = "(mac:" + std::to_string(dest_mac) + ") received segment from (ip:" + std::to_string(src_ip) + ") with contents:\n\t" + segment_str;
        if (it->second)
            logline = "{Duplicate delivery} " + logline;
        it->second = true;
        log(LogLevel::EVENT, logline);
    }
}

void Simulation::node_log(MACAddress mac, std::string logline) const
{
    auto p = nodes.at(mac);
    if (node_log_enabled && !p->log(logline))
        log(LogLevel::WARNING, "Too many logs emitted at (mac:" + std::to_string(mac) + "), no more logs will be written");
}

Simulation::Simulation(NT node_type, bool node_log_enabled, std::string node_log_file_prefix, std::istream& net_spec, size_t delay_ms, bool grading_view)
    : grading_view(grading_view), delay_ms(delay_ms), node_log_enabled(node_log_enabled), node_log_file_prefix(node_log_file_prefix)
{
    size_t nr_nodes, nr_edges;
    net_spec >> nr_nodes;
    for (size_t i = 0; i < nr_nodes; ++i) {
        MACAddress mac;
        IPAddress ip;
        net_spec >> mac >> ip;
        if (adj.count(mac) > 0)
            throw std::invalid_argument(std::string("Bad network file: MAC '") + std::to_string(mac) + "' repeated");
        if (ip_to_mac.count(ip) > 0)
            throw std::invalid_argument(std::string("Bad network file: IP '") + std::to_string(ip) + "' repeated");
        adj[mac] = {};
        ip_to_mac[ip] = mac;
    }
    net_spec >> nr_edges;
    for (size_t i = 0; i < nr_edges; ++i) {
        MACAddress m1, m2;
        size_t distance;
        net_spec >> m1 >> m2 >> distance;
        if (adj[m1].count(m2) > 0)
            throw std::invalid_argument(std::string("Bad network file: Edge between (mac:'") + std::to_string(m1) + "),(mac:" + std::to_string(m2) + ") repeated");
        adj[m1][m2] = distance;
        adj[m2][m1] = distance;
    }

    for (auto const& i : ip_to_mac) {
        IPAddress ip = i.first;
        MACAddress mac = i.second;
        Node* node = nullptr;

        switch (node_type) {
        case NT::NAIVE:
            node = new NaiveNode(this, mac, ip);
            break;
        case NT::BLASTER:
            node = new BlasterNode(this, mac, ip);
            break;
        case NT::RP:
            node = new RPNode(this, mac, ip);
            break;
        }

        std::ostream* log_stream = nullptr;
        if (node_log_enabled) {
            log_stream = new std::ofstream(node_log_file_prefix + std::to_string(mac) + ".log");
            (*log_stream) << std::setprecision(2) << std::fixed;
        }
        nodes[mac] = new NodeWork(node, log_stream);
    }
}
Simulation::~Simulation()
{
    for (auto const& g : nodes)
        delete g.second;
}
