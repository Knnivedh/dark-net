import requests
import json
from .base_provider import BaseProvider

class RemoteProvider(BaseProvider):
    def __init__(self, api_url):
        # API URL should be the base URL of the cloud server
        self.api_url = api_url.rstrip('/') + "/api/chat"
        self.name = "remote"

    def chat(self, messages):
        headers = {
            "Content-Type": "application/json"
        }
        # We send the messages directly. The cloud server handles the API keys.
        data = {
            "messages": messages,
            "message": messages[-1]['content'] if messages else "" 
        }
        
        try:
            print(f"Sending request to {self.api_url}")
            response = requests.post(self.api_url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            # The cloud server returns {"response": "AI response"}
            result = response.json()
            return result.get('response', "Error: Empty response from server")
            
        except requests.exceptions.RequestException as e:
            return f"Error connecting to cloud server: {str(e)}"
        except Exception as e:
            return f"Error: {str(e)}"
