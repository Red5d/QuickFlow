from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import requests
import os
import base64
from io import BytesIO

app = Flask(__name__)

# Configure upload folder and allowed extensions
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Retrieve OpenRouter API key and model name from environment variables
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
OPENROUTER_MODEL = os.getenv('OPENROUTER_MODEL')

# Serve the index.html file
@app.route('/')
def serve_index():
    return send_from_directory(os.path.dirname(__file__), 'index.html')

@app.route('/tools.json')
def serve_tools():
    return send_from_directory(os.path.dirname(__file__), 'tools.json')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Handle API requests to /process
@app.route('/process', methods=['POST'])
def process_request():
    try:
        # Extract data from the incoming request
        data = request.form
        prompt = data.get('prompt')
        print(f"Received prompt: {prompt}")
        structured = data.get('structured', False)

        if not prompt and not 'image' in request.files:
            return jsonify({'error': 'Prompt is required if no image is provided'}), 400

        # Send the request to OpenRouter
        openrouter_url = 'https://openrouter.ai/api/v1/chat/completions'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {OPENROUTER_API_KEY}"  # Use stored API key
        }
        payload = {
            'model': OPENROUTER_MODEL,  # Use stored model name
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
        }

        # Check if the post request has the file part
        if 'image' in request.files:
            image = request.files['image']
            if image and allowed_file(image.filename):
                # Read the image file and encode it as a base64 data URL
                image_data = image.read()
                image_base64 = base64.b64encode(image_data).decode('utf-8')
                    # with open('b64.txt', 'w') as f:
                    #     f.write(image_base64)
                image_data_url = f"data:image/jpeg;base64,{image_base64}"
                payload['messages'] = [
                    {"role": "user", "content": [
                        {"type": "text", "text": prompt.replace('text', 'image')},
                        {"type": "image_url", "image_url": {"url": image_data_url}}
                    ]}
                ]
                # print(f"Image data URL: {image_data_url[:100]}...")
    
        print(f"Payload sent to OpenRouter: {str(payload)[0:500]}")
        response = requests.post(openrouter_url, json=payload, headers=headers)
        print(f"Response from OpenRouter: {response.status_code} - {response.text}")
        if response.status_code != 200:
            return jsonify({'error': 'Failed to process request with OpenRouter'}), response.status_code

        # Return the response from OpenRouter
        return jsonify(response.json()), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)  # Enable debug mode for development