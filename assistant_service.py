import sys
import pyaudio
import time
import pyttsx3
import pygame
import yaml
import numpy as np
import logging
import threading
import whisper
from rich.console import Console

# Constants
BACK_COLOR = (0,0,0)
REC_COLOR = (255,0,0)
TEXT_COLOR = (255,255,255)
TEXT_COLOR_YELLOW = (255,255,0)
TEXT_COLOR_CYAN = (0,255,255)
REC_SIZE = 80
FONT_SIZE = 15
WIDTH = 520
HEIGHT = 340
KWIDTH = 20
KHEIGHT = 6
MAX_TEXT_LEN_DISPLAY = 32

INPUT_DEFAULT_DURATION_SECONDS = 5
INPUT_FORMAT = pyaudio.paInt16
INPUT_CHANNELS = 1
INPUT_RATE = 16000
INPUT_CHUNK = 1024

console = Console()
# Load Whisper model
stt = whisper.load_model("base.en")

class Assistant:
    def __init__(self):
        # Audio settings
        self.INPUT_FORMAT = pyaudio.paInt16  # Typical format for audio input
        self.INPUT_CHANNELS = 1              # Mono audio
        self.INPUT_RATE = 16000              # Sample rate in Hz
        self.INPUT_CHUNK = 1024              # Frames per buffer
        console.print("[blue]Initializing Assistant")
        console.print("[cyan]Assistant started! Press Ctrl+C to exit.")
        self.config = self.init_config()

        programIcon = pygame.image.load('assistant-2.png')

        self.clock = pygame.time.Clock()
        pygame.display.set_icon(programIcon)
        pygame.display.set_caption("Assistant")

        self.windowSurface = pygame.display.set_mode((WIDTH, HEIGHT), 0, 32)
        self.font = pygame.font.SysFont(None, FONT_SIZE)

        self.audio = pyaudio.PyAudio()

        self.tts = pyttsx3.init("nsss")
        self.tts.setProperty('rate', self.tts.getProperty('rate') - 20)

        try:
            self.audio.open(format=INPUT_FORMAT,
                            channels=INPUT_CHANNELS,
                            rate=INPUT_RATE,
                            input=True,
                            frames_per_buffer=INPUT_CHUNK).close()
        except Exception as e:
            logging.error(f"Error opening audio stream: {str(e)}")
            self.wait_exit()

        self.display_message(self.config.messages.loadingModel)
        self.model = whisper.load_model(self.config.whisperRecognition.modelPath)
        self.context = []

        #self.text_to_speech(self.config.conversation.greeting)
        time.sleep(0.5)
        self.display_message(self.config.messages.pressSpace)

    def wait_exit(self):
        while True:
            self.display_message(self.config.messages.noAudioInput)
            self.clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.locals.QUIT:
                    self.shutdown()

    def shutdown(self):
        logging.info("Shutting down Assistant")
        self.audio.terminate()
        pygame.quit()
        sys.exit()

    def init_config(self):
        logging.info("Initializing configuration")
        class Inst:
            pass

        with open('assistant.yaml', encoding='utf-8') as data:
            configYaml = yaml.safe_load(data)

        # Todo: check the Inst class
        config = Inst()
        config.messages = Inst()
        config.messages.loadingModel = configYaml["messages"]["loadingModel"]
        config.messages.pressSpace = configYaml["messages"]["pressSpace"]
        config.messages.noAudioInput = configYaml["messages"]["noAudioInput"]

        config.whisperRecognition = Inst()
        config.whisperRecognition.modelPath = configYaml["whisperRecognition"]["modelPath"]
        config.whisperRecognition.lang = configYaml["whisperRecognition"]["lang"]

        return config

    def wrap_text(self, text, font, max_width):
        """Wrap text to fit into a specific width."""
        lines = []
        words = text.split()
        while words:
            line = ''
            while words and font.size(line + words[0])[0] <= max_width:
                line += (words.pop(0) + " ")
            lines.append(line)
        return lines

    def display_text(self, text, font, text_color, start_y, center_x):
        """Render text line by line starting from a specific y-coordinate."""
        lines = self.wrap_text(text, font, WIDTH - 40)  # Adjust width for margins
        for line in lines:
            surface = font.render(line, True, text_color)
            rect = surface.get_rect(center=(center_x, start_y))
            self.windowSurface.blit(surface, rect)
            start_y += rect.height  # Move down the height of the text line
        return start_y  # Return new starting y coordinate after text

    def display_rec_start(self, transcript_text="", response_text=""):
        logging.info("Displaying recording start and texts")
        self.windowSurface.fill(BACK_COLOR)
        font = pygame.font.Font(None, FONT_SIZE)  # Using Pygame default font

        # Initial Y coordinate for the transcript text
        initial_y = 50  # Start drawing from this Y position

        # Display the transcript text
        final_y = self.display_text(transcript_text, font, TEXT_COLOR_YELLOW, initial_y, WIDTH // 2)

        # Display the response text slightly below the last line of transcript text
        self.display_text(response_text, font, TEXT_COLOR_CYAN, final_y + 20, WIDTH // 2)

        pygame.display.flip()

    def display_message(self, text):
        logging.info(f"Displaying message: {text}")
        self.windowSurface.fill(BACK_COLOR)

        label = self.font.render(text
                                 if (len(text)<MAX_TEXT_LEN_DISPLAY)
                                 else (text[0:MAX_TEXT_LEN_DISPLAY]+"..."),
                                 1,
                                 TEXT_COLOR)

        size = label.get_rect()[2:4]
        self.windowSurface.blit(label, (WIDTH/2 - size[0]/2, HEIGHT/2 - size[1]/2))

        pygame.display.flip()

    def text_to_speech(self, text):
        console.print(f"[cyan]Assistant: {text.strip()}")

        def play_speech():
            try:
                logging.info("Converting text to speech")
                self.tts.say(text)
                self.tts.runAndWait()
                logging.info("Speech playback completed")
            except Exception as e:
                logging.error(f"An error occurred during speech playback: {str(e)}")
        speech_thread = threading.Thread(target=play_speech)
        speech_thread.start()
        # Simulate sound wave as the assistant speaks
        #threading.Thread(target=self.simulate_speaking, args=(text,)).start()

    def display_sound_energy(self, energy):
        COL_COUNT = 5
        RED_CENTER = (255, 0, 0)
        MAX_AMPLITUDE = HEIGHT // 2  # Use half the window height as maximum amplitude

        # Apply a scaling factor directly, with an offset to manage smaller values
        if energy > 0:
            scaled_energy = 10 * (np.log10(energy + 1))  # Adding 1 to manage log(0) and increase scaling sensitivity
        else:
            scaled_energy = 0

        FACTOR = 10  # Adjust this factor based on the maximum log value expected to be around 2 to 3
        amplitude = max(1, min(int(scaled_energy * FACTOR), MAX_AMPLITUDE))

        self.windowSurface.fill(BACK_COLOR)
        hspace, vspace = 2 * KWIDTH, KHEIGHT
        base_y = HEIGHT // 2

        for i in range(-int(np.floor(COL_COUNT / 2)), int(np.ceil(COL_COUNT / 2))):
            x = WIDTH // 2 + i * hspace
            for j in range(amplitude):
                y_up = base_y - j * vspace
                y_down = base_y + j * vspace
                pygame.draw.rect(self.windowSurface, RED_CENTER, (x - KWIDTH // 2, y_up, KWIDTH, KHEIGHT))
                pygame.draw.rect(self.windowSurface, RED_CENTER, (x - KWIDTH // 2, y_down, KWIDTH, KHEIGHT))

        pygame.display.flip()

    def waveform_from_mic(self, key=pygame.K_SPACE) -> np.ndarray:
        logging.info("Capturing waveform from microphone")
        #self.display_rec_start()
        stream = self.audio.open(format=self.INPUT_FORMAT,
                                 channels=self.INPUT_CHANNELS,
                                 rate=self.INPUT_RATE,
                                 input=True,
                                 frames_per_buffer=self.INPUT_CHUNK)
        frames = []

        try:
            while True:
                pygame.event.pump()  # Ensure that Pygame handles events properly
                pressed = pygame.key.get_pressed()
                if pressed[key]:
                    data = stream.read(self.INPUT_CHUNK, exception_on_overflow=False)
                    frames.append(data)
                    # Calculate energy
                    np_data = np.frombuffer(data, dtype=np.int16).astype(np.float32)

                else:
                    break
        finally:
            stream.stop_stream()
            stream.close()

        return np.frombuffer(b''.join(frames), dtype=np.int16).astype(np.float32) * (1 / 32768.0)

    def simulate_speaking(self, response):
        """ Simulates sound wave output during speaking. """
        # Estimate speech duration based on text length
        duration = len(response) / 20  # Simple estimation: 20 characters per second
        start_time = time.time()

        while time.time() - start_time < duration:
            energy = random.uniform(0.1, 1.0)  # Randomly generate some energy levels
            self.display_sound_energy(energy)
            time.sleep(0.05)  # Update interval

        self.display_sound_energy(0)  # Reset display after speaking
