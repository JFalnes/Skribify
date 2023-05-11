import argparse
import asyncio
import logging
import os
import threading
from dotenv import load_dotenv
import openai
from pytube import YouTube


__version__ = '0.1.1'

load_dotenv()

if not os.path.exists('logs/'):
    os.makedirs('logs/')
    
logging.basicConfig(filename='logs/log.log',
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)

console = logging.StreamHandler()
console.setLevel(logging.INFO)

logging.getLogger('').addHandler(console)

# Default prompt for the transcription
default_prompt = '''Summarize the following text in 4 sentences: '''


class Scribe():
    '''
    A class used to transcribe and summarize video or audio content.
    '''
    def __init__(self, callback, prompt=default_prompt, url_entry=None, file_entry=None, transcribe_only=False, flask=False):
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

        self.loop = asyncio.get_event_loop()
        self.transcription_done = threading.Event()

        api_key = os.environ.get('TOKEN')
        if api_key is None:
            api_key = input('Please enter your OpenAI API Key: ')
            self.set_api_key_env(api_key)

        openai.api_key = api_key

    def set_api_key_env(self, api_key):
        '''
        Set the OpenAI API key as an environment variable.
        
        :param api_key: The OpenAI API key
        '''
        os.environ['TOKEN'] = api_key

    def run(self):
        '''
        Run the transcription process based on the provided input (URL or file).
        '''
        if self.url_entry and not self.file_entry:
            return self.loop.create_task(self.transcribe_from_url(self.url_entry))
        elif self.file_entry and not self.url_entry:
            return self.transcribe_from_file(self.file_entry)
        elif self.url_entry and self.file_entry:
            logging.error('Error: Please provide either a URL or a file path, not both.')
        else:
            logging.error('Error: Please provide either a URL or a file path.')
    
    async def transcribe_from_url(self, url):
        '''
        Transcribe the content from the provided URL.
        
        :param url: URL to download video or audio content
        '''
        logging.info('Transcribing from URL.')
        await self.url_download(url)

    async def url_download(self, url):
        '''
        Download video or audio content from the provided URL.
        
        :param url: URL to download video or audio content
        '''
        
        loop = asyncio.get_event_loop()

        youtube_object = YouTube(url, use_oauth=True, allow_oauth_cache=True)
        audio_stream = youtube_object.streams.filter().get_lowest_resolution()

        # Check and create 'downloads' folder if it doesn't exist
        downloads_folder = "downloads"
        if not os.path.exists(downloads_folder):
            os.makedirs(downloads_folder)

        downloaded_file_path = os.path.join(downloads_folder, os.path.basename(audio_stream.default_filename))
        logging.info('Checking if file is already saved.')

        if os.path.isfile(downloaded_file_path):
            logging.info(f'File "{downloaded_file_path}" already exists. Skipping download.')
        else:
            try:
                logging.info('Downloading from URL.')
                downloaded_file_path = await loop.run_in_executor(None, lambda: audio_stream.download(downloads_folder))
            except Exception as e:
                logging.error(f'Download failed! {e}')
                return

            downloaded_filename = os.path.basename(downloaded_file_path)
            logging.info('Download complete: %s', downloaded_filename)

        await self.transcribe_from_file(downloaded_file_path)

    async def transcribe_from_file(self, file_path, transcribe_only=None):
        '''
        Transcribe the content from the provided file.
        
        :param file_path: Local file path of video or audio content
        '''
        # TODO: split files over 25MB into chunks and transcribe each chunk, then combine the results
        logging.info('Loading file.')

        try:
            with open(file_path, 'rb') as audio_file:
                logging.info('Loaded file. Transcribing.')
                transcript_obj = openai.Audio.transcribe('whisper-1', audio_file)
                transcript = transcript_obj['text'].encode('unicode_escape').decode('utf-8')
                logging.info('Transcription of audio complete. Summarizing.')


            if self.transcribe_only:
                print(transcript)
            else:
                await self.transcribe(self.prompt, transcript)

        except Exception as e:
            logging.error(f'Transcription failed! {e}')
            return

    async def transcribe(self, prompt, user_prompt):
        '''
        Summarize the provided transcription using the specified prompt.
        
        :param prompt: Prompt to be used for summarizing the transcription
        :param user_prompt: Transcribed content to be summarized
        '''
        logging.info('Parsing prompt, please wait.')

        try:
            loop = asyncio.get_event_loop()
            completion = await loop.run_in_executor(None, lambda: openai.ChatCompletion.create(
                model='gpt-4',
                messages=[
                    {'role': 'user', 'content': f'{prompt}:{user_prompt}'}
                ]
            ))
        except Exception as e:
            logging.error(f'Error during completion: {e}')
            return
        
        logging.info('Prompt parsed.')
        # TODO: Fix unicode escape characters and proper formatting
        response = completion.choices[0].message
        content = response['content'].encode('unicode_escape').decode('utf-8')
        logging.info('Transcription complete.')

        with open(os.path.join(os.getcwd(), 'transcription.txt'), 'w') as f:
            f.write(content)
            f.close()

        if self.flask:
            await self.callback(content)
        else:
            self.callback(content)

        self.transcription_done.set()


    def __enter__(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.loop.close()


