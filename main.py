import time
import pygame
import yaml
import logging
from rich.console import Console
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain.prompts import PromptTemplate
from langchain_community.llms import Ollama
from assistant_service import Assistant
from transcription import transcribe

# Global console setup
console = Console()

def load_config():
    """Loads configuration from YAML file."""
    with open('assistant.yaml', encoding='utf-8') as data:
        return yaml.safe_load(data)

def setup_logging():
    """Configures the logging."""
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def initialize_prompt_template():
    """Initializes the prompt template for the conversational model."""
    template = """
    You are a helpful assistant. Answer as concisely as possible. Keep your answer very minimum. 
    Make it brief and only say things that are needed, don't make it verbose. 

    The conversation transcript is as follows:
    {history}

    And here is the user's follow-up:
    {input}

    Your response:
    """
    return PromptTemplate(input_variables=["history", "input"], template=template)

def setup_conversation_chain(config):
    """Sets up the conversation chain with the language model."""
    return ConversationChain(
        prompt=initialize_prompt_template(),
        verbose=False,
        memory=ConversationBufferMemory(ai_prefix=config["ollama"]["ai_prefix"]),
        llm=Ollama(model=config["ollama"]["model"]),
    )

def initialize_pygame():
    """Initializes Pygame."""
    pygame.init()
    pygame.display.set_mode((config["display"]["width"], config["display"]["height"]))

def main_loop(assistant, conversation_chain):
    """Main event loop."""
    push_to_talk_key = pygame.K_SPACE
    quit_key = pygame.K_ESCAPE

    while True:
        assistant.clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == push_to_talk_key:
                    handle_push_to_talk(assistant, conversation_chain)
                elif event.key == quit_key:
                    logging.info("Quit key pressed")
                    assistant.shutdown()
                    break

def handle_push_to_talk(assistant, conversation_chain):
    """Handles the push-to-talk functionality."""
    logging.info("Push-to-talk key pressed")
    waveform = assistant.waveform_from_mic()
    transcription = transcribe(waveform)

    if not transcription.strip():  # Check if the transcription is empty or just whitespace
        message = "Not able to capture any word. Please try again."
        logging.info("No text captured in the transcription.")
        assistant.display_rec_start(transcript_text=message)
        return  # Exit the function if there's nothing to process

    display_transcription(transcription)
    response = conversation_chain.predict(input=transcription)
    display_response(response, assistant)


def display_transcription(transcription):
    """Displays the transcription in the console."""
    message = "You: " + transcription.strip()
    assistant.display_rec_start(transcript_text=message)
    console.print(f"[yellow]{message}")

def display_response(response, assistant):
    """Displays the response in the console and handles speech."""
    response_message = "Assistant: " + response.strip()
    console.print(f"[cyan]{response_message}")
    assistant.text_to_speech(response)
    assistant.display_rec_start(response_text=response_message)
    time.sleep(1)  # Pause briefly before next interaction

if __name__ == "__main__":
    setup_logging()
    config = load_config()
    initialize_pygame()
    assistant = Assistant()
    conversation_chain = setup_conversation_chain(config)
    main_loop(assistant, conversation_chain)
