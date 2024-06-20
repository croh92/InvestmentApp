import assemblyai as aai
import time
import os

class PodcastTranscriber:
    def __init__(self):
        self.api_key = os.environ.get("ASSEMBLYAI_API_KEY")
        aai.settings.api_key = self.api_key

    def upload_to_assemblyai(self, audio_file_path):
        transcriber = aai.Transcriber()
        upload_response = transcriber.upload(audio_file_path)
        return upload_response['upload_url']

    def transcribe(self, audio_url):
        transcriber = aai.Transcriber()
        transcription = transcriber.transcribe(audio_url)
        while transcription['status'] != 'completed':
            time.sleep(5)
            transcription = transcriber.transcription(transcription['id'])
        if transcription['status'] == 'completed':
            return transcription['text']
        elif transcription['status'] == 'failed':
            raise Exception("Transcription failed")

# Example usage of PodcastTranscriber
if __name__ == "__main__":
    assemblyai_api_key = 'your_assemblyai_api_key'
    transcriber = PodcastTranscriber()
    audio_file_path = 'AIInvest/DOJ targets Nvidia, Meme stock comeback, Trump fundraiser in SF, Apple-OpenAI, Texas stock market.mp3'

    # Upload and transcribe audio
    audio_url = transcriber.upload_to_assemblyai(audio_file_path)
    transcript = transcriber.transcribe(audio_url)
    breakpoint
    print("Transcript:")
    print(transcript)