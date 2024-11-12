import os
import subprocess
import argparse
import time

# Default Parameters
file_size = "20M"                                   # 20 MB file size for transfer
num_runs = 20                                       # Number of runs for each experiment
default_tcp_variants = ["reno", "cubic"]            # Default TCP congestion control algorithms to test
default_delays = ["10ms", "50ms", "100ms"]          # Default network delays to simulate
default_loss_rates = ["0.1%", "0.5%", "1%"]         # Default packet loss rates to simulate
bandwidth = "100mbit"                               # Bandwidth for the network link
mtu = 1500                                          # Maximum Transmission Unit size
burst = "32kbit"                                    # Burst size for traffic control
capture_dir = "wireshark_captures"                  # Directory for storing Wireshark capture files
result_dir = "experiment_results"                   # Directory for storing experiment results
test_file = "20MB_test_file.txt"                    # Test file to be created and transferred

# Argument parsing
parser = argparse.ArgumentParser(description="Run TCP throughput experiments with configurable parameters")
parser.add_argument("--variant", type=str, nargs='+', default="default", help="TCP variant(s) to test: 'all-available', 'default', or specific values (e.g., 'reno', 'cubic')")
parser.add_argument("--delay", type=str, nargs='+', default="default", help="Network delays to simulate: 'default' or specific values (e.g., '10ms', '50ms')")
parser.add_argument("--loss", type=str, nargs='+', default="default", help="Packet loss rates to simulate: 'default' or specific values (e.g., '0.1%', '1%')")
parser.add_argument("--runs", type=int, default=num_runs, help="Number of iperf test runs for each experiment")
args = parser.parse_args()

# Set experiment parameters based on arguments
num_runs = args.runs
tcp_variants = (
    default_tcp_variants if args.variant == "default" else
    ["reno", "cubic"] if args.variant == "all-available" else args.variant
)
delays = default_delays if args.delay == "default" else args.delay
loss_rates = default_loss_rates if args.loss == "default" else args.loss

# Commands map
commands = {
    "set_mtu": ["sudo", "ifconfig", "lo", "mtu", str(mtu)],
    "create_file": ["dd", "if=/dev/urandom", f"of={test_file}", "bs=1M", "count=20"],
    "reset_tc": ["sudo", "tc", "qdisc", "del", "dev", "lo", "root"],
    "add_root_qdisc": ["sudo", "tc", "qdisc", "add", "dev", "lo", "root", "handle", "1:", "htb", "default", "1"],
    "add_htb_class": lambda: ["sudo", "tc", "class", "add", "dev", "lo", "parent", "1:", "classid", "1:1", "htb", 
                              "rate", bandwidth, "burst", burst, "quantum", str(mtu)],
    "add_netem_qdisc": lambda delay, loss: ["sudo", "tc", "qdisc", "add", "dev", "lo", "parent", "1:1", "netem", 
                                            "delay", delay, "loss", loss],
    "start_iperf_server": ["iperf", "-s", "-D"],
    "stop_iperf_server": ["sudo", "pkill", "iperf"],
    "run_iperf_client": ["iperf", "-c", "127.0.0.1", "-F", test_file],
    "start_wireshark": lambda capture_file: ["sudo", "tshark", "-i", "lo", "-f", "tcp", "-w", capture_file],
}

# Set MTU for loopback interface
subprocess.run(commands["set_mtu"], check=True)

# Create directories for Wireshark captures and experiment results
os.makedirs(capture_dir, exist_ok=True)
os.makedirs(result_dir, exist_ok=True)

# Create a 20MB test file if it does not already exist
if not os.path.isfile(test_file):
    print("Creating a 20MB test file...")
    subprocess.run(commands["create_file"], check=True)

def configure_tc(delay, loss):
    """
    Configure traffic control (tc) to simulate network conditions with
    specified delay and packet loss on the loopback interface.
    """
    # Remove any existing tc configuration and add new configuration
    subprocess.run(commands["reset_tc"], stderr=subprocess.DEVNULL)
    subprocess.run(commands["add_root_qdisc"], check=True)
    subprocess.run(commands["add_htb_class"](), check=True)
    subprocess.run(commands["add_netem_qdisc"](delay, loss), check=True)

def set_tcp_variant(variant):
    """
    Set the TCP congestion control algorithm.
    """
    subprocess.run(["sudo", "sysctl", "-w", f"net.ipv4.tcp_congestion_control={variant}"], check=True)

def run_iperf_test(variant, delay, loss):
    """
    Run iperf test to measure throughput under specified conditions.
    Captures Wireshark data and saves throughput results in CSV.
    """
    # Start iperf server as a background process
    subprocess.Popen(commands["start_iperf_server"])

    # Start Wireshark capture on loopback interface
    capture_file = f"{capture_dir}/capture_{variant}_{delay}_{loss}.pcap"
    wireshark_proc = subprocess.Popen(commands["start_wireshark"](capture_file))

    throughput = []
    time.sleep(1)
    # Run multiple iperf client tests and record throughput
    for i in range(num_runs):
        print(f"\rRun : {i+1} / {num_runs}\r")
        result = subprocess.run(commands["run_iperf_client"], capture_output=True, text=True)
        # Extract throughput in Mbits/sec from iperf output
        throughput_value = result.stdout.split()[-2] if "Mbits/sec" in result.stdout else None
        print(throughput_value)
        if throughput_value:
            throughput.append(float(throughput_value))
        print("\r----------------------------\r")

    # Stop Wireshark capture and terminate iperf server
    wireshark_proc.terminate()
    subprocess.run(commands["stop_iperf_server"])
    time.sleep(2)

    # Save throughput values in CSV format
    csv_file = f"{result_dir}/results_{variant}_{delay}_{loss}_mbits.csv"
    with open(csv_file, "w") as f:
        f.write(",".join(map(str, throughput)) + "\n")

# Main loop to test each combination of TCP variant, delay, and loss
for variant in tcp_variants:
    set_tcp_variant(variant)
    for delay in delays:
        for loss in loss_rates:
            configure_tc(delay, loss)
            print()
            print(f"Running {variant} with delay={delay} and loss={loss}")
            run_iperf_test(variant, delay, loss)
            print("================================================================\r\n")

# Reset tc settings on loopback to clear any configurations applied
subprocess.run(commands["reset_tc"])
print("Experiment completed. Results saved in", result_dir, "and packet captures saved in", capture_dir)
