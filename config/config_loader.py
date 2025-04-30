import os
from dotenv import load_dotenv
from typing import Dict

class ConfigLoader:
    def __init__(self):
        load_dotenv()
        self.required_vars = [
            'API_KEY',
            'CLIENT_CODE',
            'PIN',
            'TOTP_SECRET',
            'SECRET_KEY'
        ]
        
    def load_config(self) -> Dict[str, str]:
        """Load and validate all required environment variables."""
        config = {}
        missing_vars = []
        
        for var in self.required_vars:
            value = os.getenv(var)
            if value is None:
                missing_vars.append(var)
            else:
                config[var] = value
                
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
            
        return config 