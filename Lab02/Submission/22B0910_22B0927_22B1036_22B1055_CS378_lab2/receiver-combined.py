import time
import pyaudio
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, lfilter

# Parameters for the audio signal and CRC encoding
sample_rate = 16000               # Sampling rate of the audio
chunk_size = 1024                 # Number of frames per buffer
bit_duration = 1                  # Duration of each bit in seconds
duration = 45                     # Total duration of recording in seconds
gap = 200                         # Frequency range gap for filtering
freq1 = 5000                      # Frequency of the first signal
freq2 = 7000                      # Frequency of the second signal
lowcut = freq1 - gap              # Lower bound of the frequency range for the first signal
highcut = freq1 + gap             # Upper bound of the frequency range for the first signal
lowcut2 = freq2 - gap             # Lower bound of the frequency range for the second signal
highcut2 = freq2 + gap            # Upper bound of the frequency range for the second signal
generator_poly = "1011101011101"  # Generator polynomial for CRC encoding

def CRC(dataword, generator):
    """
    Compute the CRC remainder for the given dataword and generator polynomial.
    """
    dword = int(dataword, 2)
    l_gen = len(generator)
    
    dividend = dword << (l_gen - 1)
    generator = int(generator, 2)
    
    # Perform the division using the generator polynomial
    while dividend.bit_length() >= l_gen:
        shift = dividend.bit_length() - l_gen
        dividend ^= (generator << shift) # XOR operation
    
    return dividend

def encode(dataword, generator):
    """
    Encode the dataword using the generator polynomial.
    """
    remainder = CRC(dataword, generator)         
    l_gen = len(generator) - 1
    codeword = (int(dataword, 2) << l_gen) | remainder
    return bin(codeword)[2:].zfill(len(dataword) + l_gen)

def checkError(codeword, generator):
    """
    Check if the codeword has any errors using the generator polynomial.
    """
    remainder = CRC(codeword, generator)
    return remainder == 0   # Return True if no remainder (no errors)

def flipBitsAt(codeword, error_positions):
    """
    Flip bits at specified positions to simulate errors.
    """
    if not error_positions:
        return codeword
    
    error_positions = list(set(error_positions))
    codeword = list(codeword)
    for pos in error_positions:
        if 0 <= pos < len(codeword):
            codeword[pos] = '1' if codeword[pos] == '0' else '0'
    return ''.join(codeword)

def evaluate(dataword, generator):
    """
    Evaluate the detection of errors by flipping bits and checking the codeword.
    """
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
    }

    return result

def receive_data():
    """
    Record audio, filter signals, and extract bit string from the audio data.
    """
    p = pyaudio.PyAudio()

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
        return sum(arr) / (len(arr) + 1)

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
        # Record audio data for the specified duration
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

    # Convert the list to a numpy array and normalize the data
    audio_data = np.array(audio_data)
    audio_data *= 100

    # np.savetxt('audio.txt', audio_data)

    # Apply bandpass filters to extract the desired frequency ranges
    filtered_data = bandpass_filter(audio_data, lowcut, highcut, sample_rate)
    filtered_data = np.abs(filtered_data)
    filtered_data2 = bandpass_filter(audio_data, lowcut2, highcut2, sample_rate)
    filtered_data2 = np.abs(filtered_data2)

    # Find the starting index of the transmission in each filtered signal
    starting_idx1 = 0
    starting_idx2 = 0

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

    # Determine starting index based on significant changes in the signal
    for i in range(1000, len(filtered_data) - 100):
        if abs(avg(filtered_data[i:i + 100]) - avg(filtered_data[i - 100:i])) > threshold:
            starting_idx1 = i
            break
    for i in range(1000, len(filtered_data2) - 100):
        if abs(avg(filtered_data2[i - 100:i]) - avg(filtered_data2[i:i + 100])) > threshold:
            starting_idx2 = i
            break

    # Extract the bits from the filtered data
    bitstring = ''
    starting_idx = min(starting_idx1, starting_idx2)
    for i in range(starting_idx, len(filtered_data) - sample_rate, int(sample_rate * bit_duration)):
        if avg(filtered_data[i:i + sample_rate]) > avg(filtered_data2[i:i + sample_rate]):
            bitstring += '0'
        else:
            bitstring += '1'

    return bitstring

def main():
    received_data = receive_data()
    print("Received data :\t\t\t", received_data)

    data_length = int(received_data[:6], 2)         # Extract the length of the data
    datastring = received_data[6:6 + data_length]   # Extract the actual data

    # Evaluate the data to detect and correct errors
    results = evaluate(datastring, generator_poly)
    final_corrected_data = flipBitsAt(datastring, results['detected_errors'])

    print(f"Final corrected data : \t\t" , final_corrected_data[:data_length-12])
    print(f"Detected errors at : \t\t", results['detected_errors'])
    print("------------------------------------------------------\n")

if __name__ == "__main__":
    main()
