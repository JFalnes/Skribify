import asyncio
import logging
import os
import threading
from dotenv import load_dotenv
import openai
from pytube import YouTube
import json
import datetime

__version__ = '0.1.2'

if not os.path.exists('logs/'):
    os.makedirs('logs/')
if not os.path.exists('data/'):
    os.makedirs('data/')
logging.basicConfig(filename='logs/log.log',
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)

console = logging.StreamHandler()

logging.getLogger('').addHandler(console)

# Default prompt for the transcription
default_prompt = '''Summarize the following text in 4 sentences: '''

class Downloader:
    def __init__(self, url, downloads_folder="downloads"):
        self.url = url
        self.downloads_folder = downloads_folder

    async def download(self):
        loop = asyncio.get_event_loop()
        youtube_object = YouTube(self.url, use_oauth=True, allow_oauth_cache=True)
        audio_stream = youtube_object.streams.filter().get_lowest_resolution()
        if not os.path.exists(self.downloads_folder):
            os.makedirs(self.downloads_folder)
        downloaded_file_path = os.path.join(self.downloads_folder, os.path.basename(audio_stream.default_filename))
        if os.path.isfile(downloaded_file_path):
            return downloaded_file_path
        else:
            try:
                downloaded_file_path = await loop.run_in_executor(None, lambda: audio_stream.download(self.downloads_folder))
                return downloaded_file_path
            except Exception as e:
                logging.error(f'Download failed! {e}')
                return None


class Transcriber:
    def __init__(self, file_path):
        self.file_path = file_path

    async def transcribe(self):
        try:
            with open(self.file_path, 'rb') as audio_file:
                transcript_obj = openai.Audio.transcribe('whisper-1', audio_file)
                transcript = transcript_obj['text']
                return transcript
        except Exception as e:
            logging.error(f'Transcription failed! {e}')
            return None


class Summarizer:
    def __init__(self, transcript, prompt, model):
        self.transcript = transcript
        self.prompt = prompt
        self.model = model

    async def summarize(self):
        try:
            loop = asyncio.get_event_loop()
            completion = await loop.run_in_executor(None, lambda: openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {'role': 'user', 'content': f'{self.prompt}:{self.transcript}'}
                ]
            ))

            return completion
        except Exception as e:
            logging.error(f'Error during completion: {e}')
            return None

class Scribe():
    '''
    A class used to transcribe and summarize video or audio content.
    '''
    def __init__(self, callback, prompt=default_prompt, url_entry=None, file_entry=None, transcribe_only=False, flask=False, model='gpt-4', of='data'):
        '''
        Initialize Scribe instance.
        
        :param callback: Function to call with the transcription result
        :param prompt: Prompt to be used for summarizing the transcription (default: default_prompt)
        :param url_entry: URL to download video or audio content (default: None)
        :param file_entry: Local file path of video or audio content (default: None)
        :param flask: Whether or not to run the transcription process in a Flask app (default: False)
        '''
        
        self.url_entry = url_entry
        self.file_entry = file_entry
        self.prompt = prompt
        self.callback = callback
        self.transcribe_only = transcribe_only
        self.flask = flask
        self.model = model
        self.of = of
        self.loop = asyncio.get_event_loop()
        self.transcription_done = threading.Event()

        self.data_dict = {}
        def set_api_key_env(api_key):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            env_path = os.path.join(script_dir, '.env')
            os.environ['TOKEN'] = api_key

            with open(env_path, 'w') as f:
                f.write(f'TOKEN={api_key}')

        load_dotenv()  

        api_key = os.environ.get('TOKEN')
        if api_key is None:
            api_key = input('Please enter your OpenAI API Key: ')
            set_api_key_env(api_key)
            os.environ['TOKEN'] = api_key

        openai.api_key = api_key


    def run(self):
        '''
        Run the transcription process based on the provided input (URL or file).
        '''
        if self.url_entry and not self.file_entry:
            self.data_dict['url'] = self.url_entry
            return self.loop.create_task(self.transcribe_from_url(self.url_entry))
        
        elif self.file_entry and not self.url_entry:
            return self.transcribe_from_file(self.file_entry)
        
        elif self.url_entry and self.file_entry:
            logging.error('Error: Please provide either a URL or a file path, not both.')
        else:
            logging.error('Error: Please provide either a URL or a file path.')
    
    async def transcribe_from_url(self, url):
        downloader = Downloader(url)
        file_path = await downloader.download()
        if file_path is not None:
            self.data_dict['url'] = url

            await self.transcribe_from_file(file_path)

    async def transcribe_from_file(self, file_path):
        transcriber = Transcriber(file_path)
        transcript = await transcriber.transcribe()
        if transcript is not None:
            self.data_dict['file'] = file_path
            self.data_dict['transcript'] = transcript
            if self.transcribe_only:
                print(transcript)
            else:
                await self.summarize(transcript)

    async def summarize(self, transcript):
        summarizer = Summarizer(transcript, self.prompt, self.model)
        summary = await summarizer.summarize()
        if summary is not None:
                self.data_dict['prompt'] = self.prompt
                self.data_dict['summary'] = summary

                now = datetime.datetime.now()
                now_str = now.strftime('%Y-%m-%d_%H-%M-%S')

                directory = 'data'
                json_file = f'{directory}/{self.of}_{now_str}.json'

                with open(json_file, 'w') as f:
                    json.dump(self.data_dict, f, indent=4)
                content = summary['choices'][0]['message']['content']
                self.callback(content)


    def __enter__(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.loop.close()


