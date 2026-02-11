import os
import ast
import sys

def format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"

def analyze_pkg(pkg_path):
    with open(pkg_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # The file contains a tuple, we want the list which is the 3rd element
    # formatting is loose, so we'll use ast.literal_eval if possible, 
    # but the file might not be a valid single python expression (it looks like one tuple)
    
    try:
        data = ast.literal_eval(content)
        file_list = data[2]
    except Exception as e:
        print(f"Error parsing PKG file: {e}")
        return

    print(f"{'File':<50} | {'Size':<10} | {'Type':<10}")
    print("-" * 75)
    
    total_size = 0
    type_sizes = {}
    module_sizes = {}
    
    # Sort by size descending
    files_with_size = []
    
    for item in file_list:
        name, path, type_code = item[:3]
        if path == '': # Internal PYZ or similar
            continue
            
        try:
            # Handle some paths starting with '\\?\' (Windows long paths) or relative
            if not os.path.exists(path):
                # Try to resolve relative to build dir if needed, but usually absolute
                continue
                
            size = os.path.getsize(path)
            files_with_size.append((name, size, type_code))
            total_size += size
            
            type_sizes[type_code] = type_sizes.get(type_code, 0) + size
            
            # Module breakdown
            module = "unknown"
            lower_name = name.lower()
            if "numpy" in lower_name: module = "numpy"
            elif "shazamio" in lower_name: module = "shazamio"
            elif "aiohttp" in lower_name: module = "aiohttp"
            elif "rich" in lower_name: module = "rich"
            elif "pyaudio" in lower_name: module = "pyaudio"
            elif "speech_recognition" in lower_name: module = "speech_recognition"
            elif ".dll" in lower_name: module = "DLLs"
            
            module_sizes[module] = module_sizes.get(module, 0) + size
            
        except OSError:
            pass
            
    files_with_size.sort(key=lambda x: x[1], reverse=True)
    
    for name, size, type_code in files_with_size[:20]: # Top 20
        print(f"{name[-50:]:<50} | {format_size(size):<10} | {type_code:<10}")
        
    print("-" * 75)
    print(f"Total Content Size: {format_size(total_size)}")
    
    print("\nBreakdown by Module:")
    for module, size in sorted(module_sizes.items(), key=lambda x: x[1], reverse=True):
        print(f"{module:<20}: {format_size(size)}")

    print("\nBreakdown by Type:")
    for type_code, size in sorted(type_sizes.items(), key=lambda x: x[1], reverse=True):
        print(f"{type_code:<10}: {format_size(size)}")

if __name__ == "__main__":
    pkg_file = r"d:\dev\repos\aura\build\ShazamLive\PKG-00.toc"
    analyze_pkg(pkg_file)
