#!/usr/bin/env python3
"""
Utility script to clear all active monitors
Run this if monitors are stuck or you want to start fresh
"""

import requests
import sys

API_BASE_URL = "http://localhost:8000"

def clear_all_monitors():
    """Delete all active monitors"""
    try:
        # Get all monitors
        response = requests.get(f"{API_BASE_URL}/monitors")
        response.raise_for_status()
        
        monitors = response.json().get("monitors", [])
        print(f"Found {len(monitors)} active monitors")
        
        if len(monitors) == 0:
            print("No monitors to delete")
            return
        
        # Delete each monitor
        deleted = 0
        for monitor in monitors:
            monitor_id = monitor.get("monitor_id")
            url = monitor.get("url")
            print(f"Deleting monitor: {monitor_id} ({url})")
            
            try:
                del_response = requests.delete(f"{API_BASE_URL}/monitors/{monitor_id}")
                if del_response.status_code == 200:
                    deleted += 1
                    print(f"  ✓ Deleted")
                else:
                    print(f"  ✗ Failed: {del_response.json().get('detail', 'Unknown error')}")
            except Exception as e:
                print(f"  ✗ Error: {str(e)}")
        
        print(f"\n✓ Successfully deleted {deleted}/{len(monitors)} monitors")
        
    except requests.exceptions.ConnectionError:
        print("✗ Error: Cannot connect to backend server at http://localhost:8000")
        print("  Make sure the backend server is running!")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    print("=== Monitor Cleanup Utility ===\n")
    clear_all_monitors()
