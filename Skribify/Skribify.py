import asyncio
import logging
import os
import threading
import openai
import json
import datetime
from pydub import AudioSegment
import shutil
from openai import OpenAI
from pathlib import Path
import pkg_resources
import time

try:
    from .config import setup as config_setup
except ImportError:
    from config import setup as config_setup

config_setup()

client = OpenAI()

__version__ = '0.2'


logging.basicConfig(filename='logs/log.log',
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.INFO)

console = logging.StreamHandler()

logging.getLogger('').addHandler(console)

# Default prompt for the transcription
DEFAULT_PROMPT = 'Summarize the following video in two sentences:'
CHUNK_DURATION_MS = 2 * 60 * 1000  # 2 minutes
TEMP_CHUNKS_DIR = "chunks"
TRANSCRIPTION_MODEL = 'whisper-1'

prompt_file_path = pkg_resources.resource_filename(__name__, 'prompt.txt')

with open(prompt_file_path, 'r') as prompt_file:
    SYSTEM_PROMPT = prompt_file.read().strip()

class Transcriber:
    def __init__(self, file_path, chunks_folder=TEMP_CHUNKS_DIR):
        self.file_path = file_path
        self.chunks_folder = chunks_folder
        self.loop = asyncio.get_event_loop()  # Get the event loop and store it

    def split_by_duration(self, audio_segment, CHUNK_DURATION_MS):
        chunks = []
        while len(audio_segment) > CHUNK_DURATION_MS:
            chunks.append(audio_segment[:CHUNK_DURATION_MS])
            audio_segment = audio_segment[CHUNK_DURATION_MS:]
        chunks.append(audio_segment)
        return chunks

    async def transcribe_chunk(self, chunk, chunk_index):
        """Asynchronously transcribe a single chunk."""
        try:
            chunk_file = os.path.join(self.chunks_folder, f'chunk{chunk_index}.{self.file_path.split(".")[-1]}')
            chunk.export(chunk_file, format=self.file_path.split(".")[-1])

            with open(chunk_file, 'rb') as audio_file:
                transcript_obj = await self.loop.run_in_executor(None, lambda: client.audio.transcriptions.create(model=TRANSCRIPTION_MODEL, file=audio_file))
            return transcript_obj.text

        except Exception as e:
            logging.error(f'\nTranscription of chunk {chunk_index} failed: {e}')
            return ''

    async def transcribe(self):
        start_time = time.time()  # Start time for transcription
        total_transcript = ''
        audio = await self.loop.run_in_executor(None, AudioSegment.from_file, self.file_path)

        duration = len(audio) / 1000  # Duration in seconds
        chunk_duration_ms = 2 * 60 * 1000
        chunks = self.split_by_duration(audio, chunk_duration_ms)
        chunks_count = len(chunks)  # Number of chunks

        if not os.path.exists(self.chunks_folder):
            os.makedirs(self.chunks_folder)

        # Create a coroutine for each chunk and gather them to run concurrently.
        transcribe_tasks = [self.transcribe_chunk(chunk, i) for i, chunk in enumerate(chunks)]
        transcripts = await asyncio.gather(*transcribe_tasks)

        shutil.rmtree(self.chunks_folder, ignore_errors=True)

        transcription_time = time.time() - start_time  # Time taken for transcription
        return {'transcript': ' '.join(transcripts).strip(), 'duration': duration, 'chunks_count': chunks_count, 'transcription_time': transcription_time}

        
class Summarizer:
    def __init__(self, transcript, prompt, system, model):
        # Store the user instructions separately.
        self.user_instructions = "\nUser Instructions: "  
        self.transcript = transcript  # Keep the actual transcript clean.
        self.prompt = prompt
        self.system = system
        self.model = model

    async def summarize(self):
        try:
            loop = asyncio.get_event_loop()
            # Pass the user instructions along with the transcript to the model.
            # But do not include it in the output directly.
            completion = await loop.run_in_executor(None, lambda: client.chat.completions.create(
                model=self.model,
                messages=[   
                    {"role": "system", "content": self.system},
                    {'role': 'user', 'content': self.transcript + self.user_instructions},
                    {'role': 'user', 'content': self.prompt}
                ]
            ))

            return completion
        except BaseException as e: # change this once i know what to expect
            if 'context_length_exceeded' in str(e):
                logging.error(f'\nThe provided transcript is too long for the model. '
                              f'The maximum context length is 4096 tokens, but the transcript '
                              f'resulted in more than this limit. Please shorten the transcript and retry.\n')
            else:
                logging.error(f'\nError during completion: {e}\n')
            return None
        

class Skribify():
    '''
    A class used to transcribe and summarize video or audio content.
    '''
    def __init__(self, callback, prompt=DEFAULT_PROMPT, system=SYSTEM_PROMPT, url_entry=None, file_entry=None, transcribe_only=False, flask=False, model='gpt-4-1106-preview', of='output'):
        '''
        Initialize Skribify instance.
        
        :param callback: Function to call with the transcription result
        :param prompt: Prompt to be used for summarizing the transcription (default: DEFAULT_PROMPT)
        :param url_entry: URL to download video or audio content (default: None)
        :param file_entry: Local file path of video or audio content (default: None)
        :param flask: Whether or not to run the transcription process in a Flask app (default: False)
        '''
        
        self.url_entry = url_entry
        self.file_entry = file_entry
        self.prompt = prompt
        self.system = system
        self.callback = callback
        self.transcribe_only = transcribe_only
        self.flask = flask
        self.model = model
        self.of = of
        self.loop = asyncio.get_event_loop()
        self.transcription_done = threading.Event()
        self.data_dict = {}


    async def transcribe_from_file(self, file_path):
        transcriber = Transcriber(file_path)  # This line was missing or incorrectly placed
        transcribe_result = await transcriber.transcribe()  # Now 'transcriber' is defined
        transcript = transcribe_result['transcript']
        file_size_bytes = os.path.getsize(file_path)  # Get the file size in bytes
        file_size_kb = file_size_bytes / 1024
        response = {
            "file": file_path,
            "transcript": transcript,
            "summary": None,
            "duration": transcribe_result['duration'],
            "chunks_count": transcribe_result['chunks_count'],
            "transcription_time": transcribe_result['transcription_time'],
            "file_size_kb": file_size_kb, 
            "file_format": Path(file_path).suffix[1:],  # Without the dot
        }

        if transcript is not None and not self.transcribe_only:
            summarization_start_time = time.time()
            summary = await self.summarize(transcript)
            summarization_time = time.time() - summarization_start_time
            if summary is not None:
                response['summary'] = summary.choices[0].message.content
                response['summarization_time'] = summarization_time

        if self.flask and self.callback:
            await self.callback(response)
        else:
            return response

    async def summarize(self, transcript):
        summarizer = Summarizer(transcript, self.prompt, self.system, self.model)
        try:
            summary = await summarizer.summarize()
            return summary
        except BaseException as e:
            if 'context_length_exceeded' in str(e):
                logging.error(f'\nThe provided transcript is too long for the model. '
                              f'The maximum context length is 4096 tokens, but the transcript '
                              f'resulted in more than this limit. Please shorten the transcript and retry.\n')
            else:
                logging.error(f'\nError during completion: {e}\n')
            return None
        
    async def run(self):
        logging.info(self.model)
        if self.file_entry:
            result = await self.transcribe_from_file(self.file_entry)  # Obtain result from transcription
            return result  # Return the result back to the caller
        else:
            logging.error('\nError: Please provide a valid file path.\n')
            return None  # Return None or an appropriate error indicator

    def __enter__(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.loop.close()


