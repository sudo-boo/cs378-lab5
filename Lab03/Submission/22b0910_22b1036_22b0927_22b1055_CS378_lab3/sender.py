import pyaudio
import numpy as np
import time
from datetime import datetime

# Parameters
SAMPLE_RATE = 44100         # Audio sample rate in Hz (samples per second)
DURATION = 1                # Duration (seconds) for transmitting each bit pair
GAP_DURATION = 20           # Gap duration (seconds) between transmissions of different devices
FILE_NAME = "input.txt"     # Input file containing messages
TOTAL_DEVICES = 3           # Total number of devices in the network (Default = 3)
DEVICE_ID = 1               # Device ID of the current device (Default = 1)

# Frequencies mapped to each 2-bit pair
FREQS = [5000, 5500, 6000, 6500]  # Frequencies for '00', '01', '10', '11'

# Bit pair to frequency mapping
mapping = {
    '00': [FREQS[0]],
    '01': [FREQS[1]],
    '10': [FREQS[2]],
    '11': [FREQS[3]]
}

# Initialize PyAudio for audio transmission
p = pyaudio.PyAudio()

def get_timestamp():
    """Get the current timestamp in the format 'HH:MM:SS.ms'."""
    curr_time = datetime.now()
    return curr_time.strftime("%H:%M:%S.%f")[:-3]  # Timestamp up to milliseconds

def encode_message(bitstring, dest):
    """
    Encodes the message by appending the length, destination, and source device IDs to the bitstring.
    
    Parameters:
    bitstring (str): Original bitstring message.
    dest (int): Destination device ID.

    Returns:
    str: Encoded message with the frame header and bitstring.
    """
    global DEVICE_ID
    new_bitstring = bitstring
    
    # Ensure the bitstring length is even for 2-bit transmission
    if len(bitstring) % 2 == 0:
        new_bitstring += '0'
    
    # Add frame header with destination and source device ID
    return "1011" + format(len(bitstring) + 4, '05b') + format(dest, '02b') + format(DEVICE_ID, '02b') + new_bitstring

def generate_combined_tone(frequencies, duration, sample_rate):
    """
    Generates an audio signal by combining sine waves of multiple frequencies.

    Parameters:
    frequencies (list): List of frequencies to be combined.
    duration (float): Duration of the tone in seconds.
    sample_rate (int): Number of audio samples per second.

    Returns:
    numpy.ndarray: The combined tone generated.
    """
    # Time array for the given duration
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    combined_tone = np.zeros_like(t)
    
    # Sum sine waves of each frequency
    for freq in frequencies:
        tone = np.sin(2 * np.pi * freq * t)
        combined_tone += tone

    # Normalize the tone to prevent clipping
    combined_tone /= len(frequencies)

    return combined_tone

def transmit(bitstring):
    """
    Transmits the bitstring as audio signals using the pre-defined frequencies.
    
    Parameters:
    bitstring (str): The encoded bitstring to transmit.
    """
    print(f"{get_timestamp()} :: Started transmission.")
    
    # Delay for 2 seconds before actual transmission (simulation purpose)
    time.sleep(2)
    
    # Open PyAudio stream for audio output
    stream = p.open(format=pyaudio.paFloat32,
                    channels=1,
                    rate=SAMPLE_RATE,
                    output=True)

    print("Transmitting data...")

    # Loop through the bitstring, process 2 bits at a time
    for i in range(0, len(bitstring), 2):
        block = bitstring[i:i+2]
        frequencies = mapping.get(block, [FREQS[0]])
        combined_tone = generate_combined_tone(frequencies, DURATION, SAMPLE_RATE)

        # Play the tone
        stream.write(combined_tone.astype(np.float32).tobytes())

    print(f"{get_timestamp()} :: Transmission Completed.")
    print("--------------------------------------------------\n")
    
    # Close the audio stream
    stream.stop_stream()
    stream.close()

def countdown_to_start(delay_until_start):
    """
    Counts down to the start of the MAC Layer transmission and prints countdown messages.
    
    Parameters:
    delay_until_start (float): Time (in seconds) until the transmission should start.
    """
    global DEVICE_ID
    
    # Countdown and display messages at intervals of 10, 5, and 1 seconds
    while delay_until_start > 0:
        if delay_until_start > 10:
            print(f"{int(delay_until_start)} seconds remaining until start.")
            time.sleep(delay_until_start - 10)
            delay_until_start = 10
        elif delay_until_start > 5:
            print("10 seconds remaining until start.")
            time.sleep(5)
            delay_until_start = 5
        elif delay_until_start > 1:
            print("5 seconds remaining until start.")
            time.sleep(4)
            delay_until_start = 1
        else:
            print("1 second remaining until start.")
            print(f"Started Sender with Device ID: {DEVICE_ID}")
            print("--------------------------------------------------\n")
            print(f"{get_timestamp()} :: Waiting for message........")
            print("--------------------------------------------------\n")
            delay_until_start = 0

def is_valid_time(start_time):
    """
    Determines if it's the correct time for this device to transmit, based on the time gap.
    
    Parameters:
    start_time (float): The start time of the MAC Layer protocol.
    
    Returns:
    bool: True if it's the correct time for the device to transmit, False otherwise.
    """
    global DEVICE_ID, TOTAL_DEVICES, GAP_DURATION
    curr_time = time.time()
    total_duration = TOTAL_DEVICES * GAP_DURATION
    elapsed_time = (curr_time - start_time) % total_duration
    device_start_time = (DEVICE_ID - 1) * GAP_DURATION
    
    # Check if the current device's time slot has arrived (within a small tolerance)
    return abs(device_start_time - elapsed_time) < 1e-1


def read_file():
    """
    Reads the bitstring, destination ID, and command from the input file.
    
    Returns:
    tuple: (bitstring, destination ID) or (None, None) if no valid message is found or file access fails.
    """
    try:
        with open(FILE_NAME, 'r') as file:
            data = file.readline().strip()
            command = file.readline().strip()
        
        # If the command is 'DONE', remove the first message block from the file
        if command == 'DONE':
            data = data.split()
            bitstring = data[0]
            dest = data[1]
            
            with open(FILE_NAME, 'r') as file:
                lines = file.readlines()
            with open(FILE_NAME, 'w') as file:
                file.writelines(lines[2:])

            return bitstring, int(dest)
        
        return None, None

    except FileNotFoundError:
        print(f"Error: The file '{FILE_NAME}' was not found.")
        return None, None
    except IOError:
        print(f"Error: Unable to read/write to the file '{FILE_NAME}'.")
        return None, None


def engine():
    """
    Main engine for controlling the MAC Layer process, handling the message queue, 
    and scheduling transmissions based on the device's assigned time slots.
    """
    global DEVICE_ID, TOTAL_DEVICES

    # Get device and network configuration from user
    DEVICE_ID = int(input("Enter the device ID: "))
    TOTAL_DEVICES = int(input("Enter the total number of devices: "))

    # Calculate the start time (next minute)
    print(f"Current time is {get_timestamp()}.")
    rem_time = (60 - time.time() % 60)
    start_time = time.time() + rem_time
    print(f"The MAC Layer will start at next minute. (in {round(rem_time, 2)} seconds)\n")
    
    msg_queue = []  # Queue to store messages
    countdown_to_start(rem_time)

    last_print_time = time.time()  # Track when the last "waiting" message was printed

    while True:
        # Read messages from the file
        bitstring, dest = read_file()
        if bitstring is not None:
            encoded_bitstring = encode_message(bitstring, dest)
            print("\n--------------------------------------------------")
            print(f"{get_timestamp()} :: Detected Message: \t\t{bitstring}")
            print(f"{get_timestamp()} :: Destination Node ID: \t\t{dest}")
            
            # Validate the destination and message length before adding to the queue
            if (dest <= TOTAL_DEVICES and dest >= 0) and len(bitstring) <= 15:
                msg_queue.append(encoded_bitstring)
                print(f"{get_timestamp()} :: One msg added to queue: \t{encoded_bitstring}")
            else:
                if not (dest <= TOTAL_DEVICES and dest >= 0):
                    print(f"{get_timestamp()} :: Destination ID is invalid. Discarding message....")
                else:
                    print(f"{get_timestamp()} :: Message is too long. Discarding message....")
                print(f"{get_timestamp()} :: Waiting for next message........")

            print("--------------------------------------------------\n")

        while len(msg_queue) != 0:
            # Only print the "waiting" message every second
            current_time = time.time()
            if current_time - last_print_time >= 1:
                print(f"{get_timestamp()} :: Waiting to send message....")
                last_print_time = current_time

            # Check if it's the right time to transmit
            if is_valid_time(start_time):
                print("\n--------------------------------------------------")
                print(f"Transmitting bitstring: {msg_queue[0]}")
                transmit(msg_queue[0])
                msg_queue.pop(0)
                print("\n--------------------------------------------------")
                print(f"[SENT]: {bitstring} {dest} {get_timestamp()}")
                print("--------------------------------------------------\n")
                print(f"Waiting for next message........")
                print("--------------------------------------------------\n")

        
if __name__ == "__main__":
    engine()

# Close PyAudio when done
p.terminate()
