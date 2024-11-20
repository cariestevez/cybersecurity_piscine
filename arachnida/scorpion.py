import argparse
import os
import exifread
from datetime import datetime

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp"}

def process_file(file_path):
    try:
        file_ext = os.path.splitext(file_path)[1].lower()

        if file_ext in SUPPORTED_EXTENSIONS:
            print(f"\nProcessing file: {file_path}")
            print(f"File size: {os.path.getsize(file_path)} bytes")
            print(f"Created on: {datetime.fromtimestamp(os.path.getctime(file_path)).strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Last modified: {datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')}")

            with open(file_path, 'rb') as file:
                tags = exifread.process_file(file)
                print(f"EXIF data:" if tags else "EXIF data can't be retrieved!")
                for tag, value in tags.items():
                    print(f"{tag}: {value}")

    except Exception as e:
        print(f"Error processing {file_path}: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Program to extract image metadata.",
        usage="scorpion.py [-h] file1 [file2...]"
    )
    parser.add_argument("files", nargs='+', help="The name of the file(s) to extract from.")

    args = parser.parse_args()
    
    for file_path in args.files:
        abs_path = os.path.abspath(file_path)
        
        if not os.path.exists(abs_path):
            print(f"Error: File not found - {file_path}")
            continue
        
        process_file(abs_path)

if __name__ == "__main__":
    main()