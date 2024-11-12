import time
import pyaudio
import math
import numpy as np

key = '1011101011101'           # CRC key for encoding data
duration = 1                    # Duration of each tone in seconds
sample_rate = 44100             # Sampling rate for audio signals
freq0 = 5000                    # Frequency representing bit 0
freq1 = 7000                    # Frequency representing bit 1


def xor(a, b):
    """Performs XOR operation between two binary strings."""
    result = []
    for i in range(1, len(b)):
        # XOR each bit of the two binary strings
        if a[i] == b[i]:
            result.append('0')
        else:
            result.append('1')
    return ''.join(result)

def mod2div(dividend, divisor):
    """Performs modulo-2 division (bitwise XOR division)."""
    pick = len(divisor)  # Length of the divisor
    tmp = dividend[0:pick]  # Initial portion of the dividend

    while pick < len(dividend):
        # Perform XOR operation based on the leading bit
        if tmp[0] == '1':
            tmp = xor(divisor, tmp) + dividend[pick]
        else:
            tmp = xor('0'*pick, tmp) + dividend[pick]
        pick += 1

    # Final XOR operation to get the remainder
    if tmp[0] == '1':
        tmp = xor(divisor, tmp)
    else:
        tmp = xor('0'*pick, tmp)
    
    return tmp

def encode_data(data, key):
    """Encodes the data using the CRC key."""
    l_key = len(key)
    appended_data = data + '0'*(l_key-1)        # Append zeroes to the data
    remainder = mod2div(appended_data, key)     # Calculate CRC remainder
    codeword = data + remainder                 # Append remainder to the data
    return codeword

def flip_bits(data, positions):
    """Flips bits at the specified positions in the data."""
    data = list(data)
    for pos in positions:
        # Flip the bit at the specified position
        data[pos] = '1' if data[pos] == '0' else '0'
    return ''.join(data)

def transmit(bitstring): 
    """
    Transmit the bitstring as audio signals using specific frequencies.
    """

    p = pyaudio.PyAudio()

    def generate_tone(frequency, duration, sample_rate):
        """
        Generate a sine wave tone for a given frequency and duration.
        """
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        tone = np.sin(2 * np.pi * frequency * t)
        return tone

    stream = p.open(format=pyaudio.paFloat32,
                    channels=1,
                    rate=sample_rate,
                    output=True)
    
    print("Transmitting data...")

    # Transmit each bit in the bitstring
    for bit in bitstring:
        if bit == '0':
            tone = generate_tone(freq0, duration, sample_rate)
        else:
            tone = generate_tone(freq1, duration, sample_rate)
        
        stream.write(tone.astype(np.float32).tobytes())
    
    print("Transmission complete.")

    stream.stop_stream()
    stream.close()

    p.terminate()

def inputData():
    """
    Take input data from the user.
    """
    dataword = input("Enter data: ")
    return dataword

if __name__ == "__main__":

    data = inputData()

    # Encode data using CRC
    encoded_data = encode_data(data, key)
    print(f"Original Data: \t\t\t\t{data}")
    print(f"Encoded Data: \t\t\t\t{encoded_data}")
    m = len(encoded_data)

    # Take up to 2 indices as input to flip
    try:
        indices = input("Enter up to 2 values (a and b): ").strip()
        if indices:
            indices = [float(i) for i in indices.split(' ')]
            if len(indices) > 2:
                raise ValueError("Only up to 2 indices are allowed.")
            
            length = len(encoded_data)
            length = bin(length)[2:].zfill(6)               # Header with length of data
            encoded_data_with_header = length + encoded_data
            print(f"Encoded Data with header: \t\t\t{encoded_data_with_header}")

            # Calculate bit positions to flip
            p = 6  # Length of header
            idx = []
            if indices[0] != 0:
                idx.append(p + math.ceil(indices[0]*m)-1)
            if indices[1] != 0:
                idx.append(p + math.ceil(indices[1]*m)-1)
            
            print(f"Flipping bits at indices: \t\t\t{idx}")
            corrupted_data = flip_bits(encoded_data_with_header, idx)

            print(f"Corrupted Data after flipping bits: \t\t{corrupted_data}")

            # Transmit the corrupted data
            transmit(corrupted_data)

            print(f"Data transmission complete.")

    except ValueError as e:
        print(f"Invalid input: {e}")
