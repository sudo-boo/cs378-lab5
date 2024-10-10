#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <time.h>

int main(int argc, char *argv[]) {
    if (argc != 5) {
        printf("Usage: %s <packet size in bits> <destination IP> <spacing (ms)> <number of packet-pairs>\n", argv[0]);
        return 1;
    }

    int packet_size = atoi(argv[1]) / 8;  // Convert bits to bytes
    char *dest_ip = argv[2];
    int spacing_ms = atoi(argv[3]);
    int packet_pairs = atoi(argv[4]);

    // (a) Create Datagram Socket
    int sockfd = socket(AF_INET, SOCK_DGRAM, 0);
    if (sockfd < 0) {
        perror("Socket creation failed");
        exit(EXIT_FAILURE);
    }

    struct sockaddr_in dest_addr;
    memset(&dest_addr, 0, sizeof(dest_addr));
    dest_addr.sin_family = AF_INET;
    dest_addr.sin_port = htons(12345);  // Arbitrary port
    if (inet_pton(AF_INET, dest_ip, &dest_addr.sin_addr) <= 0) {
        perror("Invalid address/ Address not supported");
        exit(EXIT_FAILURE);
    }

    char *packet = malloc(packet_size);

    for (int i = 1; i <= packet_pairs; i++) {
        // Prepare the packet with the packet number
        memset(packet, 0, packet_size);
        snprintf(packet, packet_size, "%d", i);

        // (b) Send/write data to the socket
        if (sendto(sockfd, packet, packet_size, 0, (struct sockaddr *)&dest_addr, sizeof(dest_addr)) < 0) {
            perror("Send failed");
            break;
        }

        // Send the second packet immediately after the first
        if (sendto(sockfd, packet, packet_size, 0, (struct sockaddr *)&dest_addr, sizeof(dest_addr)) < 0) {
            perror("Send failed");
            break;
        }

        // Wait for the specified time before sending the next pair
        usleep(spacing_ms * 1000);
    }

    free(packet);
    close(sockfd);
    return 0;
}
