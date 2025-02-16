import torch
from diffusers import FluxPipeline
from PIL import Image
from io import BytesIO

pipe = FluxPipeline.from_pretrained("black-forest-labs/FLUX.1-dev", torch_dtype=torch.bfloat16)
pipe.enable_model_cpu_offload() #save some VRAM by offloading the model to CPU. Remove this if you have enough GPU power

def generate_image(prompt: str, output_path: str=None) -> None | BytesIO:
    """
    Generate an image from a given prompt using the Flux.1-dev model.
    
    Args:
        prompt (str): The prompt to generate the image from.
        output_path (str, optional): The path to save the generated image to. Defaults to None.

    Returns:
        None | BytesIO: If output_path is not provided, the generated image as a byte array.
    """
    image = pipe(
        prompt,
        height=512,
        width=512,
        guidance_scale=3.5,
        num_inference_steps=50,
        max_sequence_length=512,
        generator=torch.Generator("cpu").manual_seed(0)
    ).images[0]
    if output_path:
        image.save(output_path)
    else:
        # convert PIL image to byte array
        image_byte_array = BytesIO()
        image.save(image_byte_array, format="PNG")
        image_byte_array.seek(0)
        return image_byte_array


if __name__ == "__main__":
    image = generate_image("Create an illustration that vividly captures the concept of 'abandon' in a way that resonates with a 5-year-old child. Envision a serene park setting, where the gentle rustling of leaves and the soft chirping of birds create a peaceful atmosphere. In the foreground, place a small, sad puppy sitting alone beside an empty wooden bench. The puppy's eyes are large and expressive, filled with a sense of longing and sadness, as if it is patiently waiting for an owner who is nowhere to be found. Its fur is slightly ruffled, and its posture is slumped, emphasizing its loneliness and abandonment. In stark contrast, the background of the scene is filled with vibrant life and joy. A loving family is depicted, consisting of a Middle-Eastern mother with a warm smile, a Black father with a gentle demeanor, and their children, a delightful mix of Hispanic and South Asian heritage. The children are laughing and playing energetically with a puppy that looks identical to the one by the bench, suggesting they are siblings. This family exudes warmth, unity, and care, embodying the love and companionship that the lonely puppy yearns for. The scene is bathed in soft, golden sunlight, enhancing the contrast between the solitary puppy and the joyful family, and highlighting the emotional depth of the concept of 'abandon' through the juxtaposition of loneliness and togetherness.", output_path="flux-dev-expanded.png")
