import argparse
import time
import logging
import sys
import os
import asyncio
import json
import datetime

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
    parser.add_argument('-m', '--model', type=str, default='gpt-4-1106-preview', help='OpenAI model to use for summarization (default: gpt-4)')
    
    return parser.parse_args()

def write_to_json(data, output_file):
    now = datetime.datetime.now()
    now_str = now.strftime('%Y-%m-%d_%H-%M-%S')  # Current time and date
    directory = 'output'  # Target directory
    filename = f'output_{now_str}.json'  # New filename format
    os.makedirs(directory, exist_ok=True)  # Ensure directory exists
    path_to_file = os.path.join(directory, filename)  # Full path to file

    with open(path_to_file, 'w') as f:  # Use the full path to file
        json.dump(data, f, indent=4)
    print(f"Result written to {path_to_file}")

def format_transcription(transcription):
    sentences = transcription.split('.')
    formatted_text = '\n'.join(sentence.strip() for sentence in sentences if sentence.strip())
    return formatted_text

def handle_transcription(response):
    # something needs to be done here, im just not sure what yet
    if 'transcript' in response and isinstance(response['summary'], str):
        formatted_transcription = format_transcription(response['summary'])
        print(f'\nFinal transcript: \n\n{formatted_transcription}')
    else:
        logging.error("No valid transcription found in response.")

async def main_async(args):
    start_time = time.time()

    if not args.file:
        logging.error('Error: Please provide a valid file path.')
        return

    prompt = read_prompt(args.prompt)
    skribify = Skribify(callback=handle_transcription, prompt=prompt, file_entry=args.file, transcribe_only=args.transcribe, model=args.model)
    result = await skribify.run()

    if result is not None:
        handle_transcription(result)  # Handle transcription printing or processing
        write_to_json(result, args.file)  # Write result to json using the file name as part of the output file name

    end_time = time.time()
    duration = end_time - start_time
    logging.info(f'Total execution time: {duration:.2f} seconds')

def main():
    args = parse_command_line_arguments()
    asyncio.run(main_async(args))

if __name__ == '__main__':
    main()

