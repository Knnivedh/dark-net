import requests
from .base_provider import BaseProvider

class GroqProvider(BaseProvider):
    def __init__(self, api_key):
        super().__init__(api_key)
        self.name = "groq"
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"

    def chat(self, messages):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "llama3-8b-8192",
            "messages": messages,
            "temperature": 0.7
        }
        try:
            response = requests.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            return f"Error: {str(e)}"
