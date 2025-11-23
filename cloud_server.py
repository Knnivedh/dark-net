import os
import sys

# Set cloud mode flag
os.environ['CLOUD_MODE'] = 'true'

# Set cloud mode flag
os.environ['CLOUD_MODE'] = 'true'

from ui_bridge import app
from flask import request, jsonify
import base64
import io

# Initialize OCR Engine lazily
ocr_engine = None

@app.route('/api/ocr_remote', methods=['POST'])
def ocr_remote():
    global ocr_engine
    try:
        if 'image' not in request.files:
            return jsonify({"error": "No image provided"}), 400
            
        file = request.files['image']
        image_bytes = file.read()
        
        if not ocr_engine:
            print("Loading Cloud OCR Engine...")
            from ocr.ocr_engine import OCREngine
            ocr_engine = OCREngine()
            
        text, method = ocr_engine.extract_text_from_image(image_bytes)
        return jsonify({"text": text, "method": f"Cloud {method}"})
        
    except Exception as e:
        print(f"Cloud OCR Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Run with Gunicorn/Waitress in production, but for now standard run
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
