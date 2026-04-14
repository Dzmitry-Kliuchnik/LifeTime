import os
import tempfile

AUDIO_UPLOAD_DIR = tempfile.mkdtemp()


def transcribe_audio_with_whisper(audio_file_path: str) -> str:
    try:
        import openai

        if not os.path.exists(audio_file_path):
            raise FileNotFoundError("Audio file not found")

        if os.path.getsize(audio_file_path) == 0:
            return "Empty audio file detected."

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return "[Mock Transcription] This is a placeholder transcription. Set OPENAI_API_KEY environment variable to use real Whisper."

        client = openai.OpenAI(api_key=api_key)

        with open(audio_file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1", file=audio_file, response_format="text"
            )

        return transcript.strip() if transcript else "No speech detected in audio."

    except Exception as e:
        if "api_key" in str(e).lower() or "openai" in str(e).lower():
            return "[Mock Transcription] OpenAI API not available. This is a placeholder transcription."
        raise Exception(f"Transcription failed: {str(e)}")


def cleanup_temp_file(file_path: str):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        print(f"Warning: Could not clean up temp file {file_path}: {e}")
