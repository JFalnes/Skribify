import argparse
import time
import logging
import sys
import os

scribe_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Skribify'))
sys.path.append(scribe_dir)

from Skribify import Skribify, __version__

def read_prompt(prompt_str):
    if os.path.isfile(prompt_str):
        with open(prompt_str, 'r') as file:
            return file.read()
    else:
        return prompt_str


def parse_command_line_arguments():
    parser = argparse.ArgumentParser(description='Skribify - A transcription and summarization tool')

    parser.add_argument('-f', '--file', type=str, help='Path of the local file to transcribe and summarize')
    parser.add_argument('-p','--prompt', type=str, default='Summarize the following text: ', help='Custom prompt for the summarization or path to a file containing the prompt')
    parser.add_argument('-v', '--version', action='version', version=f'Skribify {__version__}')
    parser.add_argument('-t', '--transcribe', action='store_true', help='Output only the transcribed text')
    parser.add_argument('-m', '--model', type=str, default='gpt-4', help='OpenAI model to use for summarization (default: gpt-4)')
    parser.add_argument('-tts', '--text-to-speech', type=bool, default=False, help='Enable text-to-speech (default: False)')
    
    return parser.parse_args()

def format_transcription(transcription):
    sentences = transcription.split('.')
    formatted_text = '\n'.join(sentence.strip() for sentence in sentences if sentence.strip())
    return formatted_text

def handle_transcription(transcription):
    formatted_transcription = format_transcription(transcription)
    print(f'\nFinal transcript: \n\n{formatted_transcription}')

def main():
    start_time = time.time()
    args = parse_command_line_arguments()


    if not args.file:
        logging.error('Error: Please provide a valid file path.')
        return

    prompt = read_prompt(args.prompt)

    with Skribify(callback=handle_transcription, prompt=prompt, file_entry=args.file, transcribe_only=args.transcribe, model=args.model) as skribify:
        skribify.loop.run_until_complete(skribify.run())

        

    end_time = time.time()
    duration = end_time - start_time
    logging.info(f'Total execution time: {duration:.2f} seconds')

if __name__ == '__main__':
    main()