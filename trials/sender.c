#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <sys/time.h>

#define MAX_PACKET_SIZE 1024

int main(int argc, char *argv[]) {
    if (argc != 5) {
        printf("Usage: %s <packet_size> <IP> <spacing (ms)> <total_packet_pairs>\n", argv[0]);
        return -1;
    }

    int packet_size = atoi(argv[1]);
    char *ip_address = argv[2];
    int spacing = atoi(argv[3]); // Time spacing between pairs
    int total_packet_pairs = atoi(argv[4]);

    if (packet_size > MAX_PACKET_SIZE) {
        printf("Error: Packet size exceeds maximum allowed (%d bytes)\n", MAX_PACKET_SIZE);
        return -1;
    }

    int sock = socket(AF_INET, SOCK_DGRAM, 0);
    if (sock < 0) {
        perror("Error creating socket");
        return -1;
    }

    struct sockaddr_in server_addr;
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(8080); // Listen on port 8080
    server_addr.sin_addr.s_addr = inet_addr(ip_address);

    char message[MAX_PACKET_SIZE];
    for (int i = 0; i < total_packet_pairs; i++) {
        // Send first packet of the pair
        snprintf(message, sizeof(message), "Packet %d", 2 * i + 1);
        sendto(sock, message, packet_size, 0, (struct sockaddr *)&server_addr, sizeof(server_addr));
        printf("Sent packet %d to %s\n", 2 * i + 1, ip_address);

        // Send second packet of the pair
        snprintf(message, sizeof(message), "Packet %d", 2 * i + 2);
        sendto(sock, message, packet_size, 0, (struct sockaddr *)&server_addr, sizeof(server_addr));
        printf("Sent packet %d to %s\n", 2 * i + 2, ip_address);

        // Sleep for the specified spacing between packet pairs
        usleep(spacing * 1000); // Convert ms to us
    }

    close(sock);
    return 0;
}
