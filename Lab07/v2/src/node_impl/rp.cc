#include "rp.h"
#include <cassert>
#include <cstring>

struct RPPacketHeader {
    bool is_routing_table;
    IPAddress src_ip;
    IPAddress dest_ip;

    RPPacketHeader(IPAddress src_ip, IPAddress dest_ip, bool is_table)
        : is_routing_table(is_table), src_ip(src_ip), dest_ip(dest_ip) { }
    
    static RPPacketHeader from_bytes(const uint8_t* bytes) {
        RPPacketHeader header(0, 0, false);
        memcpy(&header, bytes, sizeof(header));
        return header;
    }
};

void RPNode::debug_log(const std::string& message) const {
    if (ip == 1000) {
        std::cout << message << std::endl;
    }
}

void RPNode::remove_expired_entries() {
    debug_log("[DEBUG] Removing expired entries from the routing table");
    for (auto it = routing_table.begin(); it != routing_table.end();) {
        --(it->second.expiry); // Decrement expiry
        if (it->second.expiry <= 0) {
            debug_log("[DEBUG] Entry for dest_ip " + std::to_string(it->first) + " has expired and will be removed");
            it = routing_table.erase(it); // Remove entry if expired
        } else {
            ++it; // Move to the next entry if not expired
        }
    }
    debug_log("[DEBUG] Expired entries removed");
}

void RPNode::print_routing_table() const {
    if (ip == 1000){
        std::cout << "Routing Table for Node with IP: " << ip << std::endl;
        std::cout << "---------------------------------------" << std::endl;
        std::cout << "Destination IP  |  Next Hop IP  |  Next Hop MAC  |  Distance  |  Expiry" << std::endl;
        std::cout << "---------------------------------------" << std::endl;

        for (const auto& entry : routing_table) {
            std::cout << entry.first << "   |   " 
                    << entry.second.next_hop << "   |   "
                    << entry.second.next_hop_MAC << "   |   "
                    << entry.second.distance << "   |   "
                    << entry.second.expiry << std::endl;
        }
        std::cout << "---------------------------------------" << std::endl;
    }
}
// Assumed sizes for IPAddress and MACAddress, adjust as necessary
constexpr size_t IP_SIZE = 4;  // e.g., 32-bit
constexpr size_t MAC_SIZE = 4; // e.g., 32-bit
constexpr size_t DISTANCE_SIZE = sizeof(size_t); // Ensure this matches distance's storage size

// Parsing function with offsets
void RPNode::parse_and_validate_packet(const std::vector<uint8_t>& packet) const {
    const uint8_t* ptr = packet.data();

    // Parsing Self Entry
    IPAddress parsed_self_ip;
    MACAddress parsed_self_mac;
    size_t parsed_self_distance;

    memcpy(&parsed_self_ip, ptr, IP_SIZE);
    ptr += IP_SIZE;
    memcpy(&parsed_self_mac, ptr, MAC_SIZE);
    ptr += MAC_SIZE;
    memcpy(&parsed_self_distance, ptr, DISTANCE_SIZE);
    ptr += DISTANCE_SIZE;

    debug_log("[PARSE CHECK] Parsed Self IP: " + std::to_string(parsed_self_ip));
    debug_log("[PARSE CHECK] Parsed Self MAC: " + std::to_string(parsed_self_mac));
    debug_log("[PARSE CHECK] Parsed Self Distance: " + std::to_string(parsed_self_distance));

    // Parsing Routing Table Entries
    while (ptr < packet.data() + packet.size()) {
        IPAddress dest_ip;
        MACAddress next_hop_mac;
        size_t distance;
        
        memcpy(&dest_ip, ptr, IP_SIZE);
        ptr += IP_SIZE;
        memcpy(&next_hop_mac, ptr, MAC_SIZE);
        ptr += MAC_SIZE;
        memcpy(&distance, ptr, DISTANCE_SIZE);
        ptr += DISTANCE_SIZE;

        debug_log("[PARSE CHECK] Parsed Destination IP: " + std::to_string(dest_ip));
        debug_log("[PARSE CHECK] Parsed Next Hop MAC: " + std::to_string(next_hop_mac));
        debug_log("[PARSE CHECK] Parsed Distance: " + std::to_string(distance));
    }
}

std::vector<uint8_t> RPNode::prepare_table_packet() const {
    debug_log("[DEBUG] Preparing table packet");
    std::vector<uint8_t> packet;

    IPAddress self_ip = ip;
    MACAddress self_mac = mac;
    size_t self_distance = 0;

    packet.insert(packet.end(), (uint8_t*)&self_ip, (uint8_t*)&self_ip + sizeof(self_ip));
    packet.insert(packet.end(), (uint8_t*)&self_mac, (uint8_t*)&self_mac + sizeof(self_mac));
    packet.insert(packet.end(), (uint8_t*)&self_distance, (uint8_t*)&self_distance + sizeof(self_distance));

    for (const auto& entry : routing_table) {
        IPAddress dest_ip = entry.first;
        MACAddress next_hop_mac = entry.second.next_hop_MAC;
        size_t distance = entry.second.distance;

        packet.insert(packet.end(), (uint8_t*)&dest_ip, (uint8_t*)&dest_ip + sizeof(dest_ip));
        packet.insert(packet.end(), (uint8_t*)&next_hop_mac, (uint8_t*)&next_hop_mac + sizeof(next_hop_mac));
        packet.insert(packet.end(), (uint8_t*)&distance, (uint8_t*)&distance + sizeof(distance));

        debug_log("[DEBUG] Added to packet: dest_ip=" + std::to_string(dest_ip) +
                  ", next_hop_mac=" + std::to_string(next_hop_mac) +
                  ", distance=" + std::to_string(distance));
    }

    parse_and_validate_packet(packet); // Parse immediately to validate

    debug_log("[DEBUG] Table packet prepared with " + std::to_string(packet.size()) + " bytes");
    return packet;
}


void RPNode::update_routing_table(size_t distance_to_src, const std::unordered_map<IPAddress, RoutingEntry>& new_entries) {
    debug_log("[DEBUG] IN UPDATE, routing table with distance to source: " + std::to_string(distance_to_src));
    for (const auto& entry : new_entries) {
        IPAddress dest_ip = entry.first;
        const RoutingEntry& new_entry = entry.second;
        size_t proposed_distance = distance_to_src + new_entry.distance;

        debug_log("[DEBUG] Considering update for dest_ip " + std::to_string(dest_ip) + " with proposed distance: " + std::to_string(new_entry.distance));

        // Check if a shorter route is offered
        if (routing_table.find(dest_ip) == routing_table.end() || proposed_distance < routing_table[dest_ip].distance) {
            routing_table[dest_ip] = {new_entry.next_hop, new_entry.next_hop_MAC, proposed_distance, MAX_EXPIRY};
            ip_to_mac[dest_ip] = new_entry.next_hop_MAC;
debug_log("[DEBUG] Routing entry updated for dest_ip " + std::to_string(dest_ip)
          + " with next hop MAC: " + std::to_string(entry.second.next_hop_MAC)
          + " and distance: " + std::to_string(proposed_distance));

        } else {
            debug_log("[DEBUG] Existing route is shorter or equal for dest_ip " + std::to_string(dest_ip));
        }
    }
    remove_expired_entries();
    print_routing_table();
}

void RPNode::send_segment(IPAddress dest_ip, std::vector<uint8_t> const& segment) const {
    debug_log("[DEBUG] Sending segment to dest_ip " + std::to_string(dest_ip));
    if (routing_table.find(dest_ip) != routing_table.end()) {
        const RoutingEntry& entry = routing_table.at(dest_ip);
        MACAddress next_hop_mac = ip_to_mac.at(entry.next_hop);

        RPPacketHeader header(ip, dest_ip, false);
        std::vector<uint8_t> packet(sizeof(header) + segment.size());
        memcpy(&packet[0], &header, sizeof(header));
        memcpy(&packet[sizeof(header)], segment.data(), segment.size());

        send_packet(next_hop_mac, packet, true);
        debug_log("[DEBUG] Packet sent to next hop MAC " + next_hop_mac);
    } else {
        debug_log("[DEBUG] No route found for dest_ip " + std::to_string(dest_ip) + ", broadcasting packet");
        RPPacketHeader header(ip, 0, false);
        std::vector<uint8_t> packet(sizeof(header) + segment.size());
        memcpy(&packet[0], &header, sizeof(header));
        memcpy(&packet[sizeof(header)], segment.data(), segment.size());

        broadcast_packet_to_all_neighbors(packet, true);
    }
}

void RPNode::receive_packet(MACAddress src_mac, std::vector<uint8_t> packet, size_t distance) {
    debug_log("[DEBUG] Received packet from src_mac " + std::to_string(src_mac) + " with distance " + std::to_string(distance));
    RPPacketHeader header = RPPacketHeader::from_bytes(packet.data());
    debug_log("[DEBUG] Packet header: is_routing_table=" + std::to_string(header.is_routing_table)
              + ", src_ip=" + std::to_string(header.src_ip) + ", dest_ip=" + std::to_string(header.dest_ip));

    if (header.is_routing_table) {
        debug_log("[DEBUG] Received a routing table packet");
        std::unordered_map<IPAddress, RoutingEntry> new_entries;
        const uint8_t* ptr = packet.data() + sizeof(header);

        while (ptr < packet.data() + packet.size()) {
            IPAddress dest_ip;
            RoutingEntry entry;

            memcpy(&dest_ip, ptr, sizeof(dest_ip));
            debug_log("[DEBUG] Parsed dest_ip: " + std::to_string(dest_ip));
            ptr += sizeof(dest_ip);

            memcpy(&entry.next_hop, ptr, sizeof(entry.next_hop));
            debug_log("[DEBUG] Parsed next_hop: " + std::to_string(entry.next_hop));
            ptr += sizeof(entry.next_hop);

            memcpy(&entry.next_hop_MAC, ptr, sizeof(entry.next_hop_MAC));
            debug_log("[DEBUG] Parsed next_hop_MAC: " + std::to_string(entry.next_hop_MAC));
            ptr += sizeof(entry.next_hop_MAC);

            memcpy(&entry.distance, ptr, sizeof(entry.distance));
            debug_log("[DEBUG] Parsed distance: " + std::to_string(entry.distance));
            ptr += sizeof(entry.distance);

            memcpy(&entry.expiry, ptr, sizeof(entry.expiry));
            debug_log("[DEBUG] Parsed expiry: " + std::to_string(entry.expiry));
            ptr += sizeof(entry.expiry);


            new_entries[dest_ip] = entry;
            debug_log("[DEBUG] IN RECEIVER, new entry added for IP " + std::to_string(dest_ip)
                      + " with next hop MAC " + std::to_string(entry.next_hop_MAC)
                      + " and distance " + std::to_string(entry.distance));
        }
        update_routing_table(distance, new_entries);
    } else {
        debug_log("[DEBUG] Received a data packet for dest_ip " + std::to_string(header.dest_ip));
        if (header.dest_ip == ip) {
            std::vector<uint8_t> segment(packet.begin() + sizeof(header), packet.end());
            receive_segment(header.src_ip, segment);
            debug_log("[DEBUG] Packet received by destination IP " + std::to_string(ip));
        } else {
            send_segment(header.dest_ip, std::vector<uint8_t>(packet.begin() + sizeof(header), packet.end()));
            debug_log("[DEBUG] Packet forwarded to dest_ip " + std::to_string(header.dest_ip));
        }
    }
}

void RPNode::do_periodic() {
    debug_log("[DEBUG] Periodic function called");

    auto table_packet = prepare_table_packet();
    RPPacketHeader header(ip, 0, true);
    std::vector<uint8_t> packet(sizeof(header) + table_packet.size());
    memcpy(&packet[0], &header, sizeof(header));
    memcpy(&packet[sizeof(header)], table_packet.data(), table_packet.size());

    debug_log("[DEBUG] Validating packet before broadcasting...");
    parse_and_validate_packet(packet); // Validate the full packet

    broadcast_packet_to_all_neighbors(packet, true);
    debug_log("[DEBUG] Routing table broadcasted");
}
