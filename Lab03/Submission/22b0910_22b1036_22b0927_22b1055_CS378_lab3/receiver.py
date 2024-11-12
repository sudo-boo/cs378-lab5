import pyaudio
import numpy as np
import time
from datetime import datetime
import matplotlib.pyplot as plt
from scipy.signal import butter, lfilter
import threading

# Parameters
SAMPLE_RATE = 20000         # Sample rate for audio recording (in Hz)
CHUNK = 1024                # Buffer size for reading audio data
BIT_DURATION = 1            # Duration allocated for each bit in the bitstream (seconds)
DURATION = 20                # Duration for which audio will be recorded during each slot (seconds)
GAP_DURATION = 20            # Gap between transmission slots (seconds)
TOLERANCE = 100             # Frequency detection tolerance (to account for minor variations)
DEVICE_ID = 1               # Device ID for identifying which device is receiving
TOTAL_DEVICES = 3           # Total number of devices communicating in the network

# List to hold frequency bands for filtering
lowcuts = []
highcuts = []
freqs = [5000, 5500, 6000, 6500]  # Frequencies used for transmitting bits

# Timestamps for each recorded session
timestamps = []

# Compute the lower and upper bounds for bandpass filtering based on the given tolerance
for freq in freqs:
    lowcuts.append(freq - TOLERANCE)
    highcuts.append(freq + TOLERANCE)

# Map each frequency to a 2-bit string for demodulating the bitstream
mapping = {
    0: '00',
    1: '01',
    2: '10',
    3: '11'
}

# Initialize PyAudio to handle audio recording
p = pyaudio.PyAudio()
# Open a stream for recording audio
stream = p.open(format=pyaudio.paFloat32,
                channels=1,
                rate=SAMPLE_RATE,
                input=True,
                frames_per_buffer=CHUNK)


def detect_frequency(data, sample_rate):
    """
    Detect the frequency of the given audio chunk by performing FFT.
    """
    # Apply Fast Fourier Transform (FFT) to convert time domain data to frequency domain
    fft_data = np.fft.fft(np.frombuffer(data, dtype=np.float32))
    frequencies = np.fft.fftfreq(len(fft_data), 1 / sample_rate)
    
    # Only use the positive half of the frequency data
    frequencies = frequencies[:len(frequencies)//2]
    fft_data = np.abs(fft_data[:len(fft_data)//2])
    
    # Find the frequency with the highest peak (strongest signal)
    peak_index = np.argmax(fft_data)
    peak_freq = frequencies[peak_index]
    
    return peak_freq

def convert(current_time):
    """
    Convert a timestamp from time.time() to a readable HH-MM-SS format with milliseconds.
    """
    return datetime.fromtimestamp(current_time).strftime("%H-%M-%S_%f")[:-3]

def get_timestamp():
    """
    Get the current timestamp in the format HH:MM:SS.ms.
    """
    curr_time = datetime.now()
    return curr_time.strftime("%H:%M:%S.%f")[:-3]

def process_audio_data(audio_data):
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
    

    audio_data = np.array(audio_data)
    audio_data *= 100
    audio_data = audio_data[10000:]

    noise = 0.009

    def filter_data(audio_data, lowcuts, highcuts, SAMPLE_RATE, i):
        """
        Apply bandpass filters to extract the desired frequency ranges.
        """
        filtered_data = bandpass_filter(audio_data, lowcuts[i], highcuts[i], SAMPLE_RATE)
        filtered_data = np.abs(filtered_data)
        for j in range(len(filtered_data)):
            if filtered_data[j] > 0.5:
                filtered_data[j] = 0.5
            if filtered_data[j] > noise:
                filtered_data[j] -= noise
        return filtered_data

    f_datas = []
    for i in range(len(freqs)):
        f_datas.append(filter_data(audio_data, lowcuts, highcuts, SAMPLE_RATE, i))    

    # Find the starting index of the transmission in each filtered signal
    starting_idxs = []

    def compute_threshold(signal, factor=1.0):
        """
        Compute a threshold for detecting signal changes.
        """
        mean = np.mean(signal)
        std_dev = np.std(signal)
        threshold = mean + factor * std_dev
        return threshold
    
    threshold = compute_threshold(f_datas[0], factor=1.0)

    def compute_starting_idx(filtered_data):
        """
        Compute the starting index of the transmission in the filtered data.
        """
        # threshold = compute_threshold(filtered_data, threshold)
        for i in range(1000, len(filtered_data) - 100):
            if abs(avg(filtered_data[i:i + 100]) - avg(filtered_data[i - 100:i])) > threshold:
                starting_idx = i
                return starting_idx
        return 0
        
    # Compute the starting index of the transmission
    for i in range(len(f_datas)):
        starting_idxs.append(compute_starting_idx(f_datas[i]))

    for i in range(len(f_datas)):
        f_datas[i] = abs(f_datas[i])

    bitstring = ''
    s_idx = min(starting_idxs)

    for i in range(s_idx, len(f_datas[0]), int(SAMPLE_RATE * BIT_DURATION)):
        avgs = []
        for j in range(len(f_datas)):
            avgs.append(avg(f_datas[j][i:i + int(SAMPLE_RATE * BIT_DURATION)]))
        max_avg = max(avgs)
        added_bs = mapping[avgs.index(max_avg)]
        bitstring += added_bs

    # plot_data(f_datas)

    return bitstring

def decode_bitstring(bitstring):
    """
    Decode the received bitstream to extract the actual message and source.
    """
    global DEVICE_ID
    preambles = ["1011"]  # Preamble to indicate the start of a valid message
    for preamble in preambles:
        if preamble == bitstring[:len(preamble)]:
            without_pr = bitstring[len(preamble):]
            # First 5 bits represent the length of the message
            length = int(without_pr[:5], 2)
            message = without_pr[5:5 + length]
            # Next 2 bits represent the destination device
            dest = int(message[:2], 2)

            # Check if the message is meant for this device or is broadcast (0)
            if dest == DEVICE_ID or dest == 0: 
                source = int(message[2:4], 2)  # Extract the source device ID
                return source, message[4:]
            
    return None, None

def decode_and_print(audio_data, timestamp, count):
    """
    Decoding in a separate thread.
    """
    global DEVICE_ID
    source, message = decode_bitstring(process_audio_data(audio_data))
    print("\n--------------------------------------------------")
    if source is not None:
        print(f"[RECVD]: {message} {source} {timestamp}")
    else:
        print(f"{get_timestamp()} :: Invalid bitstream for {timestamp} slot")
    if count == 1:
        print(f"Waiting till next slot...")
    print("--------------------------------------------------\n")



def record_bitstream(count):
    """
    Record audio, filter signals, and extract bit string from the audio data.
    """
    global timestamps, TOTAL_DEVICES
    
    st = time.time()
    print("==================================================")
    print(f"{get_timestamp()} :: Starting recording...\n")
    
    # List to hold the audio data
    audio_data = []

    t = st

    try:
        while count > 0:
            data = stream.read(CHUNK, exception_on_overflow=False)
            chunk = np.frombuffer(data, dtype=np.float32)
            audio_data.extend(chunk)
            # print(abs(time.time() - t))
            if abs(time.time() - t) > DURATION:

                # Start a new thread for decoding while recording continues
                decoding_thread = threading.Thread(target=decode_and_print, args=(audio_data, get_timestamp(), count))
                decoding_thread.start()

                t = time.time()            
                audio_data = []
                count -= 1


    except KeyboardInterrupt:
        print("Stopped recording.")

    finally:
        print(f"\n{get_timestamp()} :: Recording stopped.")
        print("==================================================\n")


def plot_data(f_datas):
        # Plot the filtered data1 and filtered data2
    plt.figure(figsize=(10, 6))
    time_axis = np.linspace(0, len(f_datas[0]) / SAMPLE_RATE, num=len(f_datas[0]))

    for i in range(len(f_datas)):
        plt.plot(time_axis, f_datas[i], label=f"Filtered Data {i + 1}", alpha=0.5)

    plt.title("Filtered Data vs Time")
    plt.xlabel("Time (seconds)")
    plt.ylabel("Amplitude")
    plt.legend(loc="upper right")
    plt.grid(True)
    plt.savefig(f'{str(get_timestamp())[:-4].replace(":", "-")}.png')
    # plt.show()

def countdown_to_start(delay_until_start):
    """
    Countdown function to print messages when there are 10, 5, and 1 seconds remaining.
    
    Parameters:
    delay_until_start (float): Time in seconds to wait before starting.
    """
    global DEVICE_ID
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
            time.sleep(1)
            print(f"\nStarted Receiver with Device ID : {DEVICE_ID}")
            print("--------------------------------------------------\n")
            delay_until_start = 0

def is_valid_time(start_time):
    """
    Checks if the current time falls within the communication slot assigned to the device.
    """
    global DEVICE_ID, TOTAL_DEVICES, GAP_DURATION
    curr_time = time.time()
    total_duration = TOTAL_DEVICES * GAP_DURATION
    elapsed_time = (curr_time - start_time) % total_duration
    device_start_time = (DEVICE_ID % TOTAL_DEVICES) * GAP_DURATION
    device_end_time = device_start_time + GAP_DURATION
    if device_start_time <= elapsed_time < device_end_time:
        return True
    else:
        return False

def engine():
    """
    Main function to initialize the device, manage recording sessions, and control 
    when each device can transmit/receive based on time slots in a network.

    Globals:
        DEVICE_ID (int): The ID of the current device, entered by the user.
        TOTAL_DEVICES (int): Total number of devices participating in the network.
        GAP_DURATION (float): Time slot duration for each device.

    Functionality:
        - The user inputs the device ID and total number of devices.
        - The function calculates the remaining time until the start of the next minute 
          and schedules the device to start at that time.
        - Depending on the device ID, the system starts recording audio data and decodes 
          the bitstream during its allocated time slot in a round-robin fashion.
    """
    global DEVICE_ID, TOTAL_DEVICES, GAP_DURATION

    # Prompt user to input the device ID and the total number of devices in the network
    DEVICE_ID = int(input("Enter the device id: "))
    TOTAL_DEVICES = int(input("Enter the total number of devices: "))

    # Display current time
    print(f"Current time is {get_timestamp()}.")

    # Calculate the remaining time to start at the beginning of the next minute
    rem_time = (60 - time.time() % 60)
    start_time = time.time() + rem_time  # Time when the device will start recording
    print(f"The device will start at {start_time}. (in {rem_time} seconds)")

    if DEVICE_ID == 2:
        tempctr = 1
    else:
        tempctr = 0

    # Start the countdown until the recording begins
    countdown_to_start(rem_time)

    while True:
        if tempctr:
            record_bitstream(1)
            tempctr -= 1
        else:
            if is_valid_time(start_time):
                record_bitstream(TOTAL_DEVICES - 1)

# Start the program
if __name__ == "__main__":
    engine()

# Clean up the audio stream once the program ends
stream.stop_stream()
stream.close()
p.terminate()
