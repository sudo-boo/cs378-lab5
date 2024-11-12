import pyaudio
import numpy as np
import time

# Parameters
SAMPLE_RATE = 44100  # Sample rate (Hz)
DURATION = 1       # Duration for each bit (seconds)
FREQ_0 = 5000        # Frequency for bit '00'
FREQ_1 = 5500        # Frequency for bit '10'
FREQ_2 = 6000        # Frequency for bit '01'
FREQ_3 = 6500        # Frequency for bit '11'

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
        '00': [FREQ_0],
        '01': [FREQ_2],
        '10': [FREQ_1],
        '11': [FREQ_3]
    }

    stream = p.open(format=pyaudio.paFloat32,
                    channels=1,
                    rate=SAMPLE_RATE,
                    output=True)

    print("Transmitting data...")

    # Split the bitstring into blocks of size 2
    for i in range(0, len(bitstring), 2):
        # Extract 2 bits
        block = bitstring[i:i+2]
        print(f"Transmitting block: {block}")

        # Get the corresponding frequencies for the current 2-bit block
        frequencies = mapping.get(block, [FREQ_0])  # Default to '00' if unknown block

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

    time.sleep(4)

    # Transmit the bitstring as audio
    transmit(transmitted_bitstring)

if __name__ == "__main__":
    main()

# Close PyAudio when done
p.terminate()
