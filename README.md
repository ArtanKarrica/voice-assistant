# Voice Assistant local - using  Ollama and siri voice on Mac
A completely offline voice assistant using Mistral 7b/Llama3 via Ollama and Whisper speech recognition models.

## Installing and running

1. Install [Ollama](https://ollama.ai) on your Mac.
2. Download the Mistral 7b or any other model like: phi3 using the `ollama pull mistral` command.
3. Download an [OpenAI Whisper Model](https://github.com/openai/whisper/discussions/63#discussioncomment-3798552) (base.en works fine).
4. **Create and Activate a Python Virtual Environment**:
   ```bash
   python3 -m venv venv
   source voice-assistent_env/bin/activate
   ```
5. Clone this repo somewhere.
6. Place the Whisper model in a /whisper directory in the repo root folder.
7. Make sure you have [Python](https://www.python.org/downloads/macos/) and [Pip](https://pip.pypa.io/en/stable/installation/) installed.
8. For Apple silicon support of the PyAudio library you'll need to install [Homebrew](https://brew.sh) and run `brew install portaudio`.
9. Run`pip install -r requirements.txt` to install.
10. Run `python main.py` to start the assistant.


## Setup voice on mac

1. In System Settings select Accessibility > Spoken Content
2. Select System Voice and Manage Voices...
3. For English find "Zoe (Premium)" and download it.
4. Select Zoe (Premium) as your System voice.

## Other languages
You can set up support for other languages by editing `assistant.yaml`. Be sure to download a different Whisper model in your language and change the default `modelPath`.