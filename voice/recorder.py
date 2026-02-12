import tempfile
import sounddevice as sd
import soundfile as sf


def record_audio(sample_rate=16000):
    """Record audio from microphone until user presses Enter. Returns path to temp WAV file."""
    print("Parle maintenant... (appuie sur Entree pour arreter)")

    frames = []
    recording = True

    def callback(indata, frame_count, time_info, status):
        if recording:
            frames.append(indata.copy())

    stream = sd.InputStream(samplerate=sample_rate, channels=1, callback=callback)
    stream.start()

    input()
    recording = False
    stream.stop()
    stream.close()

    if not frames:
        return None

    import numpy as np
    audio = np.concatenate(frames, axis=0)

    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    sf.write(tmp.name, audio, sample_rate)
    return tmp.name
