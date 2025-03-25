import os
import re

CHUNK_SIZE = 25 * 1024 * 1024  # 25MB default chunk size

def split_file(file_path, chunk_size=CHUNK_SIZE):
    """Splits a large .uasset file into 25MB chunks."""
    if not os.path.exists(file_path):
        print("❌ File not found!")
        return

    file_name, file_ext = os.path.splitext(file_path)
    
    with open(file_path, 'rb') as f:
        chunk_index = 0
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break  # End of file
            
            chunk_filename = f"{file_name}_part{chunk_index:03d}{file_ext}"
            with open(chunk_filename, 'wb') as chunk_file:
                chunk_file.write(chunk)
            
            print(f"✅ Created: {chunk_filename} ({len(chunk)} bytes)")
            chunk_index += 1

    print(f"\n✅ File split into {chunk_index} parts.")

    # Ask user if they want to delete the original file
    delete_original = input(f"🗑️ Do you want to delete the original file '{file_path}'? (y/n): ").strip().lower()
    if delete_original == 'y':
        os.remove(file_path)
        print(f"🗑️ Deleted: {file_path}")

def auto_merge_files(directory):
    """Automatically detects and merges split files in a directory."""
    os.chdir(directory)  # Change working directory to user input

    # Find all chunked files with pattern *_partXXX.*
    chunk_files = [f for f in os.listdir() if re.search(r"_part\d+\.", f)]
    if not chunk_files:
        print("❌ No split files found in the directory.")
        return

    # Group files by common prefix
    file_groups = {}
    for file in chunk_files:
        prefix = re.split(r"_part\d+\.", file)[0]  # Extract prefix
        if prefix not in file_groups:
            file_groups[prefix] = []
        file_groups[prefix].append(file)

    # Merge each group
    for prefix, files in file_groups.items():
        files.sort(key=lambda x: int(re.search(r"_part(\d+)", x).group(1)))  # Sort by part number
        output_file_name = f"{prefix}{os.path.splitext(files[0])[1]}"  # Keep original filename without "_merged"

        with open(output_file_name, 'wb') as output_file:
            for file in files:
                with open(file, 'rb') as f:
                    output_file.write(f.read())
                print(f"✅ Merged: {file} -> {output_file_name}")

        print(f"\n✅ Successfully reconstructed: {output_file_name}")

        # Ask user if they want to delete the split files
        delete_chunks = input(f"🗑️ Do you want to delete the split files for '{prefix}'? (y/n): ").strip().lower()
        if delete_chunks == 'y':
            for file in files:
                os.remove(file)
                print(f"🗑️ Deleted: {file}")

def auto_slice_files(directory, chunk_size=CHUNK_SIZE):
    """Automatically finds large files in a directory and splits them into chunks."""
    os.chdir(directory)  # Change working directory to user input
    files = [f for f in os.listdir() if os.path.isfile(f) and not re.search(r"_part\d+\.", f)]

    if not files:
        print("❌ No files found in the directory.")
        return

    for file in files:
        file_size = os.path.getsize(file)
        if file_size > chunk_size:
            print(f"📂 Splitting '{file}' ({file_size} bytes)...")
            split_file(file)

# 🛠 User Input for Directory & Action
directory = input("📂 Enter the directory path: ").strip()
if not os.path.isdir(directory):
    print("❌ Invalid directory! Please enter a valid path.")
    exit()

os.chdir(directory)  # Change working directory to user input

action = input("🔄 Do you want to [S]plit, [M]erge, [A]uto Merge, or [X] Auto Slice? ").strip().lower()

if action == "s":
    file_name = input("📁 Enter the .uasset file name to split: ").strip()
    split_file(file_name)
elif action == "m":
    output_file = input("📁 Enter the output file name (e.g., merged_file.uasset): ").strip()
    chunk_prefix = input("🔍 Enter the prefix of split files (without '_partXXX.uasset'): ").strip()
    merge_files(output_file, chunk_prefix) # type: ignore
elif action == "a":
    auto_merge_files(directory)
elif action == "x":
    auto_slice_files(directory)
else:
    print("❌ Invalid choice! Please enter 'S' for Split, 'M' for Merge, 'A' for Auto Merge, or 'X' for Auto Slice.")
