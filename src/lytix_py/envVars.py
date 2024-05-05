import os

LX_BASE_URL = os.environ.get("LX_BASE_URL", "https://api.lytix.co")
LX_API_KEY = os.environ.get("LX_API_KEY")

def validateEnvVars(): 
    if (LX_BASE_URL is None):
       print("LX_BASE_URL is not set")
    if (LX_API_KEY is None):
        print("LX_API_KEY is not set")


"""
Always validate when importing this file
@note This will not hard break, just print an error
"""
validateEnvVars()