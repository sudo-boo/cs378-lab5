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
