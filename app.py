from flask import Flask, request, jsonify
from google.cloud import storage
import google.generativeai as genai
import os
import json
import uuid

app = Flask(__name__)

# Load API key from environment variable
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is not set. Please set it as an environment variable.")

genai.configure(api_key=GEMINI_API_KEY)

# Initialize Cloud Storage
BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
storage_client = storage.Client()
bucket = storage_client.bucket(BUCKET_NAME)

def generate_caption(image_url):
    model = genai.GenerativeModel("gemini-pro-vision")
    response = model.generate_content(image_url)
    return response.text if response else "No caption generated."

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['image']
    filename = f"{uuid.uuid4()}.jpeg"
    blob = bucket.blob(filename)
    blob.upload_from_file(file, content_type=file.content_type)

    # Generate AI Caption
    public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"
    caption = generate_caption(public_url)

    metadata = {
        "title": caption.split('.')[0] if '.' in caption else caption,
        "description": caption
    }

    json_blob = bucket.blob(filename.replace(".jpeg", ".json"))
    json_blob.upload_from_string(json.dumps(metadata), content_type="application/json")

    return jsonify({
        "message": "Upload successful",
        "image_url": public_url,
        "metadata_url": json_blob.public_url
    })

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
