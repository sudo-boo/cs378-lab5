import random
import time
import pyaudio
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, lfilter

# Parameters
sample_rate = 16000
chunk_size = 1024
bit_duration = 1
duration = 40
gap = 500
freq1 = 5000
freq2 = 7000
lowcut = freq1 - gap  # Lower bound of the frequency range
highcut = freq1 + gap  # Upper bound of the frequency range
lowcut2 = freq2 - gap  # Lower bound of the frequency range
highcut2 = freq2 + gap # Upper bound of the frequency range
lowcut3 = 4000 - gap # Upper bound of the frequency range
highcut3 = 4000 + gap # Upper bound of the frequency range


def CRC(dataword, generator):
    dword = int(dataword, 2)
    l_gen = len(generator)
    
    dividend = dword << (l_gen - 1)
    generator = int(generator, 2)
    
    while dividend.bit_length() >= l_gen:
        shift = dividend.bit_length() - l_gen
        dividend ^= (generator << shift)

    return dividend

def encode(dataword, generator):
    remainder = CRC(dataword, generator)
    l_gen = len(generator) - 1
    codeword = (int(dataword, 2) << l_gen) | remainder
    return bin(codeword)[2:].zfill(len(dataword) + l_gen)

def checkError(codeword, generator):
    remainder = CRC(codeword, generator)
    return remainder == 0

def flipBitsAt(codeword, error_positions):
    error_positions = list(set(error_positions))
    codeword = list(codeword)
    for pos in error_positions:
        if 0 <= pos < len(codeword):
            codeword[pos] = '1' if codeword[pos] == '0' else '0'
    return ''.join(codeword)

def evaluate(dataword, generator):
    corrupted_data = dataword
    start = time.time()

    detected_error_positions = None
    # Attempt to detect the original error positions
    for i in range(len(corrupted_data)):
        for j in range(i, len(corrupted_data)):
            temp_error_pos = [i, j]
            flipped_codeword = flipBitsAt(corrupted_data, temp_error_pos)
            
            if checkError(flipped_codeword, generator):
                detected_error_positions = list(set(temp_error_pos))
                break

        if detected_error_positions:
            break

    end = time.time()

    result = {
        'length': len(dataword),
        'corrupted': corrupted_data,
        'detected_errors': detected_error_positions,
        'time_taken': end - start,
        # 'corrected': sorted(detected_error_positions) == sorted(de) if detected_error_positions else False
    }

    return result


def decode(datastring):
    generator = "1011101011101"
    results = evaluate(datastring, generator)

    # if results['corrected']:
    print(f"Data Length: \t\t{results['length']}")
    print(f"Corrupted data: \t{results['corrupted']}")
    print(f"Detected errors: \t{results['detected_errors']}")
    print(f"Time taken: \t\t{results['time_taken']:.5f} seconds")
    # print(f"Error positions: \t{results['error_positions']}")
    # print(f"Corrected: \t\t{results['corrected']}")
    print("------------------------------------------------------\n")
    # else:
    #     print("Failed to or No errors detected.")

    return results


def receive_data():

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
            chunk = np.frombuffer(data, dtype=np.float32)
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

    np.savetxt('audio.txt', audio_data)

    # Apply bandpass filters to extract the desired frequency ranges
    filtered_data = bandpass_filter(audio_data, lowcut, highcut, sample_rate)
    filtered_data = np.abs(filtered_data)
    # filtered_data = np.convolve(filtered_data, np.ones((10,)), mode='valid')
    filtered_data2 = bandpass_filter(audio_data, lowcut2, highcut2, sample_rate)
    filtered_data2 = np.abs(filtered_data2)

    # Find the starting index of the transmission
    starting_idx1 = 0
    starting_idx2 = 0


    def compute_threshold(signal, factor=1.0):
        mean = np.mean(signal)
        std_dev = np.std(signal)
        threshold = mean + factor * std_dev
        return threshold

    # Compute the threshold using mean and standard deviation
    threshold = compute_threshold(filtered_data, factor=1.0)

    for i in range(1000, len(filtered_data)-100):
        if abs(avg(filtered_data[i:i+100]) - avg(filtered_data[i-100:i])) > threshold:
            starting_idx1 = i
            break
    for i in range(1000, len(filtered_data2)-100):
        if abs(avg(filtered_data2[i-100:i]) - avg(filtered_data2[i:i+100]))  > threshold:
            starting_idx2 = i
            break

    print("Starting index of low freq range: ", starting_idx1)
    print("Starting index of high freq range: ", starting_idx2)
        
    bitstring = ''

    starting_idx = min(starting_idx1, starting_idx2)
    # Extract the bits from the filtered data
    for i in range(starting_idx, len(filtered_data)-sample_rate, int(sample_rate*bit_duration)):
        if avg(filtered_data[i:i+sample_rate]) > avg(filtered_data2[i:i+sample_rate]):
            bitstring += '0'
        else:
            bitstring += '1'

    print("Received bitstring:", bitstring)

    # # Plotting
    # plt.figure(figsize=(10, 4))

    # # Plot the first filtered data with a solid line and transparency
    # # print(len(filtered_data))
    # sample_index = np.arange(0,len(filtered_data), dtype=float)
    # # sample_index /= sample_rate
    # plt.plot(sample_index,filtered_data, label=f'Frequency Range: {lowcut}-{highcut} Hz', color='blue', alpha=0.6)

    # # Plot the second filtered data with a dashed line, different color, and transparency
    # plt.plot(sample_index, filtered_data2, label=f'Frequency Range: {lowcut2}-{highcut2} Hz', color='red', linestyle='--', alpha=0.6)
    # # plt.plot(sample_index, abs(filtered_data3), label=f'Frequency Range: {lowcut3}-{highcut3} Hz', color='black', linestyle='--', alpha=0.6)

    # # Add titles, labels, and legend
    # plt.title('Overlapped Filtered Audio Waveforms')
    # plt.xlabel('Sample Index')
    # plt.ylabel('Amplitude')

    # # Customize the grid
    # plt.grid(True, which='both', linestyle='--', linewidth=0.5)

    # # Set major and minor ticks on the x-axis
    # plt.gca().xaxis.set_major_locator(plt.MultipleLocator(sample_rate))  # Major ticks every sample_rate units
    # # plt.gca().xaxis.set_minor_locator(plt.MultipleLocator(sample_rate // 10))  # Minor ticks for more granularity

    # # Add legend
    # plt.legend()

    # # Adjust the layout to make better use of space
    # plt.tight_layout()

    # # Save the plot to a file
    # plt.savefig('waveform.png')
    # plt.show()

    return bitstring

if __name__ == "__main__":
    received_data = receive_data()
    # first 5 bits represent the size of the dataword
    # received_data = "10000010101010100000101111101011010010"
    data_length = int(received_data[:6], 2)
    print(f"Received Length: {len(received_data)}")
    print(f"Data Length: {data_length}")
    print(f"Data passed to decode: {received_data[6:6+data_length]}")
    datastring = received_data[6:6+data_length]
    decode(datastring)