import pyaudio
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, lfilter

# Parameters
sample_rate = 16000
chunk_size = 1024
duration = 11
gap = 500
freq1 = 5000
freq2 = 7000
lowcut = freq1 - gap  # Lower bound of the frequency range
highcut = freq1 + gap  # Upper bound of the frequency range
lowcut2 = freq2 - gap  # Lower bound of the frequency range
highcut2 = freq2 + gap # Upper bound of the frequency range
lowcut3 = 4000 - gap # Upper bound of the frequency range
highcut3 = 4000 + gap # Upper bound of the frequency range


p = pyaudio.PyAudio()

def butter_bandpass(lowcut, highcut, sample_rate, order=5):
    nyquist = 0.5 * sample_rate  # Nyquist frequency is half the sampling rate
    low = lowcut / nyquist
    high = highcut / nyquist
    b, a = butter(order, [low, high], btype='band')
    return b, a

def bandpass_filter(data, lowcut, highcut, sample_rate, order=5):
    b, a = butter_bandpass(lowcut, highcut, sample_rate, order=order)
    y = lfilter(b, a, data)
    return y

def avg(arr):
    return sum(arr)/(len(arr)+1)

# Open a stream to record audio
stream = p.open(format=pyaudio.paFloat32,
                channels=1,
                rate=sample_rate,
                input=True,
                frames_per_buffer=chunk_size)

print("Recording audio signal...")

# List to hold the audio data
audio_data = []

try:
    for _ in range(int(sample_rate * duration / chunk_size)):
        data = stream.read(chunk_size, exception_on_overflow=False)
        
        # Convert the binary data to a numpy array of floats
        chunk = np.frombuffer(data, dtype=np.float32)
        
        # Append the chunk to the audio_data list
        audio_data.extend(chunk)

except KeyboardInterrupt:
    print("Stopped recording.")

finally:
    stream.stop_stream()
    stream.close()
    p.terminate()

# Convert the list to a numpy array
audio_data = np.array(audio_data)
audio_data *= 100

# Save the raw audio data to a text file

np.savetxt('audio.txt', audio_data)
# take the running average of audio data to remove noise from the audio data
# audio_data = np.convolve(audio_data, np.ones((10,)), mode='valid')

# Apply bandpass filters to extract the desired frequency ranges
filtered_data = bandpass_filter(audio_data, lowcut, highcut, sample_rate)
filtered_data = np.abs(filtered_data)
# filtered_data = np.convolve(filtered_data, np.ones((10,)), mode='valid')
filtered_data2 = bandpass_filter(audio_data, lowcut2, highcut2, sample_rate)
filtered_data2 = np.abs(filtered_data2)
# filtered_data2 = np.convolve(filtered_data2, np.ones((10,)), mode='valid')
filtered_data3 = bandpass_filter(audio_data, lowcut3 ,highcut3, sample_rate)
iltered_data3 = np.abs(filtered_data3)
# filtered_data3 = np.convolve(filtered_data3, np.ones((10,)), mode='valid')

# Find the starting index of the transmission
starting_idx1 = 0
starting_idx2 = 0


def compute_threshold(signal, factor=5.0):
    mean = np.mean(signal)
    std_dev = np.std(signal)
    threshold = mean + factor * std_dev
    return threshold

# Compute the threshold using mean and standard deviation
threshold = compute_threshold(filtered_data, factor=5.0)

# starting from index= 1000, calculate the average of 500 samples and compare it with the previous 500 samples
# if the difference is greater than 1.0, then we have found the starting index

# starting_idx = []  
# ending_idx = [] 
for i in range(1000, len(filtered_data)-1000):
    if abs(avg(filtered_data[i:i+1000]) - avg(filtered_data[i-1000:i])) > threshold*3:
        starting_idx1 = i
        break
for i in range(1000, len(filtered_data2)-100):
    if abs(avg(filtered_data2[i-1000:i]) - avg(filtered_data2[i:i+1000]))  > threshold*3:
        starting_idx2 = i
        break

print("Starting index of low freq range: ", starting_idx1)
print("Starting index of high freq range: ", starting_idx2)
      
bitstring = ''

starting_idx = min(starting_idx1, starting_idx2)
# Extract the bits from the filtered data
for i in range(starting_idx, len(filtered_data)-sample_rate, sample_rate):
    if avg(filtered_data[i:i+sample_rate]) > avg(filtered_data2[i:i+sample_rate]):
        bitstring += '0'
    else:
        bitstring += '1'

print("Received bitstring:", bitstring)


filtered_data4 = np.array([])
for i in range(0, len(filtered_data3)-1000):
    filtered_data4 = np.append(filtered_data4, avg(filtered_data3[i:i+1000]))



# Plotting
sample_index = np.arange(0, len(filtered_data3), 1)
sample_index = sample_index[:len(filtered_data4)]

# Plotting
plt.figure(figsize=(10, 4))

plt.plot(sample_index, abs(filtered_data3[:len(filtered_data4)]), label=f'Frequency Range: {lowcut3}-{highcut3} Hz', color='black', linestyle='--', alpha=0.6)
plt.plot(sample_index, abs(filtered_data4), label=f'Frequency Range: {lowcut3}-{highcut3} Hz', color='green', linestyle='--', alpha=0.6)

# Add titles, labels, and legend
plt.title('Overlapped Filtered Audio Waveforms')
plt.xlabel('Sample Index')
plt.ylabel('Amplitude')

# Customize the grid
plt.grid(True, which='both', linestyle='--', linewidth=0.5)

# Set major and minor ticks on the x-axis
plt.gca().xaxis.set_major_locator(plt.MultipleLocator(sample_rate))  # Major ticks every sample_rate units

# Add legend
plt.legend()

# Adjust the layout to make better use of space
plt.tight_layout()

# Save the plot to a file
plt.savefig('waveform.png')
plt.show()