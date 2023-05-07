import os
import sys

scribe_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Scribe'))
sys.path.append(scribe_dir)

from Scribe import Scribe

def handle_transcription(transcription):
    print(transcription)

url = "https://www.youtube.com/watch?v=8FC7TYAnKW4"
prompt = "Summarize the following text: "

with Scribe(callback=handle_transcription, prompt=prompt, url_entry=url) as scribe:
    scribe.loop.run_until_complete(scribe.run()) 