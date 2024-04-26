import time
import pygame
from rich.console import Console
import logging
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain.prompts import PromptTemplate
from langchain_community.llms import Ollama
from assistant_service import Assistant
from transcription import transcribe

console = Console()

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Define the prompt template for the conversational model
template = """
You are a helpful assistant. Answer as concisely as possible. Keep your answer very minimum. 
Make it brief and only say things that are needed, don't make it verbose. 

The conversation transcript is as follows:
{history}

And here is the user's follow-up:
{input}

Your response:
"""
prompt = PromptTemplate(input_variables=["history", "input"], template=template)

# Initialize the conversation chain with Ollama model
conversation_chain = ConversationChain(
    prompt=prompt,
    verbose=False,
    memory=ConversationBufferMemory(ai_prefix="Assistant:"),
    llm=Ollama(model="mistral:7b-instruct-v0.2-q4_K_S"),
)

def main():
    pygame.init()
    pygame.display.set_mode((520, 340))
    assistant = Assistant()

    push_to_talk_key = pygame.K_SPACE
    quit_key = pygame.K_ESCAPE

    while True:
        assistant.clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == push_to_talk_key:
                    logging.info("Push-to-talk key pressed")
                    waveform = assistant.waveform_from_mic(push_to_talk_key)

                    transcription = transcribe(waveform)
                    message = "You: " + transcription.strip()
                    console.print(f"[yellow]{message}")
                    assistant.display_rec_start(transcript_text=message)

                    response = conversation_chain.predict(input=transcription)
                    response_message = "Assistant: " + response.strip()
                    console.print(f"[cyan]{response_message}")
                    assistant.display_rec_start(response_text=response_message)
                    assistant.text_to_speech(response)

                    time.sleep(1)  # Pause briefly before next interaction

                elif event.key == quit_key:
                    logging.info("Quit key pressed")
                    assistant.shutdown()

if __name__ == "__main__":
    main()
