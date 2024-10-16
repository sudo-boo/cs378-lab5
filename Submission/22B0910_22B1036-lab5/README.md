# Lab 5: Bottleneck Bandwidth Estimation Tool


## Introduction
This project contains two programs: `sender.c` and `receiver.c`. Together, they are used to estimate the bottleneck bandwidth on an end-to-end path by sending packet pairs and measuring their inter-arrival times.


## Contents
- `sender.c`: Sends packets to a specified destination at given intervals.
- `receiver.c`: Receives packets, measures the inter-arrival time, and logs the results.
- `report.pdf`: Describes the implementation and experimentation process.
- `Makefile`: Included just as an optional thing for ease.

<hr>
<br>

## Compilation Instructions

### Using `gcc`
To compile the programs:

```bash
gcc -o sender sender.c
gcc -o receiver receiver.c
```
### Using `make` (Optional)
Using `Makefile`, you can compile the programs by simply running:

```bash
make
```
This will generate two executables: `sendergit` and `receiver`.
<hr>
<br>

## Usage Instructions

> Make sure you run the receiver before running the sender.

### Running the Receiver
```bash
./receiver <output_file>
```

- `output_file`: The name of the file where the results (P/(t2-t1)) will be saved.

Example:

```bash
./receiver results.txt
```
<hr>

### Running the Sender

```bash
./sender <P> <destination_IP> <time_spacing> <num_packet_pairs>
```
- `P`: Size of each packet in bits.
- `destination_IP`: IP address of the receiving machine.
- `time_spacing`: Time interval between packet pairs in milliseconds.
- `num_packet_pairs`: Total number of packet pairs to send.

Example:
```bash
./sender 8192 192.168.1.2 1000 100
```

<hr>
<br>

## Experimentation Instructions
### Experiment 1

On the same machine, configure the loopback interface to a maximum throughput of 10 Mbps using tc:

```bash
sudo tc qdisc add dev lo root tbf rate 10mbit burst 9kb latency 50ms
```
Run both `sender` and `receiver` on the same machine.

After running the experiment, remove the traffic control rule:

```bash
sudo tc qdisc del dev lo root
sudo tc qdisc add dev lo root tbf rate <speed_limit> burst <packet_size> latency <latency_value>
sudo tc -s qdisc ls dev lo
```

<hr>

### Experiment 2
Run `sender` and `receiver` on two different machines.

Ensure before running that there are at least 4 hops between the sender and receiver using traceroute. 

```bash
traceroute <receiver_IP>
```
Run the `sender` and `receiver` with the given parameters and observe the results.

<!-- > <br> -->

> **NOTE:**
> - Make sure to adjust the `packet_size` and `time_spacing` based on your experimentation needs.
> - If any packet in a pair is dropped, that pair’s result will be ignored.
> - Ensure that the packet transmission is synchronized correctly to avoid any misalignment between consecutive packets.


<hr>