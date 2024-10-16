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
    server_addr.sin_port = htons(8080);  // Matching sender port
    server_addr.sin_addr.s_addr = htonl(INADDR_ANY);

    if (bind(sock, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
        perror("Error binding socket");
        fclose(fp);
        close(sock);
        return -1;
    }

    char buffer[MAX_PACKET_SIZE];
    socklen_t addr_len = sizeof(client_addr);
    struct timeval t1;

    while (1) {
        int recv_len = recvfrom(sock, buffer, MAX_PACKET_SIZE, 0, (struct sockaddr *)&client_addr, &addr_len);
        gettimeofday(&t1, NULL);

        if (recv_len < 0) {
            perror("Error receiving packet");
            continue;
        }

        buffer[recv_len] = '\0';  // Null-terminate the received message
        int packet_num;
        sscanf(buffer, "%4d", &packet_num);
        printf("Received packet: %d\n", packet_num);

        // Log packet number and timestamp to file
        fprintf(fp, "%d %ld\n", packet_num, (t1.tv_sec % 1000) * 1000000 + t1.tv_usec);
        fflush(fp);  // Ensure the result is written to the file
    }

    fclose(fp);
    close(sock);
    return 0;
}
