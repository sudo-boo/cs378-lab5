import os
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy import stats

# Define directories
result_dir = "experiment_results"
plot_dir = "plots"
os.makedirs(plot_dir, exist_ok=True)

# Variants, delays, and losses
variants = ["reno", "cubic"]
delays = ["10ms", "50ms", "100ms"]
losses = ["0.1%", "0.5%", "1%"]

# Dictionary to store results for easy access
results = {variant: {delay: {loss: [] for loss in losses} for delay in delays} for variant in variants}

# Load data
for v in variants:
    for d in delays:
        for l in losses:
            file_name = f"results_{v}_{d}_{l}_mbits.csv"
            file_path = os.path.join(result_dir, file_name)
            if os.path.isfile(file_path):
                with open(file_path, 'r') as f:
                    vals = f.readline().strip().split(",")
                    vals = [float(i) for i in vals]
                    results[v][d][l] = vals

# Function to calculate mean and 90% confidence interval
def mean_confidence_interval(data, confidence=0.90):
    mean = np.mean(data)
    n = len(data)
    if n > 1:
        sem = stats.sem(data)
        h = sem * stats.t.ppf((1 + confidence) / 2., n - 1)
    else:
        h = 0
    return mean, h

# Plot settings
plot_configs = [
    ("Throughput vs Delay (Loss=0.1%)", "0.1%", "delay", "Throughput (Mbps)", delays),
    ("Throughput vs Delay (Loss=0.5%)", "0.5%", "delay", "Throughput (Mbps)", delays),
    ("Throughput vs Delay (Loss=1%)", "1%", "delay", "Throughput (Mbps)", delays),
    ("Throughput vs Loss (Delay=10ms)", "10ms", "loss", "Throughput (Mbps)", losses),
    ("Throughput vs Loss (Delay=50ms)", "50ms", "loss", "Throughput (Mbps)", losses),
    ("Throughput vs Loss (Delay=100ms)", "100ms", "loss", "Throughput (Mbps)", losses)
]

# Generate and save plots
for plot_title, filter_value, x_type, y_label, x_values in plot_configs:
    plt.figure()
    for v in variants:
        means = []
        conf_intervals = []
        for x in x_values:
            if x_type == "delay":
                data = results[v][x][filter_value]
            else:
                data = results[v][filter_value][x]
                
            if data:
                mean, ci = mean_confidence_interval(data)
                means.append(mean)
                conf_intervals.append(ci)
            else:
                means.append(np.nan)
                conf_intervals.append(np.nan)

        # Convert x_values to numerical for plotting if they're delays
        x_vals_numeric = [int(x[:-2]) for x in x_values] if x_type == "delay" else [float(x[:-1]) for x in x_values]
        
        # Plot with error bars
        plt.errorbar(x_vals_numeric, means, yerr=conf_intervals, label=v, capsize=5)

    plt.xlabel("Delay (ms)" if x_type == "delay" else "Loss (%)")
    plt.ylabel(y_label)
    plt.title(plot_title)
    plt.legend()
    plt.grid(True)
    
    # Save the plot
    plot_filename = f"{plot_title.replace(' ', '_').replace('(', '').replace(')', '')}.png"
    plt.savefig(os.path.join(plot_dir, plot_filename))
    plt.close()
