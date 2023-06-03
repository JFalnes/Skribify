import os
from dotenv import load_dotenv
import openai
import subprocess


def set_api_key_env(api_key):
    project_dir = os.getcwd() 
    env_path = os.path.join(project_dir, '.env')
    openai.api_key = api_key

    with open(env_path, 'w') as f:
        f.write(f'OPENAI_API_KEY={api_key}')


def ensure_folders():
    if not os.path.exists('logs/'):
        os.makedirs('logs/')
    if not os.path.exists('output/'):
        os.makedirs('output/')


def is_ffmpeg_installed():
    try:
        subprocess.run(['ffmpeg', '-version'], check=True)
        print('\nffmpeg is installed on this system\n')
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def setup():
    load_dotenv()  

    api_key = os.environ.get('OPENAI_API_KEY')
    if api_key is None:
        api_key = input('\nPlease enter your OpenAI API Key: ')
        set_api_key_env(api_key)
        os.environ['OPENAI_API_KEY'] = api_key

    ensure_folders()

    if not is_ffmpeg_installed():
        raise SystemExit('\nffmpeg is not installed on this system\n')
    
if __name__ == "__main__":
    setup()