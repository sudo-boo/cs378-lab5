#ifndef SIMULATION_H
#define SIMULATION_H

#include "node.h"
#undef send_packet
#undef broadcast_packet_to_all_neighbors

#include <atomic>
#include <map>
#include <mutex>
#include <optional>
#include <string>
#include <unordered_map>
#include <utility>

class NodeWork;

struct Simulation {
private:
    bool const grading_view;
    size_t const delay_ms;
    bool const node_log_enabled;
    std::string const node_log_file_prefix;

    std::unordered_map<MACAddress, NodeWork*> nodes;
    std::unordered_map<IPAddress, MACAddress> ip_to_mac;
    std::unordered_map<MACAddress, std::unordered_map<MACAddress, size_t>> adj;

    std::map<std::pair<MACAddress, std::string>, bool> segment_delivered;

    std::atomic<size_t> packets_transmitted = 0;
    std::atomic<size_t> packets_distance = 0;
    std::atomic<size_t> total_packets_transmitted = 0;
    std::atomic<size_t> total_packets_distance = 0;
    std::atomic<size_t> nr_segments_wrongly_delivered = 0;

    mutable std::mutex log_mt;
    enum class LogLevel {
        DEBUG,
        INFO,
        STATS,
        EVENT,
        WARNING,
        ERROR,
    };
    void log(LogLevel l, std::string logline) const;

    std::optional<std::pair<size_t, size_t>> hop_count_with_min_distance(MACAddress m1, MACAddress m2) const;

public:
    enum class NT {
        NAIVE,
        BLASTER,
        RP,
    };
    Simulation(NT node_type, bool log_enabled, std::string logfile_prefix, std::istream& net_spec, size_t delay_ms, bool grading_view);
    void run(std::istream& msg_file);
    ~Simulation();

    void send_packet(MACAddress src_mac, MACAddress dest_mac, std::vector<uint8_t> const& packet, bool from_do_periodic);
    void broadcast_packet_to_all_neighbors(MACAddress src_mac, std::vector<uint8_t> const& packet, bool from_do_periodic);
    void verify_received_segment(IPAddress src_ip, MACAddress dest_mac, std::vector<uint8_t> const& segment);
    void node_log(MACAddress, std::string logline) const;
};

#endif // SIMULATION_H
