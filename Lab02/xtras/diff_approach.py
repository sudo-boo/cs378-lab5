import random
import time

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

def evaluate(dataword, generator, error_positions):
    encoded_data = encode(dataword, generator)
    corrupted_data = flipBitsAt(encoded_data, error_positions)
    start = time.time()

    detected_error_positions = None
    # Attempt to detect the original error positions
    for i in range(len(encoded_data)):
        for j in range(i, len(encoded_data)):
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
        'encoded': encoded_data,
        'corrupted': corrupted_data,
        'detected_errors': detected_error_positions,
        'time_taken': end - start,
        'error_positions': error_positions,
        'corrected': sorted(detected_error_positions) == sorted(error_positions) if detected_error_positions else False
    }

    return result

def inputDataString():
    data = input("Enter data string: ")
    return data

def inputFlipPositions():
    positions = input("Enter up to 2 positions to flip (space separated): ")
    return [int(i) for i in positions.split()]

def main():
    generator = "1011101011101"
    # datastring = "11010111101110010010"
    datastring = inputDataString()
    error_positions = inputFlipPositions()
    results = evaluate(datastring, generator, error_positions)

    if results['corrected']:
        print(f"Data Length: \t\t{results['length']}")
        print(f"Encoded data: \t\t{results['encoded']}")
        print(f"Corrupted data: \t{results['corrupted']}")
        print(f"Detected errors: \t{results['detected_errors']}")
        print(f"Time taken: \t\t{results['time_taken']:.5f} seconds")
        print(f"Error positions: \t{results['error_positions']}")
        print(f"Corrected: \t\t{results['corrected']}")
        print("------------------------------------------------------\n")
    else:
        print("Failed to or No errors detected.")

if __name__ == "__main__":
    main()
