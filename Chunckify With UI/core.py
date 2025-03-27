import os
import re
from typing import List, Dict

CHUNK_SIZE = 25 * 1024 * 1024  # 25MB default chunk size

class FileProcessor:
    @staticmethod
    def split_file(file_path: str, chunk_size: int = CHUNK_SIZE, delete_original: bool = False, output_dir: str = None) -> int:
        """Splits a large file into chunks.
        Returns the number of chunks created."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        print(f"📂 Splitting file: {file_path}")

        file_dir, file_name = os.path.split(file_path)
        file_name, file_ext = os.path.splitext(file_name)
        
        # Use specified output directory if provided, otherwise use original file's directory
        output_directory = output_dir if output_dir else file_dir
        
        chunk_index = 0
        
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                
                chunk_filename = f"{file_name}_part{chunk_index:03d}{file_ext}"
                chunk_path = os.path.join(output_directory, chunk_filename)
                with open(chunk_path, 'wb') as chunk_file:
                    chunk_file.write(chunk)
                chunk_index += 1
        
        if delete_original:
            os.remove(file_path)
        
        return chunk_index

    @staticmethod
    def merge_files(output_path: str, chunk_paths: List[str], delete_chunks: bool = False) -> None:
        """Merges chunks back into a single file."""
        # Ensure chunks are sorted numerically by their part number
        chunk_paths.sort(key=lambda x: int(re.search(r"_part(\d+)", os.path.basename(x)).group(1)))
        
        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        with open(output_path, 'wb') as output_file:
            for chunk_path in chunk_paths:
                with open(chunk_path, 'rb') as f:
                    output_file.write(f.read())
        
        if delete_chunks:
            for chunk_path in chunk_paths:
                try:
                    os.remove(chunk_path)
                except OSError:
                    pass

    @staticmethod
    def find_large_files(directory: str, min_size: int = CHUNK_SIZE) -> List[str]:
        """Returns list of files larger than min_size."""
        return [f for f in os.listdir(directory) 
                if os.path.isfile(os.path.join(directory, f)) 
                and os.path.getsize(os.path.join(directory, f)) > min_size
                and not re.search(r"_part\d+\.", f)]

    @staticmethod
    def find_chunk_groups(directory: str) -> Dict[str, List[str]]:
        """Finds all chunked files grouped by their base name."""
        chunk_files = [f for f in os.listdir(directory) if re.search(r"_part\d+\.", f)]
        file_groups = {}
        
        for file in chunk_files:
            prefix = re.split(r"_part\d+\.", file)[0]
            if prefix not in file_groups:
                file_groups[prefix] = []
            file_groups[prefix].append(file)
        
        # Sort each group by part number
        for prefix in file_groups:
            file_groups[prefix].sort(key=lambda x: int(re.search(r"_part(\d+)", x).group(1)))
        
        return file_groups