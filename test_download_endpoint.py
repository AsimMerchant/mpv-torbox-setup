#!/usr/bin/env python3
"""Test TorBox download endpoint formats"""

import base64
import httpx
from dotenv import load_dotenv
import os

# Load API key
load_dotenv('.env')
encoded_key = os.getenv('TORBOX_API_KEY')
api_key = base64.b64decode(encoded_key).decode('utf-8')

headers = {"Authorization": f"Bearer {api_key}"}

# Test different possible endpoint patterns
torrent_id = 8010485
file_id = 5
hash_value = "25f318fa42f649953615897d83b1c70db4b8fdc6"

test_urls = [
    f"https://api.torbox.app/v1/api/torrents/requestdl?token={api_key}&torrent_id={torrent_id}&file_id={file_id}",
    f"https://api.torbox.app/v1/api/torrents/requestdl?torrent_id={torrent_id}&file_id={file_id}",
]

print("Testing TorBox download endpoint formats...")
print("=" * 60)

for url in test_urls:
    print(f"\nTesting: {url[:80]}...")
    try:
        response = httpx.get(url, headers=headers, timeout=10.0, follow_redirects=False)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {data}")
        elif response.status_code in [301, 302, 307, 308]:
            print(f"Redirect to: {response.headers.get('Location', 'N/A')}")
        else:
            print(f"Response: {response.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")

print("\n" + "=" * 60)
print("\nLet me also check if there's a createdownload endpoint...")

# Try createdownload endpoint
url = "https://api.torbox.app/v1/api/torrents/createdownload"
try:
    response = httpx.post(
        url,
        headers=headers,
        json={"torrent_id": torrent_id, "file_id": file_id},
        timeout=10.0
    )
    print(f"POST createdownload - Status: {response.status_code}")
    print(f"Response: {response.text[:500]}")
except Exception as e:
    print(f"Error: {e}")
