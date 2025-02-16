# word-learning-video-gen
Generator of videos that teach kindergartener and first grader common words.

## Setup

```bash
pip install -r requirements.txt
```

Install LibreOffice, poppler and ffmpeg for your OS if they are not installed.

## Usage

Put your API keys in the `.env` file. List the words you want to generate videos for in the `materials/` folder.

```bash
python main.py
```

## Output

The combined videos are saved in the `output/` folder and individual videos are saved in the `cache/` folder.
Currently, the script generates definition and example for each word using Anthropic Claude API.
Then it uses dall-e to generate an image for the word based on the definition and example.
After that, a slide is created for the word with the generated information.
The script then combines the slide and the image into a video.
Finally, the videos are grouped together into serveral longer videos.


## Future work

- [ ] minimize the cost of LLM calls, especially for image generation. We can use cheaper alternatives for dall-e or local models. Alternatively, we can search for images on the internet.
- [ ] make better command line interface for the script.
- [ ] add more smooth support for different OS.