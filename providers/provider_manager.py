import os
from dotenv import load_dotenv
from .groq_provider import GroqProvider
from .cerebras_provider import CerebrasProvider
from .remote_provider import RemoteProvider

class ProviderManager:
    def __init__(self, env_file):
        load_dotenv(env_file)
        self.providers = {}
        self.current_provider = None
        self.load_providers()

    def load_providers(self):
        # Check for Remote Mode first
        remote_url = os.getenv('REMOTE_SERVER_URL')
        if remote_url:
            print(f"Initializing Remote Provider with URL: {remote_url}")
            self.providers['remote'] = RemoteProvider(remote_url)
            self.current_provider = self.providers['remote']
            return

        # Fallback to local providers
        groq_key = os.getenv('GROQ_API_KEY')
        cerebras_key = os.getenv('CEREBRAS_API_KEY')
        
        if groq_key:
            self.providers['groq'] = GroqProvider(groq_key)
        if cerebras_key:
            self.providers['cerebras'] = CerebrasProvider(cerebras_key)
            
        current = os.getenv('CURRENT_PROVIDER', 'groq')
        if current in self.providers:
            self.current_provider = self.providers[current]
        elif self.providers:
            self.current_provider = list(self.providers.values())[0]

    def get_provider(self):
        return self.current_provider

    def get_provider_name(self):
        return self.current_provider.name if self.current_provider else None

    def switch_provider(self, name):
        if name in self.providers:
            self.current_provider = self.providers[name]
            return True
        return False

    def add_provider(self, name, api_key):
        if name == 'groq':
            self.providers['groq'] = GroqProvider(api_key)
        elif name == 'cerebras':
            self.providers['cerebras'] = CerebrasProvider(api_key)
        elif name == 'remote':
            self.providers['remote'] = RemoteProvider(api_key) # api_key here acts as URL
        else:
            return False
        return True
