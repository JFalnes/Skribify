import os
import sys

scribe_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Skribify'))
sys.path.append(scribe_dir)

from Skribify import Skribify

def handle_transcription(transcription):
    print(transcription)

file = "<path to file>"
prompt = "Summarize the following text: "

with Skribify(callback=handle_transcription, prompt=prompt, file_entry=file, model='gpt-3.5-turbo') as skribify:
    skribify.loop.run_until_complete(skribify.run())