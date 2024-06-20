import assemblyai as aai
import time
import os

class PodcastTranscriber:
    def __init__(self):
        self.api_key = os.environ.get("ASSEMBLYAI_API_KEY")
        if not self.api_key:
            raise ValueError("ASSEMBLYAI_API_KEY environment variable not set")
        aai.settings.api_key = self.api_key

    def upload_to_assemblyai(self, audio_file_path):
        # Initialize the AssemblyAI transcriber
        transcriber = aai.Transcriber()
        
        # Upload the audio file
        upload_url = transcriber.upload_file(audio_file_path)
        return upload_url

    def transcribe(self, audio_url):
        # Initialize the AssemblyAI transcriber
        transcriber = aai.Transcriber()
        
        # Request transcription
        transcript_response = transcriber.transcribe(audio_url)
        breakpoint()
        return transcript_response.text

# Example usage of PodcastTranscriber
if __name__ == "__main__":
    transcriber = PodcastTranscriber()
    audio_file_path = 'DOJ targets Nvidia, Meme stock comeback, Trump fundraiser in SF, Apple-OpenAI, Texas stock market.mp3'

    # Upload and transcribe audio
    audio_url = transcriber.upload_to_assemblyai(audio_file_path)
    transcript = transcriber.transcribe(audio_url)
    
    breakpoint()
    print("Transcript:")
    print(transcript)