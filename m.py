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







# ####################################################################



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




# App.py main file code from flask import Flask, render_template, request
import io, base64
from PIL import Image
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

# Import Blueprints (make sure these exist)
from bg_remove import bg_remove_bp
from Image_Generator import prompt_to_image_bp

app.register_blueprint(bg_remove_bp)
app.register_blueprint(prompt_to_image_bp)


def upscale_image_dynamic(image_stream, user_scale):
    img = Image.open(image_stream).convert("RGB")

    # Input size in MB
    image_stream.seek(0, io.SEEK_END)
    original_size_bytes = image_stream.tell()
    image_stream.seek(0)
    original_size_mb = original_size_bytes / (1024 * 1024)

    # Target size: 2MB per 1x scale
    target_size_mb = user_scale * 2
    target_size_bytes = target_size_mb * 1024 * 1024

    # Initial upscale
    scale_factor = user_scale
    new_width = int(img.width * scale_factor)
    new_height = int(img.height * scale_factor)
    img = img.resize((new_width, new_height), Image.LANCZOS)

    output = io.BytesIO()
    img.save(output, format="PNG", compress_level=0, dpi=(600, 600))
    output.seek(0)

    max_dimension = 8192
    iterations = 0
    max_iterations = 5

    # Further upscale until target size or max dimension
    while output.getbuffer().nbytes < target_size_bytes and iterations < max_iterations:
        next_width = min(int(img.width * 1.4), max_dimension)
        next_height = min(int(img.height * 1.4), max_dimension)

        if next_width == img.width or next_height == img.height:
            break

        img = img.resize((next_width, next_height), Image.LANCZOS)
        output = io.BytesIO()
        img.save(output, format="PNG", compress_level=0, dpi=(600, 600))
        output.seek(0)
        iterations += 1

    # High-quality JPG version
    jpg_output = io.BytesIO()
    img.convert("RGB").save(
        jpg_output,
        format="JPEG",
        quality=100,
        optimize=True,
        progressive=True,
        dpi=(600, 600),
        subsampling=0
    )
    jpg_output.seek(0)

    return output, jpg_output


def encode_image_to_base64(image_bytes):
    return base64.b64encode(image_bytes.read()).decode('utf-8')


@app.route('/')
def index():
    return render_template('index.html', scale=4)


@app.route('/upload', methods=['POST'])
def upload():
    try:
        scale = int(request.form.get('scale', 4))
        if scale < 1:
            scale = 1
        elif scale > 20:
            scale = 20
    except Exception:
        scale = 4

    files = request.files.getlist('fileInput')
    results = []
    errors = []

    for file in files:
        if file.filename == '':
            continue

        try:
            original_bytes = io.BytesIO(file.read())
            original_bytes.seek(0)

            png_bytes, jpg_bytes = upscale_image_dynamic(original_bytes, scale)

            original_base64 = encode_image_to_base64(io.BytesIO(original_bytes.getvalue()))
            png_base64 = encode_image_to_base64(io.BytesIO(png_bytes.read()))
            jpg_base64 = encode_image_to_base64(io.BytesIO(jpg_bytes.read()))

            base_name = file.filename.rsplit('.', 1)[0]

            results.append({
                'original': f"data:image/png;base64,{original_base64}",
                'png': f"data:image/png;base64,{png_base64}",
                'jpg': f"data:image/jpeg;base64,{jpg_base64}",
                'png_download': f"{base_name}_{scale}x_highres.png",
                'jpg_download': f"{base_name}_{scale}x_highres.jpg"
            })
        except Exception as e:
            errors.append(f"{file.filename}: {str(e)}")

    return render_template('index.html', results=results, errors=errors, scale=scale)


if __name__ == '__main__':
    app.run(debug=True)


# 14/07/2025 Updated to include Freepik upscale code


from flask import Flask, render_template, request
import io, base64, requests, os
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Import Blueprints (ensure these files exist)
from bg_remove import bg_remove_bp
from Image_Generator import prompt_to_image_bp

app.register_blueprint(bg_remove_bp)
app.register_blueprint(prompt_to_image_bp)

FREEPIK_API_KEY = os.getenv("FREEPIK_API")

# Encode PIL image to base64 string
def encode_image_to_base64(image_bytes):
    return base64.b64encode(image_bytes.read()).decode('utf-8')


# Upscale image using local PIL processing
def upscale_image_dynamic(image_stream, user_scale):
    img = Image.open(image_stream).convert("RGB")

    # Original image size in MB
    image_stream.seek(0, io.SEEK_END)
    original_size_bytes = image_stream.tell()
    image_stream.seek(0)
    original_size_mb = original_size_bytes / (1024 * 1024)

    # Target size per scale factor
    target_size_mb = user_scale * 2
    target_size_bytes = target_size_mb * 1024 * 1024

    # Initial upscale
    scale_factor = user_scale
    new_width = int(img.width * scale_factor)
    new_height = int(img.height * scale_factor)
    img = img.resize((new_width, new_height), Image.LANCZOS)

    output = io.BytesIO()
    img.save(output, format="PNG", compress_level=0, dpi=(600, 600))
    output.seek(0)

    max_dimension = 8192
    iterations = 0
    max_iterations = 5

    while output.getbuffer().nbytes < target_size_bytes and iterations < max_iterations:
        next_width = min(int(img.width * 1.4), max_dimension)
        next_height = min(int(img.height * 1.4), max_dimension)

        if next_width == img.width or next_height == img.height:
            break

        img = img.resize((next_width, next_height), Image.LANCZOS)
        output = io.BytesIO()
        img.save(output, format="PNG", compress_level=0, dpi=(600, 600))
        output.seek(0)
        iterations += 1

    # Convert to high-quality JPG
    jpg_output = io.BytesIO()
    img.convert("RGB").save(
        jpg_output,
        format="JPEG",
        quality=100,
        optimize=True,
        progressive=True,
        dpi=(600, 600),
        subsampling=0
    )
    jpg_output.seek(0)

    return output, jpg_output


# Upscale image using Freepik API
def upscale_with_freepik_api(base64_image: str, prompt: str = None):
    try:
        url = "https://api.freepik.com/v1/ai/image-upscaler"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "x-freepik-api-key": FREEPIK_API_KEY
        }

        payload = {
            "image": base64_image,
            "scale_factor": "4x",
            "optimized_for": "films_n_photography",
            "creativity": -3,
            "hdr": 2,
            "resemblance": 3,
            "fractality": 3,
            "engine": "magnific_sparkle"
        }

        if prompt:
            payload["prompt"] = prompt

        response = requests.post(url, json=payload, headers=headers)
        result = response.json()

        if "output" in result:
            upscaled_base64 = result["output"]
            return upscaled_base64  # base64 encoded string
        else:
            raise Exception(result.get("message", "Freepik API failed"))

    except Exception as e:
        return str(e)


@app.route('/')
def index():
    return render_template('index.html', scale=4)


@app.route('/upload', methods=['POST'])
def upload():
    try:
        scale = int(request.form.get('scale', 4))
        if scale < 1:
            scale = 1
        elif scale > 20:
            scale = 20
    except Exception:
        scale = 4

    files = request.files.getlist('fileInput')
    results = []
    errors = []

    for file in files:
        if file.filename == '':
            continue

        try:
            original_bytes = io.BytesIO(file.read())
            original_bytes.seek(0)

            # Encode original image for Freepik
            original_base64 = encode_image_to_base64(io.BytesIO(original_bytes.getvalue()))

            # Call Freepik upscale API (you can toggle this logic with a checkbox later)
            freepik_upscaled_base64 = upscale_with_freepik_api(original_base64)

            # Fallback to local upscale
            png_bytes, jpg_bytes = upscale_image_dynamic(io.BytesIO(original_bytes.getvalue()), scale)

            png_base64 = encode_image_to_base64(io.BytesIO(png_bytes.read()))
            jpg_base64 = encode_image_to_base64(io.BytesIO(jpg_bytes.read()))

            base_name = file.filename.rsplit('.', 1)[0]

            results.append({
                'original': f"data:image/png;base64,{original_base64}",
                'png': f"data:image/png;base64,{png_base64}",
                'jpg': f"data:image/jpeg;base64,{jpg_base64}",
                'freepik': f"data:image/png;base64,{freepik_upscaled_base64}" if "data:image" not in freepik_upscaled_base64 else freepik_upscaled_base64,
                'png_download': f"{base_name}_{scale}x_local.png",
                'jpg_download': f"{base_name}_{scale}x_local.jpg",
                'freepik_download': f"{base_name}_freepik_upscaled.png"
            })
        except Exception as e:
            errors.append(f"{file.filename}: {str(e)}")

    return render_template('index.html', results=results, errors=errors, scale=scale)


if __name__ == '__main__':
    app.run(debug=True)






