#!/usr/bin/env python3
"""Test to inspect file object structure from TorBox API"""

import base64
import httpx
from dotenv import load_dotenv
import os
import json

# Load API key
load_dotenv('.env')
encoded_key = os.getenv('TORBOX_API_KEY')
api_key = base64.b64decode(encoded_key).decode('utf-8')

# Fetch torrents
url = "https://api.torbox.app/v1/api/torrents/mylist"
headers = {"Authorization": f"Bearer {api_key}"}

response = httpx.get(
    url,
    headers=headers,
    params={"limit": 10, "offset": 0, "bypass_cache": True},
    timeout=30.0
)

data = response.json()['data']

# Get first torrent with files
if data:
    torrent = data[0]
    print(f"Torrent ID: {torrent.get('id')}")
    print(f"Torrent Hash: {torrent.get('hash')}")
    print(f"Torrent Name: {torrent.get('name')}")
    print("\nFIRST FILE OBJECT STRUCTURE:")
    print("=" * 60)
    
    if torrent.get('files'):
        first_file = torrent['files'][0]
        print(json.dumps(first_file, indent=2))
        
        print("\n" + "=" * 60)
        print("Available fields in file object:")
        for key in first_file.keys():
            print(f"  - {key}: {type(first_file[key]).__name__}")
