import pyaudio
import numpy as np
import time
import matplotlib.pyplot as plt
from scipy.signal import butter, lfilter

# Parameters
SAMPLE_RATE = 20000  # Sample rate (Hz)
CHUNK = 1024         # Buffer size for recording
BIT_DURATION = 1       # Duration for each bit (seconds)
DURATION = 17
FREQ_0 = 5000        # Frequency for bit 0
FREQ_1 = 5500        # Frequency for bit 1
FREQ_2 = 6000        # Frequency for bit 2
FREQ_3 = 6500
TOLERANCE = 100      # Frequency detection tolerance
# lowcut = FREQ_0 - TOLERANCE  # Lower bound of the frequency range for bit 0
# highcut = FREQ_0 + TOLERANCE  # Upper bound of the frequency range for bit 0
# lowcut2 = FREQ_1 - TOLERANCE  # Lower bound of the frequency range for bit 1
# highcut2 = FREQ_1 + TOLERANCE  # Upper bound of the frequency range for bit 1
# lowcut3 = FREQ_2 - TOLERANCE  # Lower bound of the frequency range for bit 2
# highcut3 = FREQ_2 + TOLERANCE  # Upper bound of the frequency range for bit 2

lowcuts = []
highcuts = []
freqs = [FREQ_0, FREQ_1, FREQ_2,FREQ_3]

for freq in freqs:
    lowcuts.append(freq - TOLERANCE)
    highcuts.append(freq + TOLERANCE)

# Initialize PyAudio
p = pyaudio.PyAudio()

def detect_frequency(data, sample_rate):
    """Detect the frequency of the given audio chunk."""
    fft_data = np.fft.fft(np.frombuffer(data, dtype=np.float32))
    frequencies = np.fft.fftfreq(len(fft_data), 1 / sample_rate)
    
    # Get the positive half of the frequencies
    frequencies = frequencies[:len(frequencies)//2]
    fft_data = np.abs(fft_data[:len(fft_data)//2])
    
    # Find the peak frequency
    peak_index = np.argmax(fft_data)
    peak_freq = frequencies[peak_index]
    
    return peak_freq

def record_bitstream(duration):
    """
    Record audio, filter signals, and extract bit string from the audio data.
    """
    p = pyaudio.PyAudio()

    def check_bs(avg,mini,maxi):
        return ((avg-mini)/(maxi-mini))**4

    def butter_bandpass(lowcut, highcut, sample_rate, order=5):
        """
        Design a bandpass Butterworth filter.
        """
        nyquist = 0.5 * sample_rate
        low = lowcut / nyquist
        high = highcut / nyquist
        b, a = butter(order, [low, high], btype='band')
        return b, a

    def bandpass_filter(data, lowcut, highcut, sample_rate, order=5):
        """
        Apply a bandpass filter to the data.
        """
        b, a = butter_bandpass(lowcut, highcut, sample_rate, order=order)
        y = lfilter(b, a, data)
        return y

    def avg(arr):
        """
        Calculate the average of an array.
        """
        return sum(arr) / len(arr) 

    # Open a stream to record audio
    stream = p.open(format=pyaudio.paFloat32,
                    channels=1,
                    rate=SAMPLE_RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print("Recording audio signal...")
    
    # List to hold the audio data
    audio_data = []

    try:
        # Record audio data for the specified duration
        for _ in range(int(SAMPLE_RATE * duration / CHUNK)):
            data = stream.read(CHUNK, exception_on_overflow=False)
            chunk = np.frombuffer(data, dtype=np.float32)
            audio_data.extend(chunk)

    except KeyboardInterrupt:
        print("Stopped recording.")

    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()

    # Convert the list to a numpy array and normalize the data
    audio_data = np.array(audio_data)
    audio_data *= 100
    audio_data = audio_data[10000:]

    # np.savetxt('audio.txt', audio_data)

    noise = 0.05
    # Apply bandpass filters to extract the desired frequency ranges
    filtered_data = bandpass_filter(audio_data, lowcuts[0], highcuts[0], SAMPLE_RATE)
    filtered_data = np.abs(filtered_data)
    for i in range(len(filtered_data)):
        if filtered_data[i]>0.5:
            filtered_data[i] = 0.5
        if filtered_data[i] >noise:
            filtered_data[i] -= noise
        
    # filtered_data -=
    filtered_data1 = bandpass_filter(audio_data, lowcuts[1], highcuts[1], SAMPLE_RATE)
    filtered_data1 = np.abs(filtered_data1)
    for i in range(len(filtered_data1)):
        # filtered_data1[i] -= noise
        if filtered_data1[i]>0.5:
            filtered_data1[i] = 0.5
        if filtered_data1[i] > noise:
            filtered_data1[i] -= noise

    filtered_data2 = bandpass_filter(audio_data, lowcuts[2], highcuts[2], SAMPLE_RATE)
    filtered_data2 = np.abs(filtered_data2)
    for j in range(len(filtered_data2)):
        # filtered_data2[i] -= noise
        if filtered_data2[j]>0.5:
            filtered_data2[j] = 0.5
        if filtered_data2[j] > noise:
            filtered_data2[j] -= noise

    filtered_data3 = bandpass_filter(audio_data, lowcuts[3], highcuts[3], SAMPLE_RATE)
    filtered_data3 = np.abs(filtered_data3)
    for j in range(len(filtered_data3)):
        # filtered_data2[i] -= noise
        if filtered_data3[j]>0.5:
            filtered_data3[j] = 0.5
        if filtered_data3[j] > noise:
            filtered_data3[j] -= noise
        

     

    # Find the starting index of the transmission in each filtered signal
    starting_idx = 0
    starting_idx1 = 0
    starting_idx2 = 0
    starting_idx3 = 0

    def compute_threshold(signal, factor=1.0):
        """
        Compute a threshold for detecting signal changes.
        """
        mean = np.mean(signal)
        std_dev = np.std(signal)
        threshold = mean + factor * std_dev
        return threshold

    # Compute the threshold using mean and standard deviation
    threshold = compute_threshold(filtered_data, factor=1.0)
    # threshold1 = compute_threshold(filtered_data1, factor=1.0)
    # threshold2 = compute_threshold(filtered_data2, factor=1.0)
    # threshold2 = compute_threshold(filtered_data, factor=1.0)

    # Determine starting index based on significant changes in the signal
    for i in range(1000, len(filtered_data) - 100):
        if abs(avg(filtered_data[i:i + 100]) - avg(filtered_data[i - 100:i])) > threshold:
            starting_idx = i
            break


    for i in range(1000, len(filtered_data1)-100):
        if abs(avg(filtered_data1[i:i + 100]) - avg(filtered_data1[i - 100:i])) > threshold:
            starting_idx1 = i
            break

    for i in range(1000, len(filtered_data2) - 100):
        if abs(avg(filtered_data2[i - 100:i]) - avg(filtered_data2[i:i + 100])) > threshold:
            starting_idx2 = i
            break

    for i in range(1000, len(filtered_data3) - 100):
        if abs(avg(filtered_data3[i - 100:i]) - avg(filtered_data3[i:i + 100])) > threshold:
            starting_idx3 = i
            break

    filtered_data = np.abs(filtered_data)
    filtered_data1 = np.abs(filtered_data1)
    filtered_data2 = np.abs(filtered_data2)
    filtered_data3 = np.abs(filtered_data3)


    

    # Extract 2-bit blocks from the filtered data
    bitstring = ''
    print(f"Starting indices: {starting_idx}, {starting_idx1}, {starting_idx2}, {starting_idx3}")
    s_idx = min(starting_idx,starting_idx1,starting_idx2,starting_idx3)
    print(s_idx)
    # print(threshold,threshold1, threshold2)
    # threshold = 0.02  # You can tweak this threshold for better performance
    # for i in range(s_idx, len(filtered_data) - SAMPLE_RATE, int(SAMPLE_RATE * BIT_DURATION)):
        # avg_0 = avg(filtered_data[i:i + SAMPLE_RATE])
        # avg_1 = avg(filtered_data1[i:i + SAMPLE_RATE])
        # avg_2 = avg(filtered_data2[i:i + SAMPLE_RATE])
        # print(f"avg_0: {avg_0}, avg_1: {avg_1}, avg_2: {avg_2}")
        # added_bs = ""
        # # Determine the 2-bit block based on amplitude comparison
        # if avg_0 > threshold and avg_1 < threshold and avg_2 < threshold:
        #     bitstring += '00'  # Frequency 5000 Hz (bit '00')
        #     added_bs = '00'
        # elif avg_1 > threshold and avg_0 < threshold and avg_2 < threshold:
        #     bitstring += '10'  # Frequency 6000 Hz (bit '10')
        #     added_bs = '10'
        # elif avg_2 > threshold and avg_0 < threshold and avg_1 < threshold:
        #     bitstring += '01'  # Frequency 7000 Hz (bit '01')
        #     added_bs = '01'
        # elif avg_1 > threshold and avg_2 > threshold and avg_0 < threshold:
        #     bitstring += '11'  # Combined frequencies (bit '11')
        #     added_bs = '11'
        # print(f"Block: {added_bs}")
    for i in range(s_idx, len(filtered_data), int(SAMPLE_RATE * BIT_DURATION)):
        avg_0 = avg(filtered_data[i:i + SAMPLE_RATE])
        
        avg_1 = avg(filtered_data1[i:i + SAMPLE_RATE])
        
        avg_2 = avg(filtered_data2[i:i + SAMPLE_RATE])

        avg_3 = avg(filtered_data3[i:i + SAMPLE_RATE])
        

        max_avg = max(avg_0, avg_1, avg_2,avg_3)
        # min_avg = min(avg_0, avg_1, avg_2,avg_3)

        # new_avg_0 = check_bs(avg_0,min_avg,max_avg)
        # new_avg_1 = check_bs(avg_1,min_avg,max_avg)
        # new_avg_2 = check_bs(avg_2,min_avg,max_avg)
        # new_avg_3 = check_bs(avg_3,min_avg,max_avg)

        # thresh = 0.1
        # if new_avg_0>0.1:
        #     new_avg_0 = 1
        # elif new_avg_0 <= 0.1:
        #     new_avg_0 = 0

        # if new_avg_1>0.1:
        #     new_avg_1 = 1
        # elif new_avg_1 <= 0.1:
        #     new_avg_1 = 0
        
        # if new_avg_2>0.1:
        #     new_avg_2 = 1
        # elif new_avg_2 <= 0.1:
        #     new_avg_2 = 0

        # if new_avg_3 > 0.1:
        #     new_avg_3 = 1
        # elif new_avg_3 <= 0.1:
        #     new_avg_3 = 0

        # filtered_data[i:i+SAMPLE_RATE] = new_avg_0
        # filtered_data1[i:i+SAMPLE_RATE] = new_avg_1
        # filtered_data2[i:i+SAMPLE_RATE] = new_avg_2
        # filtered_data3[i:i+SAMPLE_RATE] = new_avg_3


      

        # if avg_0 > avg_2:
        #     filtered_data[i:i+SAMPLE_RATE] = 1
        #     filtered_data2[i:i+SAMPLE_RATE] = 0
        #     filtered_data1[i:i+SAMPLE_RATE] = (avg_1 - avg_2)/(avg_0 - avg_2)
        # elif avg_2 > avg_0:
        #     filtered_data2[i:i+SAMPLE_RATE] = 1
        #     filtered_data[i:i+SAMPLE_RATE] = 0
        #     filtered_data1[i:i+SAMPLE_RATE] = (avg_1 - avg_0)/(avg_2 - avg_0)
        
        

        # threshold = np.mean(filtered_data[i:i + SAMPLE_RATE]) + 0.2*np.std(filtered_data[i:i + SAMPLE_RATE])
        # threshold1 = np.mean(filtered_data1[i:i + SAMPLE_RATE]) + 0.2*np.std(filtered_data1[i:i + SAMPLE_RATE])
        # threshold2 = np.mean(filtered_data2[i:i + SAMPLE_RATE]) + 0.2*np.std(filtered_data2[i:i + SAMPLE_RATE])
        print(f"avg_0: {avg_0}, avg_1: {avg_1}, avg_2: {avg_2}, avg_3: {avg_3}")
        # print(f"new_avg_0: {new_avg_0}, new_avg_1: {new_avg_1}, new_avg_2: {new_avg_2}, new_avg_3: {new_avg_3}")
        # thresh = 0.6
        # print(f"median_0: {np.median(filtered_data[i:i+SAMPLE_RATE])}, median_1: {np.median(filtered_data1[i:i+SAMPLE_RATE])}, median_2: {np.median(filtered_data2[i:i+SAMPLE_RATE])}")
        # print(f"threshold: {threshold}, threshold1: {threshold1}, threshold2: {threshold2}")
        added_bs = ""
        # Determine the 2-bit block based on amplitude comparison
        if max_avg == avg_0:
            added_bs = '00'
        elif max_avg == avg_1:
            added_bs = '10'
        elif max_avg == avg_2:
            added_bs = '01'
        elif max_avg == avg_3:
            added_bs = '11'


        bitstring += added_bs

        print(f"Block: {added_bs}")
        print('---------------------------------')


    
    # Plot the filtered data1 and filtered data2
    plt.figure(figsize=(10, 6))
    time_axis = np.linspace(0, len(filtered_data) / SAMPLE_RATE, num=len(filtered_data))

    plt.plot(time_axis, filtered_data, color='blue', label="Filtered Data  (5000Hz)", alpha=0.5)
    plt.plot(time_axis, filtered_data1, color='green', label="Filtered Data 1 (6000Hz)",alpha=0.5)
    plt.plot(time_axis, filtered_data2, color='red', label="Filtered Data 2 (7000Hz)",alpha=0.5)
    plt.plot(time_axis, filtered_data3, color='grey', label="Filtered Data 3 (8000Hz)",alpha=0.5)

    plt.title("Filtered Data vs Time")
    plt.xlabel("Time (seconds)")
    plt.ylabel("Amplitude")
    plt.legend(loc="upper right")
    plt.grid(True)
    plt.savefig('figure.png')
    plt.show()


    return bitstring

        
    
    

    # return bitstring

# def decode_bitstream(bitstream):
#     """Decode the bitstream into message, destination, and timestamp."""
#     # Split the bitstream into parts
#     message = bitstream[:-2]  # Extract message bits (all except last 34 bits)
#     destination = bitstream[-2:]  # Extract the 2-bit destination
#     # timestamp = bitstream[-32:]  # Extract the last 32 bits as the timestamp
    
#     # Convert timestamp back to decimal
#     # timestamp_value = int(timestamp, 2)
#     # human_readable_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp_value))
    
#     return message, destination

# def check_destination(destination):
#     """Check if the destination bits correspond to decimal 2."""
#     return destination == '10'  # '10' in binary is 2 in decimal

def main():
    # Record audio and convert it into bitstream
    bitstream = record_bitstream(DURATION)
    print(f"Received bitstream: {bitstream}")
    
    # Decode the bitstream
    # message, destination = decode_bitstream(bitstream)
    # timestamp = int(time.time())
    # # Check if the destination matches 2
    # if check_destination(destination):
    #     print(f"Message: {message}")
    #     print(f"Timestamp: {timestamp}")
    #     print(f"Destination: {destination} (This message is meant for this receiver)")
    # else:
    #     print(f"Destination: {destination} (This message is NOT meant for this receiver)")

if __name__ == "__main__":
    main()

# Close PyAudio when done
p.terminate()