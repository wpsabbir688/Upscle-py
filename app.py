from flask import Flask, render_template, request, session, redirect, url_for
import io, base64, os
from PIL import Image
from dotenv import load_dotenv
from datetime import datetime, timedelta

# ইউটিলিটি ফাংশন
from utils import init_db, create_access_key, validate_access_key, log_user_activity

# ESRGAN মডেল (High Quality Upscale)
import RRDBNet_arch as arch
import torch

# .env লোড
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "your_secret_key_here")

# ===== Register Blueprints =====
from bg_remove import bg_remove_bp
from Image_Generator import prompt_to_image_bp
from transaction import transaction_bp
from seo_gen import seo_gen_bp

app.register_blueprint(bg_remove_bp)
app.register_blueprint(prompt_to_image_bp)
app.register_blueprint(transaction_bp)
app.register_blueprint(seo_gen_bp)

# ===== Config =====
MAX_FREE_UPSCALES = 20
ip_usage = {}

# DB ইনিশিয়ালাইজ
init_db()

# ===== Helper Functions =====
def get_client_ip():
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0]
    return request.remote_addr

def encode_image_to_base64(image_bytes):
    return base64.b64encode(image_bytes.read()).decode('utf-8')

def upscale_image_dynamic(image_stream, user_scale):
    img = Image.open(image_stream).convert("RGB")
    width, height = img.size
    new_width, new_height = width * user_scale, height * user_scale

    if new_width > 10000 or new_height > 10000:
        raise ValueError("Image too large after upscaling. Please choose a smaller scale.")

    upscaled = img.resize((new_width, new_height), Image.LANCZOS)

    png_output = io.BytesIO()
    upscaled.save(png_output, format="PNG", optimize=True, compress_level=0)
    png_output.seek(0)

    jpg_output = io.BytesIO()
    upscaled.save(jpg_output, format="JPEG", quality=100, subsampling=0, optimize=True)
    jpg_output.seek(0)

    return png_output, jpg_output

def is_unlocked():
    if session.get('unlocked'):
        access_expiry = session.get("access_expiry")
        if access_expiry:
            expiry_date = datetime.strptime(access_expiry, "%Y-%m-%d")
            if datetime.utcnow() <= expiry_date:
                return True
            else:
                session.pop("unlocked", None)
                session.pop("access_expiry", None)
    return False

# ===== Routes =====
@app.route('/')
def index():
    client_ip = get_client_ip()
    session['client_ip'] = client_ip
    upscale_count = ip_usage.get(client_ip, 0)

    unlocked = is_unlocked()
    locked = not unlocked and upscale_count >= MAX_FREE_UPSCALES
    return render_template('index.html', scale=4, locked=locked)

@app.route('/upload', methods=['POST'])
def upload():
    scale = int(request.form.get('scale', 4))
    scale = min(max(scale, 1), 20)

    client_ip = session.get('client_ip', get_client_ip())
    upscale_count = ip_usage.get(client_ip, 0)

    unlocked = is_unlocked()

    if not unlocked and upscale_count >= MAX_FREE_UPSCALES:
        return render_template('index.html', scale=scale, locked=True)

    files = request.files.getlist('fileInput')
    results, errors = [], []

    for file in files:
        if file.filename == '':
            continue
        try:
            original_bytes = io.BytesIO(file.read())
            original_bytes.seek(0)

            original_base64 = encode_image_to_base64(io.BytesIO(original_bytes.getvalue()))

            png_bytes, jpg_bytes = upscale_image_dynamic(io.BytesIO(original_bytes.getvalue()), scale)
            png_base64 = encode_image_to_base64(io.BytesIO(png_bytes.read()))
            jpg_base64 = encode_image_to_base64(io.BytesIO(jpg_bytes.read()))

            base_name = file.filename.rsplit('.', 1)[0]

            results.append({
                'original': f"data:image/png;base64,{original_base64}",
                'png': f"data:image/png;base64,{png_base64}",
                'jpg': f"data:image/jpeg;base64,{jpg_base64}",
                'png_download': f"{base_name}_{scale}x_local.png",
                'jpg_download': f"{base_name}_{scale}x_local.jpg"
            })

            log_user_activity(client_ip)
            if not unlocked:
                ip_usage[client_ip] = ip_usage.get(client_ip, 0) + 1

        except Exception as e:
            errors.append(f"{file.filename}: {str(e)}")

    upscale_count = ip_usage.get(client_ip, 0)
    locked = not unlocked and upscale_count >= MAX_FREE_UPSCALES
    return render_template('index.html', results=results, errors=errors, scale=scale, locked=locked)

@app.route('/verify', methods=['POST'])
def verify_password():
    entered_password = request.form.get("password", "").strip()
    days_valid = validate_access_key(entered_password)
    if days_valid:
        session['unlocked'] = True
        expiry_date = datetime.utcnow() + timedelta(days=days_valid)
        session['access_expiry'] = expiry_date.strftime("%Y-%m-%d")
    else:
        session['unlocked'] = False
        session.pop('access_expiry', None)
    return redirect(url_for('index'))

@app.route('/adminptb', methods=['GET', 'POST'])
def admin():
    generated_key = None
    if request.method == 'POST':
        duration = int(request.form['duration'])
        generated_key = create_access_key(duration)
    return render_template('adminptb.html', generated_key=generated_key)

# ===== Run App =====
if __name__ == '__main__':
    app.run(debug=True)
