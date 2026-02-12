import os
from openai import OpenAI


def transcribe(audio_path, api_key):
    """Transcribe audio file using OpenAI Whisper API. Returns text."""
    client = OpenAI(api_key=api_key)

    with open(audio_path, "rb") as f:
        result = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            language="fr",
        )

    os.unlink(audio_path)
    return result.text
