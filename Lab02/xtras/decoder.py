import pyaudio
import numpy as np

# Parameters













# decoder.py

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

def check_data(received_data, key):
    """Checks received data for errors using the CRC key."""
    remainder = mod2div(received_data, key)
    return remainder == '0' * (len(key) - 1)

def flip_bits(data, positions):
    """Flips bits at the specified positions in the data."""
    data = list(data)
    for pos in positions:
        data[pos] = '1' if data[pos] == '0' else '0'
    return ''.join(data)

def brute_force_correct(data, key):
    """Performs brute-force correction by trying all 1-bit and 2-bit flips with optimizations."""
    n = len(data)
    
    # Check all 1-bit flips
    for i in range(n):
        flipped_data = data[:i] + ('1' if data[i] == '0' else '0') + data[i+1:]
        if check_data(flipped_data, key):
            return flipped_data, [i]

    # Check all 2-bit flips
    for i in range(n):
        for j in range(i + 1, n):
            flipped_data = data[:i] + ('1' if data[i] == '0' else '0') + data[i + 1:j] + ('1' if data[j] == '0' else '0') + data[j + 1:]
            if check_data(flipped_data, key):
                return flipped_data, [i, j]

    return None, []

if __name__ == "__main__":
    import time

    # Example of erroneous encoded data
    encoded_data = '10101001100101001010100000011110'
    key = '101110101111'

    non_correct = []

    # Start the timer
    start_time = time.time()

    is_correct = check_data(encoded_data, key)

    if not is_correct:
        corrected_data, corrected_positions = brute_force_correct(encoded_data, key)
        
        if corrected_data:
            # Uncomment to print debug info
            print(f"Corrected Data: \t\t{corrected_data}")
            print(f"Corrected Bit Positions: \t{corrected_positions}")
            print(f"-----------------------------------")
        else:
            # Uncomment to print debug info
            print("Unable to correct the data using brute-force.")
            pass
    else:
        # Uncomment to print debug info
        print("Data is correct. No errors found.")
        pass

    # End the timer
    end_time = time.time()

    # Print the timing result
    elapsed_time = end_time - start_time
    # print(f"Non-corrected errors: {non_correct}")
    print(f"Elapsed Time: {elapsed_time:.4f} seconds")
