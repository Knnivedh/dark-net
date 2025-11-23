import requests
from .base_provider import BaseProvider

class CerebrasProvider(BaseProvider):
    def __init__(self, api_key):
        super().__init__(api_key)
        self.name = "cerebras"
        self.api_url = "https://api.cerebras.ai/v1/chat/completions"

    def chat(self, messages):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "llama3.1-8b",
            "messages": messages,
            "temperature": 0.7
        }
        try:
            response = requests.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            return f"Error: {str(e)}"
