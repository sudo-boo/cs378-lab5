#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <sys/time.h>

#define MAX_PACKET_SIZE 1024

int main(int argc, char *argv[]) {
    if (argc != 2) {
        printf("Usage: %s <output_file>\n", argv[0]);
        return -1;
    }

    char *output_file = argv[1];
    FILE *fp = fopen(output_file, "w");
    if (fp == NULL) {
        perror("Error opening output file");
        return -1;
    }

    int sock = socket(AF_INET, SOCK_DGRAM, 0);
    if (sock < 0) {
        perror("Error creating socket");
        fclose(fp);
        return -1;
    }

    struct sockaddr_in server_addr, client_addr;
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(8080); // Listen on port 8080
    server_addr.sin_addr.s_addr = htonl(INADDR_ANY); // Listen on all interfaces

    if (bind(sock, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
        perror("Error binding socket");
        fclose(fp);
        close(sock);
        return -1;
    }

    printf("Receiver ready, listening on port 8080...\n");

    char buffer[MAX_PACKET_SIZE];
    socklen_t addr_len = sizeof(client_addr);
    struct timeval t1, t2;
    double time_diff;

    while (1) {
        // Receive the first packet of the pair
        int recv_len = recvfrom(sock, buffer, MAX_PACKET_SIZE, 0, (struct sockaddr *)&client_addr, &addr_len);
        if (recv_len < 0) {
            perror("Error receiving packet");
            continue;
        }
        gettimeofday(&t1, NULL);  // Capture the time for the first packet
        buffer[recv_len] = '\0';  // Null-terminate the received data
        printf("Received: %s\n", buffer);

        // Receive the second packet of the pair
        recv_len = recvfrom(sock, buffer, MAX_PACKET_SIZE, 0, (struct sockaddr *)&client_addr, &addr_len);
        if (recv_len < 0) {
            perror("Error receiving packet");
            continue;
        }
        gettimeofday(&t2, NULL);  // Capture the time for the second packet
        buffer[recv_len] = '\0';  // Null-terminate the received data
        printf("Received: %s\n", buffer);

        // Calculate the time difference in microseconds
        time_diff = (t2.tv_sec - t1.tv_sec) * 1000000 + (t2.tv_usec - t1.tv_usec);
        printf("Time difference between the pair: %.2f microseconds\n", time_diff);
        printf("Throughput: %.2f Megabites per second\n",1024/ (time_diff));

        // Write the time difference to the output file
        fprintf(fp, "%.2f \n", time_diff);
        fflush(fp); // Ensure the result is written to the file
    }

    fclose(fp);
    close(sock);
    return 0;
}
