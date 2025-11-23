import json
import os
from datetime import datetime

class ConversationManager:
    def __init__(self, storage_file='conversation_history.json'):
        self.storage_file = storage_file
        self.history = []
        self.load_history()

    def load_history(self):
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r') as f:
                    self.history = json.load(f)
            except Exception:
                self.history = []

    def save_history(self):
        try:
            with open(self.storage_file, 'w') as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            print(f"Error saving history: {e}")

    def add_message(self, role, content):
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        self.history.append(message)
        self.save_history()
        return message

    def get_history(self):
        return self.history

    def clear_history(self):
        self.history = []
        self.save_history()
