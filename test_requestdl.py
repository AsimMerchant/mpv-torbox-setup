#!/usr/bin/env python3
"""Test TorBox requestdl endpoint to get streaming URL"""

import base64
import httpx
from dotenv import load_dotenv
import os

# Load API key
load_dotenv('.env')
encoded_key = os.getenv('TORBOX_API_KEY')
api_key = base64.b64decode(encoded_key).decode('utf-8')

headers = {"Authorization": f"Bearer {api_key}"}

# Using the same file from inspect_file_structure.py
torrent_id = 8010485
file_id = 5

print("Testing TorBox requestdl endpoint...")
print("=" * 60)
print(f"Torrent ID: {torrent_id}")
print(f"File ID: {file_id}")
print("=" * 60)

# Try the requestdl endpoint
url = f"https://api.torbox.app/v1/api/torrents/requestdl"

try:
    response = httpx.get(
        url,
        headers=headers,
        params={"token": api_key, "torrent_id": torrent_id, "file_id": file_id},
        timeout=10.0
    )
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response:\n{response.text}")
    
    if response.status_code == 200:
        data = response.json()
        if 'data' in data:
            # Mask the token in the URL for display
            url = data['data']
            masked_url = url.replace(api_key, "***API_KEY***")
            print(f"\nStreaming URL: {masked_url}")
        
except Exception as e:
    print(f"Error: {e}")
