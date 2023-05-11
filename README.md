# SCRIBE 0.1.2
Scribe is a powerful transcription and summarization tool that leverages the power of OpenAI's GPT-4 and WhisperAI to generate concise summaries from video or audio content. With support for both local files and YouTube videos, Scribe makes it easy to extract valuable insights from your media files.

## **Table of Contents**
* <u>Features</u>
* <u>Installation</u>
* <u>Usage</u>
  * <u>Command Line Interface</u>
  * <u>Example: get_transcript.py</u>
* <u>Contributing</u>
* <u>License</u>
## **Features**
* Transcribe and summarize video or audio content.
* Supports local files and YouTube videos.
* Customizable summarization prompts.
* Detailed logging for debugging and tracking progress.
  
## <u>Installation</u>
1. Clone this repository:
    ```bash
    git clone https://github.com/jfalnes/Scribe.git
    ```

2. Install the required dependencies:

    ```bash
    pip install -r requirements.txt
    ```
    2b. Install as a package:
    ```bash
    pip install git+https://github.com/jfalnes/Scribe.git
    ```
3. Set up your OpenAI API key:
   * Scribe uses GPT4, if you do not have a GPT4 API key, you can request access to the beta [here](https://openai.com/waitlist/gpt-4-api).
   * Obtain an OpenAI API key from OpenAI
   * Create a .env file in the project root directory and add your API key as follows:

       ```makefile
       TOKEN=your_openai_api_key
       ```
4. Set up your Google API key:
   * Follow the prompt to open https://www.google.com/device in your web browser.
   * Enter the code provided by the script (e.g., "DBTH-BTYV") on the webpage and authenticate your account.
   *   Return to the terminal and press enter to continue the script.



## **Usage**
### **Command Line Interface**
Scribe can be used from the command line by providing the required arguments:

* **`--url`, `-u`**: URL of the YouTube video to transcribe and summarize.
* **`--file`, `-f`**: Path of the local video or audio file to transcribe and summarize.
* **`--prompt`, `-p`**: Custom prompt for the summarization or path to a file containing the prompt (default: "Summarize the following text: ")
* **`--transcribe`, `-t`**: Transcribe only the video or audio file, and make no changes.

```bash
python Scribe.py --url https://www.youtube.com/watch?v=your_video_id
```

or

```bash
python Scribe.py --file path/to/your/video_or_audio_file
```


You can use the **`--prompt`** argument to provide a custom prompt for the summarization, either as a direct string or by specifying the path to a file containing the prompt. 

## **Example: get_transcript.py**

You can also use Scribe in your Python script as follows:

```python
from Scribe import Scribe

def handle_transcription(transcription):
    print(transcription)

url = "https://www.youtube.com/watch?v=your_video_id"
prompt = "Summarize the following text: "

with Scribe(callback=handle_transcription, prompt=prompt, url_entry=url) as scribe:
    pass
```
## **Example Output**
### **Input**
- URL: https://www.youtube.com/watch?v=jNQXAC9IVRw
- Prompt: 'Summarize the following text'

### **Command used**:
```bash
py .\Scribe.py --url https://www.youtube.com/watch?v=jNQXAC9IVRw --prompt 'Summarize the following text: '
```
### **Output**:
```
The text discusses elephants and highlights their impressively long fronts as a cool feature.
```
## **Planned Features**
* Support for files over 25MB

## **Contributing**
We welcome contributions! Please feel free to submit a pull request for new features, bug fixes, or improvements.

## **License**
Scribe is released under the <u>**GNU General Public License v3.0**</u>. See  [LICENSE](LICENSE) for more information.