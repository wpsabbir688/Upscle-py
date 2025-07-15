from flask import Blueprint, render_template, request
from google import genai
from werkzeug.utils import secure_filename

seo_gen_bp = Blueprint('seo_gen_bp', __name__, url_prefix='/seo-gen')

def get_genai_client(api_key):
    return genai.Client(api_key=api_key)

@seo_gen_bp.route('/', methods=['GET', 'POST'])
def seo_gen():
    errors = []
    results = []
    all_seo = []
    api_key = ""

    if request.method == 'POST':
        api_key = request.form.get('api_key', '').strip()
        files = request.files.getlist('fileInput')

        if not api_key:
            errors.append("API key is required.")
        if not files or files[0].filename == '':
            errors.append("Please upload at least one image.")

        if not errors:
            try:
                client = get_genai_client(api_key)

                for file in files:
                    filename = secure_filename(file.filename)
                    prompt = (
                        f"Generate an SEO-friendly title and keywords for an image named '{filename}'. "
                        "Provide output as:\nTitle: <title>\nKeywords: <comma separated keywords>"
                    )

                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=prompt,
                    )

                    generated_text = response.text.strip()
                    results.append({'filename': filename, 'generated_text': generated_text})

            except Exception as e:
                errors.append(f"Error calling Google Gemini API: {str(e)}")

    # TODO: লোড পূর্বে সেভ করা ডেটা DB থেকে, যদি থাকে
    return render_template("seo_gen.html", results=results, errors=errors, all_seo=all_seo, api_key=api_key)
