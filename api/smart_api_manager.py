import pyotp
import time
from typing import Dict, Optional
from SmartApi import SmartConnect
from datetime import datetime, timedelta

class SmartAPIConnectionError(Exception):
    """Custom exception for SmartAPI connection issues."""
    pass

class SmartAPIManager:
    def __init__(self, config: Dict[str, str]):
        self.config = config
        self.api = None
        self.session_expiry = None
        self.max_retries = 3
        self.retry_delay = 5  # seconds
        self.refresh_token = None
        
    def generate_totp(self) -> str:
        """Generate TOTP using the secret key."""
        totp = pyotp.TOTP(self.config['TOTP_SECRET'])
        return totp.now()
    
    def login(self) -> bool:
        """Attempt to login to SmartAPI with retry mechanism."""
        for attempt in range(self.max_retries):
            try:
                if self.api is None:
                    self.api = SmartConnect(api_key=self.config['API_KEY'])
                
                totp = self.generate_totp()
                login_data = self.api.generateSession(
                    self.config['CLIENT_CODE'],
                    self.config['PIN'],
                    totp
                )
                
                if login_data.get('status'):
                    self.session_expiry = datetime.now() + timedelta(minutes=30)
                    self.refresh_token = login_data.get('data', {}).get('refreshToken')
                    print(f"Login successful. Session expires at: {self.session_expiry}")
                    return True
                else:
                    print(f"Login failed: {login_data.get('message')}")
                    
            except Exception as e:
                print(f"Login attempt {attempt + 1} failed: {str(e)}")
                
            if attempt < self.max_retries - 1:
                print(f"Retrying in {self.retry_delay} seconds...")
                time.sleep(self.retry_delay)
                
        raise SmartAPIConnectionError("Failed to establish connection after maximum retries")
    
    def check_session(self) -> bool:
        """Check if the current session is valid and refresh if needed."""
        if self.api is None or self.session_expiry is None:
            return self.login()
            
        if datetime.now() >= self.session_expiry:
            print("Session expired. Refreshing...")
            return self.login()
            
        return True
    
    def get_profile(self) -> Dict:
        """Get user profile with session validation."""
        if not self.check_session():
            raise SmartAPIConnectionError("Failed to establish valid session")
            
        try:
            if not self.refresh_token:
                raise SmartAPIConnectionError("No refresh token available")
            return self.api.getProfile(self.refresh_token)
        except Exception as e:
            raise SmartAPIConnectionError(f"Failed to fetch profile: {str(e)}")
    
    def get_ltp(self, exchange: str, symbol: str, token: str) -> Dict:
        """Get LTP (Last Traded Price) for a symbol with session validation."""
        if not self.check_session():
            raise SmartAPIConnectionError("Failed to establish valid session")
            
        try:
            return self.api.ltpData(exchange, symbol, token)
        except Exception as e:
            raise SmartAPIConnectionError(f"Failed to fetch LTP: {str(e)}")
    
    def logout(self) -> None:
        """Logout from the current session."""
        if self.api:
            try:
                self.api.terminateSession(self.config['CLIENT_CODE'])
                print("Successfully logged out")
            except Exception as e:
                print(f"Error during logout: {str(e)}")
            finally:
                self.api = None
                self.session_expiry = None
                self.refresh_token = None 