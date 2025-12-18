#!/usr/bin/env python3
"""
Test My.JDownloader API using myjdapi library
"""

import base64
import os
from dotenv import load_dotenv
import myjdapi

def test_myjd_connection():
    """Test connection to My.JDownloader and add a link"""
    # Load environment variables
    load_dotenv()
    
    # Get credentials
    email = os.getenv('MYJD_EMAIL')
    encoded_password = os.getenv('MYJD_PASSWORD')
    device_name = os.getenv('MYJD_DEVICE_NAME')
    
    if not all([email, encoded_password, device_name]):
        print("✗ Missing My.JDownloader credentials in .env")
        return False
    
    # Decode password
    password = base64.b64decode(encoded_password).decode('utf-8')
    
    print(f"Connecting to My.JDownloader...")
    print(f"Email: {email}")
    print(f"Device: {device_name}")
    
    try:
        # Create API instance
        jd = myjdapi.Myjdapi()
        jd.set_app_key("TORBOX_BROWSER")
        
        # Connect
        jd.connect(email, password)
        print("✓ Connected successfully!")
        
        # Update devices
        jd.update_devices()
        
        # Get device
        device = jd.get_device(device_name)
        if not device:
            print(f"✗ Device '{device_name}' not found")
            print(f"Available devices: {[d['name'] for d in jd.list_devices()]}")
            return False
        
        print(f"✓ Found device: {device_name}")
        
        # Test adding a link
        test_url = "https://example.com/test.zip"
        print(f"\nTesting link addition: {test_url}")
        
        response = device.linkgrabber.add_links([{
            "autostart": False,
            "links": test_url,
            "packageName": "TorBox Test",
            "destinationFolder": None,
            "extractPassword": None,
            "priority": "DEFAULT",
            "downloadPassword": None,
            "overwritePackagizerRules": False
        }])
        
        print(f"✓ Link added successfully!")
        print(f"Response: {response}")
        
        # Disconnect
        jd.disconnect()
        print(f"\n✓ Test completed successfully!")
        return True
        
    except myjdapi.MYJDException as e:
        print(f"✗ My.JDownloader error: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("My.JDownloader API Test using myjdapi library")
    print("=" * 60)
    test_myjd_connection()

