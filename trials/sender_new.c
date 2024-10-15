#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <time.h>

#define MAX_PACKET_SIZE 1024

int main(int argc, char *argv[]) {
    if (argc != 5) {
        printf("Usage: %s <packet_size> <IP> <spacing (ms)> <total_packet_pairs>\n", argv[0]);
        return -1;
    }

    int packet_size = atoi(argv[1]);
    char *ip_address = argv[2];
    int spacing = atoi(argv[3]);
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
    server_addr.sin_port = htons(8080); // Change port if necessary
    server_addr.sin_addr.s_addr = inet_addr(ip_address);

    char message[MAX_PACKET_SIZE];
    char temp[5];
    // for(int i=0;i<4;i++){
    //     temp[i] = '1';
    // }  
    for (int i = 0; i < total_packet_pairs; i++) {
        // First packet
        memset(message, '0', packet_size-1);
        message[packet_size-1] = '\0';
        sprintf(temp,"%04d",2*i+1);
        memcpy(message,temp,4);
        // memset(message+2, '1',1);
        // int packet_number = 2 * i + 1;
        // int num_digits = 0;
        // while (packet_number != 0) {
        //     packet_number /= 10;
        //     num_digits++;
        // }
        // memset(message + num_digits, '0', packet_size - num_digits - 1);
        // snprintf(message, sizeof(message),"%04d", 2 * i + 1);
        // snprintf(message, packet_size, "Packet %d", 2 * i + 1);
        printf("%s",message);
        int send_status = sendto(sock, message, packet_size, 0, (struct sockaddr *)&server_addr, sizeof(server_addr));
        if (send_status < 0) {
            perror("Error sending packet 1");
            return -1;
        }
        printf("Sent packet %d to %s\n", 2 * i + 1, ip_address);

        // Second packet
        // memset(message, 0, packet_size-1);
        // message[packet_size-1] = '\0';
        // snprintf(message, sizeof(message),"%04d", 2 * i + 2);
        // snprintf(message, packet_size, "Packet %d", 2 * i + 2);
        memset(message, '0', packet_size-1);
        message[packet_size-1] = '\0';
        sprintf(temp,"%04d",2*i+2);
        memcpy(message,temp,4);
        send_status = sendto(sock, message, packet_size, 0, (struct sockaddr *)&server_addr, sizeof(server_addr));
        if (send_status < 0) {
            perror("Error sending packet 2");
            return -1;
        }
        printf("Sent packet %d to %s\n", 2 * i + 2, ip_address);

        // Sleep for the specified spacing between packet pairs
        usleep(spacing * 1000); // Convert ms to us
    }

    close(sock);
    return 0;
}
