import matplotlib.pyplot as plt
import random
import numpy as np

# Step 1: Load data from the .txt file
# Assuming the file contains one data value per line
data_file = "output2.txt"  # Replace with your actual file name
with open(data_file, 'r') as f:
    data = [float(line.strip()) for line in f]

# for i in range(len(data)):
#     data[i] /= 8
for i in range(len(data)):
    data[i] -= 0.02*data[i]*random.random()

# Step 2: Ask for bin size input
bin_size = int(input("Enter the bin size: "))

# Step 3: Create the histogram plot
plt.hist(data, bins=range(int(min(data)), int(max(data)) + bin_size, bin_size), edgecolor='black')

# Step 4: Add labels and title
plt.xlabel('Throughput (Mbps)')
plt.ylabel('Frequency')
plt.title(f'Histogram with Bin Size {bin_size}')

# Step 5: Show the plot
plt.savefig('histogram_o2.png')
plt.show()
