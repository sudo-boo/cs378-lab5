import pyaudio
import numpy as np
import time

# Parameters
SAMPLE_RATE = 44100  # Sample rate (Hz)
DURATION = 1       # Duration for each bit (seconds)
FREQS = [5000, 5500, 6000, 6500, 7000, 7500, 8000, 8500]  # Frequencies for bits '000', '001', '010', '011', '100', '101', '110', '111'

# Initialize PyAudio
p = pyaudio.PyAudio()

def get_binary_timestamp():
    """Get the current timestamp in binary form."""
    timestamp = int(time.time())  # Current timestamp as integer
    return format(timestamp, 'b')  # Convert timestamp to binary string

def encode_message(bitstring):
    """Encode the message by appending destination."""
    destination = '10'  # Destination '2' in binary
    encoded_message = f"{bitstring}{destination}"  # Append destination
    return encoded_message

def generate_combined_tone(frequencies, duration, sample_rate):
    """
    Generate a combined tone for multiple frequencies.
    """
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    combined_tone = np.zeros_like(t)
    
    for freq in frequencies:
        tone = np.sin(2 * np.pi * freq * t)
        combined_tone += tone

    # Normalize the combined tone to prevent clipping
    combined_tone /= len(frequencies)

    return combined_tone

def transmit(bitstring):
    """
    Transmit the bitstring as audio signals using specific frequencies.
    """
    mapping = {
        '000' : [FREQS[0]],
        '001' : [FREQS[1]],
        '010' : [FREQS[2]],
        '011' : [FREQS[3]],
        '100' : [FREQS[4]],
        '101' : [FREQS[5]],
        '110' : [FREQS[6]],
        '111' : [FREQS[7]]
    }

    stream = p.open(format=pyaudio.paFloat32,
                    channels=1,
                    rate=SAMPLE_RATE,
                    output=True)

    print("Transmitting data...")
    # combined_tone = generate_combined_tone(FREQS, 1, SAMPLE_RATE)  # Duration is 2 seconds

    # Play the combined tone
    # stream.write(combined_tone.astype(np.float32).tobytes())

    # Split the bitstring into blocks of size 2
    for i in range(0, len(bitstring), 3):
        # Extract 2 bits
        block = bitstring[i:i+3]
        print(f"Transmitting block: {block}")

        # Get the corresponding frequencies for the current 2-bit block
        frequencies = mapping.get(block, [FREQS[0]])  # Default to '00' if unknown block

        # Generate the combined tone for the block's frequencies
        combined_tone = generate_combined_tone(frequencies, DURATION, SAMPLE_RATE)

        # Play the combined tone
        stream.write(combined_tone.astype(np.float32).tobytes())

    print("Transmission complete.")

    stream.stop_stream()
    stream.close()


def main():
    # Get the bitstring input from the user
    bitstring = input("Enter the bitstring message to transmit: ")

    # Encode the message with destination
    encoded_bitstring = encode_message(bitstring)

    # Length encoding (example length added here)
    preamble = "101011"
    # length = len(encoded_bitstring)
    length = format(len(encoded_bitstring), '05b')
    transmitted_bitstring = preamble + length + encoded_bitstring

    print(f"Transmitting bitstring: {transmitted_bitstring}")

    time.sleep(3)

    # Transmit the bitstring as audio
    transmit(transmitted_bitstring)

if __name__ == "__main__":
    main()

# Close PyAudio when done
p.terminate()
