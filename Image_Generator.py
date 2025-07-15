from flask import Blueprint, render_template, request
import io, base64, requests, os
from dotenv import load_dotenv

load_dotenv()

prompt_to_image_bp = Blueprint('prompt_to_image', __name__)
CLIPDROP_API_KEY = os.getenv('AI_IMAGE_UPSCALER_API')

def generate_image_from_prompt(prompt):
    response = requests.post(
        'https://clipdrop-api.co/text-to-image/v1',
        files={
            'prompt': (None, prompt, 'text/plain')
        },
        headers={
            'x-api-key': CLIPDROP_API_KEY
        }
    )
    if response.ok:
        return response.content
    else:
        raise Exception(f"ClipDrop API Error: {response.status_code} - {response.text}")

def encode_image_to_base64(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')

@prompt_to_image_bp.route('/prompt-to-image', methods=['GET', 'POST'])
def prompt_to_image():
    result = None
    error = None
    if request.method == 'POST':
        prompt = request.form.get('prompt')
        if prompt:
            try:
                image_bytes = generate_image_from_prompt(prompt)
                result = {
                    'prompt': prompt,
                    'image': f"data:image/png;base64,{encode_image_to_base64(image_bytes)}",
                    'download_name': prompt.replace(' ', '_') + ".png"
                }
            except Exception as e:
                error = str(e)

    return render_template('prompt_to_image.html', result=result, error=error)
