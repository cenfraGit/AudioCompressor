import pyaudio

class AudioData:
    def __init__(self):
        self.CHUNK = 2048
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = None
        self.RATE = None
