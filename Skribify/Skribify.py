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

try:
    from .config import setup as config_setup
except ImportError:
    from config import setup as config_setup

config_setup()

client = OpenAI()

__version__ = '0.1.9'


logging.basicConfig(filename='logs/log.log',
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.INFO)

console = logging.StreamHandler()

logging.getLogger('').addHandler(console)

# Default prompt for the transcription
default_prompt = 'Summarize the following video in two sentences:'
with open('Skribify\prompt.txt', 'r') as prompt_file:
    system_prompt = prompt_file.read().strip()

class Transcriber:
    def __init__(self, file_path, chunks_folder='chunks'):
        self.file_path = file_path
        self.chunks_folder = chunks_folder


    def split_by_duration(self, audio_segment, chunk_duration_ms):
        chunks = []
        while len(audio_segment) > chunk_duration_ms:
            chunks.append(audio_segment[:chunk_duration_ms])
            audio_segment = audio_segment[chunk_duration_ms:]
        chunks.append(audio_segment)
        return chunks

    async def transcribe(self):
        try:
            total_transcript = ''
            
            loop = asyncio.get_event_loop()
            audio = await loop.run_in_executor(None, AudioSegment.from_file, self.file_path)

            chunk_duration_ms = 2 * 60 * 1000

            chunks = self.split_by_duration(audio, chunk_duration_ms)

            file_size_MB = os.path.getsize(self.file_path) / (1024 * 1024)
            logging.info(f'\nNumber of chunks created: {len(chunks)}. File size: {file_size_MB:.2f} MB\n')

            if not os.path.exists(self.chunks_folder):
                os.makedirs(self.chunks_folder)

            for i, chunk in enumerate(chunks):
                chunk_file = os.path.join(self.chunks_folder, f'chunk{i}.{self.file_path.split(".")[-1]}')
                await loop.run_in_executor(None, chunk.export, chunk_file, self.file_path.split(".")[-1])

                with open(chunk_file, 'rb') as audio_file:
                    # Use lambda to ensure only one argument (the dictionary) is passed
                    transcript_obj = await loop.run_in_executor(None, lambda: client.audio.transcriptions.create(model='whisper-1', file=audio_file))
                    total_transcript += transcript_obj.text + ' '

            shutil.rmtree(self.chunks_folder, ignore_errors=True)
            if os.path.exists(self.chunks_folder):
                logging.error(f'\nDirectory {self.chunks_folder} was not deleted.\n')
            else:
                logging.info(f'\nDirectory {self.chunks_folder} was deleted successfully.\n')
            return total_transcript.strip()

        except Exception as e:
            logging.error(f'\nTranscription failed! {e}.')
            raise e

        
class Summarizer:
    def __init__(self, transcript, prompt, system, model):
        self.transcript = transcript + "\nUser Instructions: "  
        self.prompt = prompt
        self.model = model
        self.system = system
        print(f'PROMPT:{self.system},{self.transcript}, {self.prompt}')
    async def summarize(self):
        try:
            loop = asyncio.get_event_loop()
            completion = await loop.run_in_executor(None, lambda: client.chat.completions.create(
                model=self.model,
                messages=[   
                    {"role": "system", "content": {self.system}},  # system instructions first
                    {'role': 'user', 'content': self.transcript},  # then the transcript
                    {'role': 'user', 'content': self.prompt}  # and finally the user prompt
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
        except Exception as e:
            logging.error(f'\nAn unexpected error occurred during completion: {e}\n')
            return None
        

class Skribify():
    '''
    A class used to transcribe and summarize video or audio content.
    '''
    def __init__(self, callback, prompt=default_prompt, system=system_prompt, url_entry=None, file_entry=None, transcribe_only=False, flask=False, model='gpt-4-1106-preview', of='output'):
        '''
        Initialize Skribify instance.
        
        :param callback: Function to call with the transcription result
        :param prompt: Prompt to be used for summarizing the transcription (default: default_prompt)
        :param url_entry: URL to download video or audio content (default: None)
        :param file_entry: Local file path of video or audio content (default: None)
        :param flask: Whether or not to run the transcription process in a Flask app (default: False)
        '''
        
        self.url_entry = url_entry
        self.file_entry = file_entry
        self.prompt = prompt
        self.system = system_prompt
        self.callback = callback
        self.transcribe_only = transcribe_only
        self.flask = flask
        self.model = model
        self.of = of
        self.loop = asyncio.get_event_loop()
        self.transcription_done = threading.Event()
        self.data_dict = {}


    def run(self):
        '''
        Run the transcription process based on the provided input (URL or file).
        '''
        logging.info(self.model)

        
        if self.file_entry and not self.url_entry:
            return self.transcribe_from_file(self.file_entry)
        else:
            logging.error('\nError: Please provide a valid file path.\n')


    async def transcribe_from_file(self, file_path):
        transcriber = Transcriber(file_path)
        transcript = await transcriber.transcribe()
        if transcript is not None:
            self.data_dict['file'] = file_path
            self.data_dict['transcript'] = transcript

            self.write_to_json()

            if self.transcribe_only:
                print(transcript)
            else:
                await self.summarize(transcript)


    async def summarize(self, transcript):
        summarizer = Summarizer(transcript, self.prompt, self.system, self.model)
        summary = await summarizer.summarize()
        if summary is not None:
            self.data_dict['prompt'] = self.prompt

            # Extract only the serializable content from the summary
            content = summary.choices[0].message.content
            self.data_dict['summary'] = content  # Store only the content string

            self.write_to_json()

            if self.flask:
                await self.callback(content)
            else:
                self.callback(content)


    def write_to_json(self):
        now = datetime.datetime.now()
        now_str = now.strftime('%Y-%m-%d_%H-%M-%S')
        directory = 'output'
        json_file = f'{directory}/{self.of}_{now_str}.json'

        with open(json_file, 'w') as f:
            json.dump(self.data_dict, f, indent=4)


    def __enter__(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        return self


    def __exit__(self, exc_type, exc_value, traceback):
        self.loop.close()


