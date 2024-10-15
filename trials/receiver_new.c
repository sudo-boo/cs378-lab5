#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <sys/time.h>

#define MAX_PACKET_SIZE 1024

int main(int argc, char *argv[]) {
    if (argc != 3) {
        printf("Usage: %s <packet_size> <output_file>\n", argv[0]);
        return -1;
    }

    int packet_size = atoi(argv[1]);
    char *output_file = argv[2];

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
    server_addr.sin_port = htons(8080); // Change port if necessary
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
    double time_diff;
    // int packet_counter = 0;

    while (1) {
        int recv_len = recvfrom(sock, buffer, MAX_PACKET_SIZE, 0, (struct sockaddr *)&client_addr, &addr_len);
        gettimeofday(&t1, NULL);
        if (recv_len < 0) {
            perror("Error receiving packet");
            continue;
        }
        buffer[recv_len] = '\0';
        int packet_num;
        sscanf(buffer, "%4d", &packet_num);
        printf("Received packet: %d\n", packet_num);

            // First packet of the pair
        
            // Second packet of the pair
            // gettimeofday(&t2, NULL);
            // time_diff = (t2.tv_sec - t1.tv_sec) * 1000000 + (t2.tv_usec - t1.tv_usec); // Time difference in microseconds
            // fprintf(fp, "Estimate of C: %f bps\n", (double)(packet_size * 8) / time_diff);
            // fprintf(fp,"%f\n",);
            fprintf(fp,"%d %ld\n", packet_num,(t1.tv_sec%1000) * 1000000 + t1.tv_usec);
            fflush(fp); // Ensure the result is written to the file
        

        // packet_counter++;
    }

    fclose(fp);
    close(sock);
    return 0;
}
