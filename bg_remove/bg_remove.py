from flask import Blueprint, render_template, request
import io, base64, requests, os, mimetypes
from PIL import Image
from dotenv import load_dotenv

load_dotenv()
bg_remove_bp = Blueprint('bg_remove', __name__, template_folder='templates')
REMOVE_BG_API_KEY = os.getenv('REMOVE_BG_API')

def remove_bg_with_api(image_stream, filename):
    content_type = mimetypes.guess_type(filename)[0] or 'image/png'
    response = requests.post(
        'https://api.remove.bg/v1.0/removebg',
        files={'image_file': ('image', image_stream, content_type)},
        data={'size': 'auto'},
        headers={'X-Api-Key': REMOVE_BG_API_KEY},
    )
    if response.status_code == 200:
        return response.content
    else:
        raise Exception(f"Remove.bg API Error: {response.status_code} - {response.text}")

def upscale_and_save_hq_image(image_bytes, upscale_factor=2, max_size_mb=5):
    img = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    new_size = (img.width * upscale_factor, img.height * upscale_factor)
    img = img.resize(new_size, Image.LANCZOS)

    output = io.BytesIO()
    img.save(output, format="PNG", compress_level=0)
    output.seek(0)

    max_dimension = 4096
    iterations = 0
    max_iterations = 2

    while output.getbuffer().nbytes < max_size_mb * 1024 * 1024 and iterations < max_iterations:
        new_width = min(img.width * 2, max_dimension)
        new_height = min(img.height * 2, max_dimension)
        if new_width == img.width or new_height == img.height:
            break
        img = img.resize((new_width, new_height), Image.LANCZOS)
        output = io.BytesIO()
        img.save(output, format="PNG", compress_level=0)
        output.seek(0)
        iterations += 1

    return output

def encode_image_to_base64(image_bytes):
    return base64.b64encode(image_bytes.read()).decode('utf-8')

@bg_remove_bp.route('/bg-remove', methods=['GET', 'POST'])
def bg_remove():
    result = None
    error = None
    if request.method == 'POST':
        file = request.files.get('fileInput')
        if file and file.filename != '':
            try:
                original_bytes = io.BytesIO(file.read())
                original_bytes.seek(0)

                removed_raw = remove_bg_with_api(original_bytes, file.filename)
                hq_output = upscale_and_save_hq_image(removed_raw)
                hq_output.seek(0)

                result = {
                    'original': encode_image_to_base64(io.BytesIO(original_bytes.getvalue())),
                    'removed': encode_image_to_base64(io.BytesIO(hq_output.read())),
                    'download_name': file.filename.rsplit('.', 1)[0] + "_nobg_HQ.png"
                }

            except Exception as e:
                error = str(e)

    return render_template('bg_remove.html', result=result, error=error)
