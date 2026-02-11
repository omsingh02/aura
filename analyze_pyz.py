import sys
import re

def parse_pyz_listing(file_path):
    # Format from pyi-archive_viewer -l:
    #  pos, length, uncompressed, name
    #  0, 10353098, 12556, 'zoneinfo._zoneinfo'
    
    module_sizes = {}
    total_size = 0
    
    with open(file_path, 'r') as f:
        for line in f:
            parts = line.strip().split(',')
            if len(parts) < 4: continue
            
            try:
                # remove leading/trailing whitespace/quotes
                size = int(parts[2].strip())
                name = parts[3].strip().strip("'")
                
                module = "unknown"
                if "rich" in name: module = "rich"
                elif "shazamio" in name: module = "shazamio"
                elif "aiohttp" in name: module = "aiohttp"
                elif "numpy" in name: module = "numpy"
                elif "pyaudio" in name: module = "pyaudio"
                elif "asyncio" in name: module = "asyncio"
                else:
                    # Group standard library or others
                    top_level = name.split('.')[0]
                    if top_level in ['typing', 'email', 'http', 'urllib', 'xml', 'multiprocessing', 'logging', 'unittest']:
                         module = "stdlib"
                    else:
                         module = "other"

                module_sizes[module] = module_sizes.get(module, 0) + size
                total_size += size
            except ValueError:
                pass

    print(f"{'Module':<20} | {'Size (Uncompressed)':<20}")
    print("-" * 45)
    for module, size in sorted(module_sizes.items(), key=lambda x: x[1], reverse=True):
        print(f"{module:<20} | {size / 1024 / 1024:.2f} MB")
    
    print("-" * 45)
    print(f"Total PYZ Size: {total_size / 1024 / 1024:.2f} MB")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        parse_pyz_listing(sys.argv[1])
    else:
        print("Usage: python analyze_pyz.py <listing_file>")
