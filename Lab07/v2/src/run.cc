#include "node_work.h"
#include "simulation.h"

#include <cassert>
#include <chrono>
#include <iostream>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <thread>
#include <unordered_map>
#include <unordered_set>

std::optional<std::pair<size_t, size_t>> Simulation::hop_count_with_min_distance(MACAddress m1, MACAddress m2) const
{
    /*
     * computed using Dijkstra
     */
    struct Info {
        MACAddress m;
        size_t hop_count;
        size_t distance;
        bool operator<(Info const& i)
        {
            return distance < i.distance;
        }
        bool operator==(Info const& i)
        {
            return m == i.m && hop_count == i.hop_count && distance == i.distance;
        }
    };

    size_t constexpr INFTY = std::numeric_limits<size_t>::max();

    std::unordered_map<MACAddress, size_t> min_distances;
    std::unordered_map<MACAddress, size_t> min_distance_counts;
    std::unordered_map<MACAddress, size_t> hop_counts;
    std::unordered_set<MACAddress> unvisited;
    for (auto r : nodes) {
        min_distances[r.first] = INFTY;
        min_distance_counts[r.first] = 0;
        hop_counts[r.first] = INFTY;
        unvisited.insert(r.first);
    }
    min_distances[m1] = 0;
    min_distance_counts[m1] = 1;
    hop_counts[m1] = 0;

    while (true) {
        size_t min_dist = INFTY;
        MACAddress m;
        for (auto j : unvisited) {
            if (min_distances[j] < min_dist) {
                min_dist = min_distances[j];
                m = j;
            }
        }
        if (min_dist == INFTY)
            break;
        if (m == m2)
            break;
        unvisited.erase(m);
        if (!nodes.at(m)->is_up)
            continue;
        for (auto r : adj.at(m)) {
            if (unvisited.count(r.first) > 0) {
                if (min_distances[r.first] > min_dist + r.second) {
                    hop_counts[r.first] = hop_counts[m] + 1;
                    min_distances[r.first] = min_dist + r.second;
                    min_distance_counts[r.first] = 1;
                } else if (min_distances[r.first] == min_dist + r.second)
                    min_distance_counts[r.first]++;
            }
        }
    }

    if (min_distance_counts[m2] > 1) {
        std::cout << "Multiple min distance paths found between " + std::to_string(m1) + " and " + std::to_string(m2) << '\n'
                  << std::flush;
        assert(false);
    }

    if (min_distances[m2] == INFTY) {
        /*
         * graph is disconnected
         */
        return std::optional<std::pair<size_t, size_t>>();
    } else
        return std::pair<size_t, size_t> { hop_counts[m2], min_distances[m2] };
}

void Simulation::run(std::istream& msgfile)
{
    std::string line;
    bool keep_going = (std::getline(msgfile, line) ? true : false);
    while (keep_going) {
        std::cout << std::string(50, '=') << '\n';

        packets_transmitted = 0;
        packets_distance = 0;
        total_packets_transmitted = 0;
        total_packets_distance = 0;
        nr_segments_wrongly_delivered = 0;

        size_t ideal_packets_transmitted = 0;
        size_t ideal_packets_distance = 0;
        size_t nr_segments_to_be_delivered = 0;

        for (auto g : nodes)
            g.second->launch_recv();
        for (auto g : nodes)
            g.second->launch_periodic();

        std::this_thread::sleep_for(std::chrono::milliseconds(delay_ms));

        do {
            std::stringstream ss(line);
            std::string type;
            ss >> type;
            if (type == "MSG") {
                MACAddress src_mac;
                IPAddress dest_ip;
                size_t count = 1;
                std::string next;
                ss >> next;
                if (next == "REPE") {
                    ss >> count;
                    ss >> src_mac >> dest_ip;
                } else {
                    src_mac = std::stoi(next);
                    ss >> dest_ip;
                }
                std::string segment;
                std::getline(ss, segment);

                bool disregard = false;

                auto it = nodes.find(src_mac);
                if (it == nodes.end())
                    throw std::invalid_argument("Bad message file: Invalid MAC '" + std::to_string(src_mac) + "', not a MAC address of a node");
                else if (!it->second->is_up) {
                    log(LogLevel::WARNING, "Node (mac:" + std::to_string(src_mac) + ") is down and cannot send segments");
                    disregard = true;
                }

                auto it2 = ip_to_mac.find(dest_ip);
                if (it2 == ip_to_mac.end())
                    throw std::invalid_argument("Bad message file: Invalid IP '" + std::to_string(dest_ip) + "', not an IP address of a node");
                else if (!nodes.at(it2->second)->is_up) {
                    log(LogLevel::WARNING, "Node (mac:" + std::to_string(it2->second) + ") is down and cannot receive segments");
                    disregard = true;
                }

                if (src_mac == it2->second)
                    throw std::invalid_argument("Bad message file: MSG with identical source and destination");

                if (!disregard) {
                    auto z = hop_count_with_min_distance(src_mac, it2->second);
                    if (z.has_value()) {
                        ideal_packets_transmitted += count * z.value().first;
                        ideal_packets_distance += count * z.value().second;
                    } else
                        log(LogLevel::WARNING, "Graph is disconnected, (ip:" + std::to_string(dest_ip) + ") is unreachable from (mac:" + std::to_string(src_mac) + ")");
                }

                nr_segments_to_be_delivered += count;
                if (count == 1) {
                    segment_delivered[{ it2->second, segment }] = false;
                    nodes[src_mac]->add_to_send_segment_queue(NodeWork::SegmentToSendInfo(dest_ip, std::vector<uint8_t>(segment.begin(), segment.end())));
                } else {
                    std::vector<NodeWork::SegmentToSendInfo> v;
                    v.reserve(count);
                    for (size_t i = 0; i < count; ++i) {
                        std::string r = segment + "#" + std::to_string(i);
                        segment_delivered[{ it2->second, r }] = false;
                        auto s = NodeWork::SegmentToSendInfo(dest_ip, std::vector<uint8_t>(r.begin(), r.end()));
                        v.push_back(s);
                    }
                    nodes[src_mac]->add_to_send_segment_queue(v);
                }
            } else if (type == "UP" || type == "DOWN")
                break;
            else
                throw std::invalid_argument("Bad message file: Unknown type line '" + type + "'");
        } while ((keep_going = (std::getline(msgfile, line) ? true : false)));

        std::this_thread::sleep_for(std::chrono::milliseconds(delay_ms));

        for (auto g : nodes)
            g.second->send_segments();

        std::this_thread::sleep_for(std::chrono::milliseconds(delay_ms));

        for (auto g : nodes)
            g.second->end_periodic();

        std::this_thread::sleep_for(std::chrono::milliseconds(delay_ms));

        for (auto g : nodes)
            g.second->end_recv();

        std::cout << std::string(50, '=') << '\n';

        log(LogLevel::INFO, "Total packets transmitted = " + std::to_string(packets_transmitted));
        log(LogLevel::INFO, "Total packet distance     = " + std::to_string(packets_distance));
        if (packets_transmitted != ideal_packets_transmitted)
            log(LogLevel::ERROR, "Ideal packets transmitted = " + std::to_string(ideal_packets_transmitted));
        if (packets_distance != ideal_packets_distance)
            log(LogLevel::ERROR, "Ideal packets distance    = " + std::to_string(ideal_packets_distance));

        size_t nr_segments_undelivered = 0;
        std::stringstream ss;
        ss << "Some segment(s) not delivered:\n";
        for (auto i : segment_delivered) {
            if (!i.second) {
                nr_segments_undelivered++;
                ss << "\tAt (mac:" << i.first.first << ") with contents:\n\t\t" << i.first.second << '\n';
            }
        }
        if (nr_segments_undelivered > 0)
            log(LogLevel::ERROR, ss.str());
        segment_delivered.clear();

        log(LogLevel::STATS, std::to_string(packets_transmitted) + " " + std::to_string(ideal_packets_transmitted));
        log(LogLevel::STATS, std::to_string(packets_distance) + " " + std::to_string(ideal_packets_distance));
        log(LogLevel::STATS, std::to_string(nr_segments_undelivered) + " " + std::to_string(nr_segments_wrongly_delivered) + " " + std::to_string(nr_segments_to_be_delivered));

        // up/down nodes
        do {
            std::stringstream ss(line);
            std::string type;
            ss >> type;
            bool is_up;
            std::string log_prefix;
            if (type == "DOWN") {
                is_up = false;
                log_prefix = "Bringing down (mac:";
            } else if (type == "UP") {
                is_up = true;
                log_prefix = "Bringing up (mac:";
            } else
                break;
            MACAddress mac;
            while (ss >> mac) {
                auto it = nodes.find(mac);
                if (it == nodes.end())
                    throw std::invalid_argument("Bad message file: Invalid node '" + std::to_string(mac) + "', not a MAC address of a node");
                log(LogLevel::INFO, log_prefix + std::to_string(mac) + ")");
                it->second->is_up = is_up;
            }
        } while ((keep_going = (std::getline(msgfile, line) ? true : false)));
    }
}
