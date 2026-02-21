"""
Quick test for exiftool metadata extraction
Tests the file analyzer module with a simple test file
"""

import os
import sys
from app.file_analyzer import analyze_file

# Create a test text file
test_file = "data/test_file.txt"
os.makedirs(os.path.dirname(test_file), exist_ok=True)

# Write test content
with open(test_file, "w") as f:
    f.write("This is a test file for exiftool analysis.\n")
    f.write("Author: DarkWeb Monitor\n")
    f.write("Software: Python 3.11\n")
    f.write("Keywords: forensic, analysis, metadata\n")

print("=" * 60)
print("🧪 Testing File Analyzer with Exiftool")
print("=" * 60)

# Analyze the test file
results = analyze_file(test_file)

print("\n📊 Analysis Results:")
print("-" * 60)

if results.get("success"):
    print(f"✅ Successfully analyzed: {results.get('filename')}")
    print(f"📏 File size: {results.get('file_size')} bytes")
    
    # Display exiftool results
    if results.get("exiftool"):
        exif = results["exiftool"]
        if exif.get("success"):
            metadata = exif.get("metadata", {})
            if metadata:
                print(f"\n📋 Exiftool Metadata ({exif.get('field_count', len(metadata))} fields):")
                print("-" * 60)
                for key, value in list(metadata.items())[:15]:  # Show first 15
                    print(f"  {key:25} : {str(value)[:50]}")
                if len(metadata) > 15:
                    print(f"  ... and {len(metadata) - 15} more fields")
            else:
                print("\n❌ No metadata extracted")
        else:
            print(f"\n⚠️ Exiftool error: {exif.get('error')}")
    
    # Display strings results
    if results.get("strings"):
        strings = results["strings"]
        if strings.get("success"):
            print(f"\n🔤 Strings Analysis ({strings.get('strings_found')} found):")
            print("-" * 60)
            for s in strings.get("sample_strings", [])[:10]:
                print(f"  {s}")
    
    # Display binwalk results
    if results.get("binwalk"):
        binwalk = results["binwalk"]
        if binwalk.get("success"):
            print(f"\n🔎 Binwalk Signatures:")
            print("-" * 60)
            for sig in binwalk.get("signatures", [])[:5]:
                print(f"  {sig}")

else:
    print(f"❌ Analysis failed: {results.get('error')}")

print("\n" + "=" * 60)
print("✅ Test completed")
print("=" * 60)

# Cleanup
os.remove(test_file)
