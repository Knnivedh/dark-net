import os
import sys
import threading
import time
import json
import subprocess
try:
    if os.environ.get('CLOUD_MODE'):
        raise ImportError("Cloud Mode: Skipping Webview")
    import webview
except ImportError:
    webview = None
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import backend logic
from conversation_manager import ConversationManager
from providers.provider_manager import ProviderManager
try:
    if os.environ.get('CLOUD_MODE'):
        raise ImportError("Cloud Mode: Skipping GUI")
    from nivy_matrix_loader import show_matrix_loader
except ImportError:
    show_matrix_loader = None

# Audio imports
try:
    if os.environ.get('CLOUD_MODE'):
        raise ImportError("Cloud Mode: Skipping audio drivers")
    import sounddevice as sd
    import soundfile as sf
    import numpy as np
    import speech_recognition as sr
except ImportError:
    sd = None
    sf = None
    np = None
    sr = None
    print("Audio drivers not available (Cloud Mode or missing dependencies)")

import tempfile

# Setup Flask
if getattr(sys, 'frozen', False):
    static_folder = os.path.join(sys._MEIPASS, 'ui_build')
else:
    static_folder = os.path.join(os.getcwd(), 'ui_ux', 'build')

app = Flask(__name__, static_folder=static_folder, static_url_path='')
CORS(app)

from pathlib import Path

# Initialize Managers
conversation_manager = ConversationManager()
env_file = Path(__file__).parent / '.env'
provider_manager = ProviderManager(env_file)

@app.route('/')
def index():
    if os.path.exists(os.path.join(app.static_folder, 'index.html')):
        return send_from_directory(app.static_folder, 'index.html')
    else:
        return "<h1>UI Not Built</h1><p>Please run <code>npm install && npm run build</code> in the <code>ui_ux</code> directory.</p>"

@app.route('/api/check_setup', methods=['GET'])
def check_setup():
    provider = provider_manager.get_provider()
    provider_name = provider_manager.get_provider_name()
    
    # Force default to cerebras if not set but key exists
    if not provider and provider_name == 'groq':
        cerebras_key = os.getenv('CEREBRAS_API_KEY')
        if cerebras_key:
            print("Auto-switching to Cerebras as key is found")
            provider_manager.switch_provider('cerebras')
            provider = provider_manager.get_provider()
            provider_name = 'cerebras'

    if not provider:
        return jsonify({
            "setup_required": True,
            "provider_name": provider_name,
            "message": "Please configure your API key to start chatting"
        })
    
    return jsonify({
        "setup_required": False,
        "provider_name": provider_name
    })

@app.route('/api/setup', methods=['POST'])
def setup_api():
    data = request.json
    api_key = data.get('api_key')
    provider_name = data.get('provider', 'groq')
    
    if not api_key:
        return jsonify({"error": "API key is required"}), 400
    
    success = provider_manager.add_provider(provider_name, api_key.strip())
    if success:
        provider_manager.switch_provider(provider_name)
        return jsonify({"success": True, "message": "API key saved successfully"})
    else:
        return jsonify({"error": "Failed to save API key"}), 500

@app.route('/api/upload_resume', methods=['POST'])
def upload_resume():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        filename = file.filename.lower()
        text_content = ""
        
        if filename.endswith('.txt'):
            text_content = file.read().decode('utf-8', errors='ignore')
            
        elif filename.endswith('.pdf'):
            try:
                import PyPDF2
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text_content += page.extract_text() + "\n"
            except Exception as e:
                return jsonify({"error": f"PDF parsing failed: {str(e)}"}), 500
                
        elif filename.endswith('.docx'):
            try:
                import docx
                doc = docx.Document(file)
                for paragraph in doc.paragraphs:
                    text_content += paragraph.text + "\n"
            except Exception as e:
                return jsonify({"error": f"DOCX parsing failed: {str(e)}"}), 500
        else:
            return jsonify({"error": "Unsupported file type. Please use PDF, DOCX, or TXT"}), 400
        
        if not text_content.strip():
            return jsonify({"error": "No text could be extracted from the file"}), 400
            
        return jsonify({"success": True, "text": text_content.strip()})
        
    except Exception as e:
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get('message', '')
        conversation_history = data.get('messages', [])
        
        if not user_message:
            return jsonify({"error": "Message is required"}), 400
        
        provider = provider_manager.get_provider()
        
        if not provider:
            return jsonify({"setup_required": True, "response": "Please configure your API key in Settings."}), 200
        
        # Debug logging
        if hasattr(provider, 'api_key'):
            masked_key = provider.api_key[:4] + "..." + provider.api_key[-4:] if len(provider.api_key) > 8 else "INVALID"
            print(f"Using provider: {provider.name}, Key: {masked_key}")

        # Simplified System prompt
        system_prompt = {
            "role": "system",
            "content": "You are a helpful AI interview assistant. Format your responses professionally using markdown."
        }
        
        messages = [system_prompt]
        
        if conversation_history:
            # Filter out any messages with null content
            valid_history = [m for m in conversation_history if m.get('content')]
            messages.extend(valid_history)
        
        messages.append({"role": "user", "content": user_message})
        
        response = provider.chat(messages)
        return jsonify({"response": response})
    except Exception as e:
        error_msg = str(e)
        print(f"CHAT ERROR: {error_msg}") # Log to console
        
        # Return ACTUAL error to user for debugging
        return jsonify({"response": f"⚠️ **API Error:**\n\n{error_msg}\n\n(Please check console for details)"}), 200

@app.route('/api/ocr', methods=['POST'])
def ocr():
    try:
        cmd = [sys.executable]
        if not getattr(sys, 'frozen', False):
            cmd.append(os.path.abspath(__file__))
        cmd.append('--ocr')
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            try:
                stdout_lines = result.stdout.strip().split('\n')
                json_str = ""
                for line in reversed(stdout_lines):
                    if line.strip().startswith('{') and line.strip().endswith('}'):
                        json_str = line.strip()
                        break
                
                if not json_str:
                    json_str = result.stdout.strip()

                output = json.loads(json_str)
                return jsonify(output)
            except json.JSONDecodeError:
                clean_text = result.stdout.strip().replace("Tesseract not available", "")
                return jsonify({"text": clean_text, "method": "Raw Output"})
        else:
            return jsonify({"error": f"OCR process failed: {result.stderr}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Config persistence endpoints
CONFIG_FILE = "user_config.json"

@app.route('/api/config/save', methods=['POST'])
def save_config():
    try:
        data = request.json
        existing_config = {}
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                existing_config = json.load(f)
        
        existing_config.update(data)
        
        with open(CONFIG_FILE, 'w') as f:
            json.dump(existing_config, f)
            
        return jsonify({"status": "saved"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/config/load', methods=['GET'])
def load_config():
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
            return jsonify(config)
        return jsonify({})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Audio handler
class LiveAudioHandler:
    def __init__(self):
        self.recording_user = False
        self.recording_system = False
        self.user_data = []
        self.system_data = []
        self.sample_rate = 44100

    def start_user(self):
        if not sd: return # No audio driver
        self.recording_user = True
        self.user_data = []
        threading.Thread(target=self._record_user).start()

    def _record_user(self):
        try:
            if not sd: return
            with sd.InputStream(samplerate=self.sample_rate, channels=1, callback=self._user_callback):
                while self.recording_user:
                    sd.sleep(100)
        except Exception as e:
            self.recording_user = False

    def _user_callback(self, indata, frames, time, status):
        if self.recording_user:
            self.user_data.append(indata.copy())

    def stop_user(self):
        self.recording_user = False
        if not self.user_data: return ""
        return self._transcribe(self.user_data)

    def start_system(self):
        if not sd: return # No audio driver
        self.recording_system = True
        self.system_data = []
        threading.Thread(target=self._record_system).start()

    def _record_system(self):
        try:
            if not sd: return
            wasapi_info = next(h for h in sd.query_hostapis() if 'WASAPI' in h['name'])
            default_speakers = wasapi_info['default_output_device']
            
            with sd.InputStream(samplerate=self.sample_rate, device=default_speakers, channels=1, callback=self._system_callback, loopback=True):
                while self.recording_system:
                    sd.sleep(100)
        except Exception as e:
            self.recording_system = False

    def _system_callback(self, indata, frames, time, status):
        if self.recording_system:
            self.system_data.append(indata.copy())

    def stop_system(self):
        self.recording_system = False
        if not self.system_data: return ""
        return self._transcribe(self.system_data)

    def _transcribe(self, data_list):
        try:
            if not data_list or not np or not sf or not sr: return ""
            audio_data = np.concatenate(data_list, axis=0)
            
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                temp_path = f.name
            
            sf.write(temp_path, audio_data, self.sample_rate)
            
            r = sr.Recognizer()
            with sr.AudioFile(temp_path) as source:
                audio = r.record(source)
            
            try:
                text = r.recognize_google(audio)
            except sr.UnknownValueError:
                text = ""
            except Exception:
                text = ""
            
            try:
                os.remove(temp_path)
            except:
                pass
                
            return text
        except Exception:
            return ""

audio_handler = LiveAudioHandler()

@app.route('/api/record/user/start', methods=['POST'])
def start_user_record():
    audio_handler.start_user()
    return jsonify({"status": "started"})

@app.route('/api/record/user/stop', methods=['POST'])
def stop_user_record():
    text = audio_handler.stop_user()
    return jsonify({"text": text})

@app.route('/api/record/system/start', methods=['POST'])
def start_system_record():
    audio_handler.start_system()
    return jsonify({"status": "started"})

@app.route('/api/record/system/stop', methods=['POST'])
def stop_system_record():
    text = audio_handler.stop_system()
    return jsonify({"text": text})

def start_server():
    app.run(port=5000, threaded=True, use_reloader=False)

class WindowApi:
    def minimize_window(self):
        if len(webview.windows) > 0:
            webview.windows[0].minimize()

def start_webview():
    if not webview:
        print("Webview not available in Cloud Mode")
        return
        
    js_api = WindowApi()
    webview.create_window(
        'Nivya Dark Net', 
        'http://localhost:5000', 
        width=1200, 
        height=800,
        min_size=(100, 100),  # Ultra flexible sizing (100x100)
        resizable=True,
        background_color='#000000',
        frameless=False, # Enable native frame for resizing
        easy_drag=False,  # Only header is draggable
        on_top=True,
        js_api=js_api
    )
    webview.start()

def run_ocr_process():
    try:
        # Import directly from the package to avoid circular dependency issues if any
        from ocr.text_selector import InvisibleTextSelector
        from ocr.ocr_engine import OCREngine
        
        # Variable to store results from callback
        selection_result = {"coords": None}
        
        def on_select(coords):
            selection_result["coords"] = coords
            
        selector = InvisibleTextSelector(on_select)
        selector.start_selection()
        
        coords = selection_result["coords"]
        
        if not coords:
            print(json.dumps({"error": "No selection made"}))
            return
        
        try:
            # Use the selector instance to capture the screen
            image_bytes = selector.capture_screen_region(coords)
            
            if image_bytes:
                ocr_engine = OCREngine()
                text, method = ocr_engine.extract_text_from_image(image_bytes)
                print(json.dumps({"text": text, "method": method}))
            else:
                print(json.dumps({"error": "Failed to capture screen region"}))
        except Exception as e:
            print(json.dumps({"error": f"OCR Engine Error: {str(e)}"}))
            
    except Exception as e:
        print(json.dumps({"error": f"OCR Process Error: {str(e)}"}))

import logging
import traceback

# Setup logging
logging.basicConfig(filename='debug_log.txt', level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

def start_app():
    logging.info("Starting app...")
    print("Initializing Nivya Dark Net...")
    
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    logging.info("Server thread started")
    
    time.sleep(1.5)
    
    logging.info("Starting webview...")
    start_webview()
    logging.info("Webview closed")

def main():
    try:
        logging.info("Application started")
        if '--ocr' in sys.argv:
            run_ocr_process()
            return
        
        # Check for Cloud Mode
        if os.environ.get('CLOUD_MODE'):
            logging.info("Starting in Cloud Mode (Server Only)")
            start_server()
            return

        try:
            logging.info("Showing Matrix Loader...")
            # Run loader first, blocking until it finishes
            if show_matrix_loader:
                show_matrix_loader(None)
            logging.info("Matrix Loader finished")
        except Exception as e:
            logging.error(f"Loader failed: {e}")
            print(f"Loader failed: {e}")
        
        # Then start the main app
        start_app()
    except Exception as e:
        logging.critical(f"FATAL ERROR: {e}")
        logging.critical(traceback.format_exc())
        # In background mode, we cannot use input() as it causes EOFError
        # Just log and exit
        sys.exit(1)

if __name__ == '__main__':
    main()
