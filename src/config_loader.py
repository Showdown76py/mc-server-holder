import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from toml_parser import parse_toml_file, TOMLParseError

def load_config():
    try:
        config = parse_toml_file('config/config.toml')
        print("Configuration loaded successfully!")
        return config
    except TOMLParseError as e:
        print(f"Error loading configuration: {e}")
        print("Using default configuration...")
        return {
            'server': {
                'host': '0.0.0.0',
                'port': 25565,
                'messages': {
                    'motd': "§cServer is closed.",
                    'kick_message': "§cThe server is currently §lCLOSED."
                }
            },
            'minecraft': {
                'version': "Offline",
                'protocol_version': 47
            }
        }
