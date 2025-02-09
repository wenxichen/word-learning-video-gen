import json
import requests
import sys
from dotenv import load_dotenv
import os
from io import BytesIO
from typing import Dict, List
from PIL import Image
from pptx import Presentation
from pptx.util import Inches, Pt
import subprocess
from pydub import AudioSegment
from moviepy.editor import ImageClip, AudioFileClip
import logging

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

output_dir = os.getcwd() + "/output/"

# Anthropic
import anthropic
anthropic_client = anthropic.Anthropic()

# OpenAI
import openai
openai_client = openai.OpenAI()


def generate_word_info(word: str) -> Dict[str, str]:
    """
    Generate a word's definition and example sentence from a given word.

    Args:
        word (str): The word to generate information for.

    Returns:
        dict: A dictionary containing the word's definition and example sentence under the keys 'definition' and 'example'.
    """
    system_message: str = "You are a kintergarden teacher. You are given a word and you need to explain it in a way that is easy to understand."
    user_message: str = (f"Can you explain the word {word} in a way that is easy to understand for a 5 year old? "
                f"Please respond in JSON format with the following two fields: 'definition' and 'example'. "
                f"The definition should be no more than a couple of sentences explaining the most common definition(s) of the word. "
                f"The example should be a sentence that uses the word in a way that is easy to understand for a 5 year old. "
                f"Start the example sentence with something like 'For example, ...', 'Here is an example: ...', or 'An example would be ...'.")
    
    message: anthropic.Message = anthropic_client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        temperature=0,
        system=system_message,
        messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": user_message
                }
            ]
            }
        ]
    )

    word_info: Dict[str, str] = json.loads(message.content[0].text)
    word_info["word"] = word

    return word_info

def generate_image_from_word_info(word_info: Dict[str, str]) -> BytesIO:
    """
    Generate an image from a given word's definition and example sentence.

    Args:
        word_info (Dict[str, str]): A dictionary containing the word's definition and example sentence under the keys 'definition' and 'example'.

    Returns:
        BytesIO: A BytesIO object containing the generated image.
    """
    image_prompt = (
        f"Please make a picture of the word \"{word_info['word']}\", so a 5 year old can understand what the word means. "
        f"The definition of the word is: \"{word_info['definition']}\". "
        f"The example of the word is: \"{word_info['example']}\"."
    )

    response = openai_client.images.generate(
        model="dall-e-3",
        prompt=image_prompt,
        size="1024x1024",
        quality="standard",
        n=1,
        # response_format="b64_json",
    )

    image_url_response = requests.get(response.data[0].url)
    image_data = BytesIO(image_url_response.content)

    return image_data

def generate_slide(word_info: Dict[str, str], image_data: BytesIO) -> str:
    """
    Generate a slide from a given word info and image data.

    Args:
        word_info (Dict[str, str]): A dictionary containing the word's definition and example sentence under the keys 'definition' and 'example'.
        image_data (BytesIO): A BytesIO object containing the generated image.

    Returns:
        str: The path to the generated slide.
    """
    prs = Presentation()
    title_slide_layout = prs.slide_layouts[0]
    slide = prs.slides.add_slide(title_slide_layout)

    # set title
    title = slide.shapes.title
    title.top = Inches(0.5)
    title.left = Inches(1)
    title.height = Inches(1)
    title.width = Inches(8)
    title.text = word_info["word"]

    # add image to slide
    pic = slide.shapes.add_picture(image_data, left=Inches(1), top=Inches(1.5), width=Inches(5), height=Inches(5))

    # Add word definition
    txBox = slide.shapes.add_textbox(left=Inches(6), top=Inches(1.5), width=Inches(4), height=Inches(2.5))
    tf = txBox.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.font.size = Pt(22)
    p.text = word_info["definition"]

    # Add word example
    txBox = slide.shapes.add_textbox(left=Inches(6), top=Inches(4), width=Inches(4), height=Inches(2.5))
    tf = txBox.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.font.size = Pt(22)
    p.text = word_info["example"]

    # save pptx file
    output_file_path = output_dir + 'temp.pptx'
    prs.save(output_file_path)

    return output_file_path

def convert_slide_to_image(slide_path: str) -> str:
    """
    Convert a PowerPoint slide to an image.

    Args:
        slide_path (str): The path to the PowerPoint slide.

    Returns:
        str: The path to the generated image.
    """
    pdf_path = os.path.join(output_dir, "temp.pdf")

    # Convert PPTX to PDF using LibreOffice
    subprocess.run(["/Applications/LibreOffice.app/Contents/MacOS/soffice", "--headless", "--convert-to", "pdf", slide_path, "--outdir", output_dir], check=True)

    # Convert PDF to PNG images using pdftoppm (part of poppler-utils)
    subprocess.run(["pdftoppm", "-png", "-singlefile", pdf_path, os.path.join(output_dir, "temp")], check=True)

    os.remove(pdf_path)

    return os.path.join(output_dir, "temp.png")


def combine_mp3s(file_paths: List[str], output_path: str, pause_duration: int = 2000) -> str:
    """Combines multiple MP3 files into one.

    Args:
        file_paths (List[str]): A list of file paths to the MP3 files to combine.
        output_path (str): The file path to save the combined MP3 file.
        pause_duration (int): The duration of the pause between the audio files.

    Returns:
        str: The path to the generated audio file.
    """
    pause = AudioSegment.silent(duration=pause_duration)
    combined_audio = AudioSegment.empty()
    for i, file_path in enumerate(file_paths):
        audio = AudioSegment.from_mp3(file_path)
        combined_audio += audio
        if i < len(file_paths) - 1:  # Add pause except after the last file
            combined_audio += pause
    combined_audio.export(output_path, format="mp3")


def generate_audio_file(word_info: Dict[str, str]) -> str:
    """
    Generate a audio file for a given word info.

    Args:
        word_info (Dict[str, str]): A dictionary containing the word's definition and example sentence under the keys 'definition' and 'example'.

    Returns:
        str: The path to the generated audio file.
    """
    word_speech_file_path = output_dir + "word_speech.mp3"  
    with openai_client.audio.speech.with_streaming_response.create(
        model="tts-1",
        voice="shimmer",
        input= "The word is \"" + word_info["word"] + "\" ...",
    ) as response:
        response.stream_to_file(word_speech_file_path)

    word_definition_speech_file_path = output_dir + "word_definition_speech.mp3"    
    with openai_client.audio.speech.with_streaming_response.create(
        model="tts-1",
        voice="shimmer",
        input= word_info["definition"],
    ) as response:
        response.stream_to_file(word_definition_speech_file_path)

    word_example_speech_file_path = output_dir + "word_example_speech.mp3"
    with openai_client.audio.speech.with_streaming_response.create(
        model="tts-1",
        voice="nova",
        input= word_info["example"],
    ) as response:
        response.stream_to_file(word_example_speech_file_path)

    file_paths = [word_speech_file_path, word_definition_speech_file_path, word_example_speech_file_path]
    output_path = output_dir + "combined_audio.mp3"
    combine_mp3s(file_paths, output_path)

    return output_path


def generate_video_file(image_path: str, audio_path: str, output_path: str) -> str:
    """
    Generate a video file from a given image and audio file.

    Args:
        image_path (str): The path to the image file.
        audio_path (str): The path to the audio file.
        output_path (str): The path to save the generated video file.        
    """
    audio_clip = AudioFileClip(audio_path)
    image_clip = ImageClip(image_path).set_duration(audio_clip.duration)
    
    video_clip = image_clip.set_audio(audio_clip)
    video_clip.write_videofile(output_path, fps=24)

if __name__ == "__main__":
    logging.info("Starting video generation process...")
    
    logging.info("Generating word information...")
    word_info = generate_word_info("apple")
    logging.info(f"Generated word info for '{word_info['word']}'")
    
    logging.info("Generating image from word info...")
    image_data = generate_image_from_word_info(word_info)
    logging.info("Image generated successfully")
    
    logging.info("Creating PowerPoint slide...")
    slide_path = generate_slide(word_info, image_data)
    logging.info(f"Slide created at {slide_path}")
    
    logging.info("Converting slide to image...")
    image_path = convert_slide_to_image(slide_path)
    logging.info(f"Slide converted to image at {image_path}")
    
    logging.info("Generating audio file...")
    audio_path = generate_audio_file(word_info)
    logging.info(f"Audio generated at {audio_path}")
    
    logging.info("Creating final video...")
    video_path = output_dir + "video.mp4"
    generate_video_file(image_path, audio_path, video_path)
    logging.info(f"Video created successfully at {video_path}")
    
    logging.info("Process completed!")