import asyncio
from flask import Blueprint, render_template, request, jsonify
import os
scribe_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Skribify'))
from .async_skribify import AsyncSkribify
main = Blueprint('main', __name__)

def run_asyncio_coroutine(coroutine):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coroutine)
    finally:
        loop.close()

@main.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['url']
        prompt = request.form['prompt']

        async def handle_skribify():
            transcription_result = None
            async def handle_transcription(transcription):
                nonlocal transcription_result

                print(transcription)

                transcription_result = transcription
            

            async with AsyncSkribify(callback=handle_transcription, prompt=prompt, url_entry=url, flask=True) as skribify:  
                await skribify.run()
            
            return transcription_result 
        
        
        result = run_asyncio_coroutine(handle_skribify())

        return render_template('result.html', result=result)

    return render_template('index.html')