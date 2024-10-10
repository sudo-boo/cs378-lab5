#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/time.h>
#include <arpa/inet.h>
#include <unistd.h>

double time_diff(struct timeval *start, struct timeval *end) {
    return (double)(end->tv_sec - start->tv_sec) * 1000000 + (double)(end->tv_usec - start->tv_usec);
}

int main(int argc, char *argv[]) {
    if (argc != 2) {
        printf("Usage: %s <output file>\n", argv[0]);
        return 1;
    }

    char *output_file = argv[1];

    // (a) Create Datagram Socket
    int sockfd = socket(AF_INET, SOCK_DGRAM, 0);
    if (sockfd < 0) {
        perror("Socket creation failed");
        exit(EXIT_FAILURE);
    }

    struct sockaddr_in recv_addr;
    memset(&recv_addr, 0, sizeof(recv_addr));
    recv_addr.sin_family = AF_INET;
    recv_addr.sin_port = htons(12345);  // Arbitrary port
    recv_addr.sin_addr.s_addr = INADDR_ANY;

    if (bind(sockfd, (const struct sockaddr *)&recv_addr, sizeof(recv_addr)) < 0) {
        perror("Bind failed");
        exit(EXIT_FAILURE);
    }

    char buffer[1024];
    struct timeval t1, t2;

    FILE *fp = fopen(output_file, "w");
    if (!fp) {
        perror("File opening failed");
        exit(EXIT_FAILURE);
    }

    while (1) {
        // (d) Measure the time of arrival of packets
        int len = recvfrom(sockfd, buffer, 1024, 0, NULL, NULL);
        if (len < 0) {
            perror("Receive failed");
            continue;
        }
        gettimeofday(&t1, NULL);

        len = recvfrom(sockfd, buffer, 1024, 0, NULL, NULL);
        if (len < 0) {
            perror("Receive failed");
            continue;
        }
        gettimeofday(&t2, NULL);

        // (d) Measure time difference and write result
        double delta_t = time_diff(&t1, &t2);
        fprintf(fp, "%f\n", delta_t);
    }

    fclose(fp);
    close(sockfd);
    return 0;
}
