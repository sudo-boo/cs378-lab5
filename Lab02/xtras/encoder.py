
import pyaudio
import numpy as np

# Parameters
bitstring = "10100111"
duration = 0.5
sample_rate = 44100

freq0 = 5000 # bit 0
freq1 = 7000 # bit 1

p = pyaudio.PyAudio()

def generate_tone(frequency, duration, sample_rate):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    tone = np.sin(2 * np.pi * frequency * t)
    return tone

stream = p.open(format=pyaudio.paFloat32,
                channels=1,
                rate=sample_rate,
                output=True)

for bit in bitstring:
    if bit == '0':
        tone = generate_tone(freq0, duration, sample_rate)
    else:
        tone = generate_tone(freq1, duration, sample_rate)
    
    stream.write(tone.astype(np.float32).tobytes())

stream.stop_stream()
stream.close()

p.terminate()








def xor(a, b):
    """Performs XOR operation between two binary strings."""
    result = []
    for i in range(1, len(b)):
        if a[i] == b[i]:
            result.append('0')
        else:
            result.append('1')
    return ''.join(result)

def mod2div(dividend, divisor):
    """Performs modulo-2 division (bitwise XOR division)."""
    pick = len(divisor)
    tmp = dividend[0:pick]

    while pick < len(dividend):
        if tmp[0] == '1':
            tmp = xor(divisor, tmp) + dividend[pick]
        else:
            tmp = xor('0'*pick, tmp) + dividend[pick]
        pick += 1

    if tmp[0] == '1':
        tmp = xor(divisor, tmp)
    else:
        tmp = xor('0'*pick, tmp)
    
    return tmp

def encode_data(data, key):
    """Encodes the data using the CRC key."""
    l_key = len(key)
    appended_data = data + '0'*(l_key-1)
    remainder = mod2div(appended_data, key)
    codeword = data + remainder
    return codeword

def flip_bits(data, positions):
    """Flips bits at the specified positions in the data."""
    data = list(data)
    for pos in positions:
        data[pos] = '1' if data[pos] == '0' else '0'
    return ''.join(data)

if __name__ == "__main__":
    import time

    data = '101010011001010010101'
    key = '101110101111'

    # Start the timer
    start_time = time.time()

    # Encode data
    encoded_data = encode_data(data, key)
    print(f"Original Data: \t\t\t{data}")
    print(f"Encoded Data: \t\t\t{encoded_data}")

    # Take up to 2 indices as input to flip
    try:
        indices = input("Enter up to 2 indices to flip (comma-separated): ").strip()
        if indices:
            indices = [int(i) for i in indices.split(',')]
            if len(indices) > 2:
                raise ValueError("Only up to 2 indices are allowed.")
            # Flip bits at specified indices
            corrupted_data = flip_bits(encoded_data, indices)
            print(f"Corrupted Data: \t\t{corrupted_data}")
    except ValueError as e:
        print(f"Invalid input: {e}")

    # End the timer
    end_time = time.time()

    # Print the timing result
    elapsed_time = end_time - start_time
    print(f"Elapsed Time: {elapsed_time:.2f} seconds")
