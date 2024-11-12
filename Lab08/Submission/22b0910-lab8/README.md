# CS378 : Lab 8 : Running Instructions

This script allows you to run a series of TCP throughput experiments with configurable parameters, including:

- TCP congestion control algorithm (e.g., Reno, Cubic)
- Network delay (e.g., 10ms, 50ms, 100ms)
- Packet loss rate (e.g., 0.1%, 0.5%, 1%)
- Number of test runs

The script will create a 20MB test file, configure the Linux traffic control (tc) system to simulate the desired network conditions, run iperf tests to measure throughput, and save the results in CSV files. It will also capture the network traffic using Wireshark and store the packet captures.

## Prerequisites

- Python 3.x
- iperf3 (for running the throughput tests)
- Wireshark (for capturing network traffic)
- A Linux-based operating system with `root` access (e.g., Ubuntu, Debian, CentOS)


## Submission Structure

```bash
22b0910-lab8/
│
├── report.pdf           # Contains Report
│
├── scripts/
│   ├── script.py        # main script
│   └── plot.py          # script for throughput graphs
│
└── README.md            # contains info and running instructions

```


## Usage

### Main Script 
1. Open a terminal and navigate to the directory where the script is located.
2. Run the script with `python` or `python3` (whichever is required) and with the desired parameters (with `sudo`):

<br>

> **Note:** For running this experiment, by default, you are not required to provide any options unless you need to run any specific configuration.

```bash
sudo python3 script.py [arg options (optional)]
```

### Plotting

Ensure the `experiment_results` contain all the files of all configurations. If confirmed, run:
```bash
python3 plot.py
```
This will produce all the necessary plots in `/plots/` directory.

## Options

| Option             | Type      | Description                                                                                               |
|--------------------|-----------|-----------------------------------------------------------------------------------------------------------|
| `--variant`        | `str`     | Specify TCP variant(s) to test. Options: `'default'`, or specific values (e.g., `reno`, `cubic`). |
| `--delay`          | `str`     | Network delays to simulate. Use `'default'` or specify custom values (e.g., `10ms`, `50ms`).             |
| `--loss`           | `str`     | Packet loss rates to simulate. Use `'default'` or custom values (e.g., `0.1%`, `1%`).                   |
| `--runs`           | `int`     | Number of `iperf` test runs for each configuration. Default is 20.                                       |

### Example Usage

```bash
sudo python3 script.py --variant reno cubic --delay 20ms 100ms --loss 0.5% 1% --runs 10
```

## Output

- **Throughput Results**: The throughput data (in Mbits/sec) is saved in CSV format in the `experiment_results` directory. The filename includes the TCP variant, network delay, and loss rate.
  
  Example:  
  `experiment_results/results_reno_20ms_0.5%_mbits.csv`

- **Wireshark Capture**: A `.pcap` file containing the captured network traffic will be saved in the `wireshark_captures` directory. The filename includes the TCP variant, delay, and loss rate.

  Example:  
  `wireshark_captures/capture_reno_20ms_0.5%.pcap`


> **Note** : Ensure `iperf`, `tshark`, and `wireshark` are installed in the Linux Environment you're running.