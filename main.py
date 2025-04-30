from config.config_loader import ConfigLoader
from api.smart_api_manager import SmartAPIManager, SmartAPIConnectionError

def main():
    try:
        # Load configuration
        config_loader = ConfigLoader()
        config = config_loader.load_config()
        
        # Initialize and test API connection
        api_manager = SmartAPIManager(config)
        
        # Test login and profile fetch
        print("Attempting to connect to SmartAPI...")
        profile = api_manager.get_profile()
        print("\nProfile Data:")
        print(f"Client Name: {profile['data']['name']}")
        print(f"Email: {profile['data']['email']}")
        print(f"Client Code: {profile['data']['clientcode']}")
        
        # Example LTP fetch (NIFTY 50)
        print("\nFetching NIFTY 50 LTP...")
        ltp_data = api_manager.get_ltp(
            exchange="NSE",
            symbol="NIFTY",
            token="26000"
        )
        print(f"NIFTY 50 LTP: {ltp_data['data']['ltp']}")
        
    except SmartAPIConnectionError as e:
        print(f"API Connection Error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
    finally:
        # Ensure proper logout
        if 'api_manager' in locals():
            api_manager.logout()

if __name__ == "__main__":
    main() 