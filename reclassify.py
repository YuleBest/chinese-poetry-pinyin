import os
import json
import shutil
from pypinyin import pinyin, Style

def get_pinyin_initial(char):
    if not char.strip():
        return '#'
    py = pinyin(char, style=Style.FIRST_LETTER)
    if not py or not py[0] or not py[0][0]:
        return '#'
    initial = py[0][0][0].upper()
    if 'A' <= initial <= 'Z':
        return initial
    return '#'

def get_title_initial_at(title, depth):
    if depth < len(title):
        return get_pinyin_initial(title[depth])
    return 'END'

def split_and_save(items, depth, prefix, dist_dir):
    json_str = json.dumps(items, ensure_ascii=False, indent=2)
    size = len(json_str.encode('utf-8'))
    
    if size <= 180 * 1024:
        filename = f"{prefix}.json" if prefix else "ALL.json"
        filepath = os.path.join(dist_dir, filename)
        with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
            f.write(json_str)
        return

    max_len = max([len(item.get('title') or '') for item in items]) if items else 0
    if depth >= max_len:
        # Force split into chunks based on size
        current_chunk = []
        current_size = 2 # length of "[\n"
        chunk_idx = 1
        
        for item in items:
            item_str = json.dumps(item, ensure_ascii=False, indent=2)
            item_size = len(item_str.encode('utf-8')) + 3 
            
            if current_size + item_size > 180 * 1024 and current_chunk:
                # Save current chunk
                filepath = os.path.join(dist_dir, f"{prefix}_{chunk_idx}.json")
                with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
                    json.dump(current_chunk, f, ensure_ascii=False, indent=2)
                chunk_idx += 1
                current_chunk = [item]
                current_size = 2 + item_size
            else:
                current_chunk.append(item)
                current_size += item_size
                
        if current_chunk:
            filepath = os.path.join(dist_dir, f"{prefix}_{chunk_idx}.json")
            with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
                json.dump(current_chunk, f, ensure_ascii=False, indent=2)
        return

    # Group by pinyin
    groups = {}
    for item in items:
        title = item.get('title') or ''
        initial = get_title_initial_at(title, depth)
        if initial not in groups:
            groups[initial] = []
        groups[initial].append(item)
        
    for initial, group_items in groups.items():
        if initial == 'END':
            new_prefix = f"{prefix}_END" if prefix else "END"
        else:
            new_prefix = f"{prefix}{initial}" if prefix else initial
            
        split_and_save(group_items, depth + 1, new_prefix, dist_dir)

def main():
    base_dir = r"d:\chinese-poetry-pinyin"
    dist_dir = os.path.join(base_dir, "dist")
    
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)
    os.makedirs(dist_dir, exist_ok=True)
    
    all_items = []
    
    print("Loading JSON files...")
    # Read all JSON files in subdirectories
    for root, dirs, files in os.walk(base_dir):
        # Skip dist dir
        if "dist" in os.path.normpath(root).split(os.sep):
            continue
        if ".git" in root or ".wrangler" in root:
            continue
            
        for file in files:
            if file.endswith('.json'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            for item in data:
                                if 'category' in item:
                                    del item['category']
                                all_items.append(item)
                        elif isinstance(data, dict):
                            if 'category' in data:
                                del data['category']
                            all_items.append(data)
                except Exception as e:
                    print(f"Error reading {filepath}: {e}")
                    
    print(f"Total items loaded: {len(all_items)}")
    
    print("Starting recursively split and save...")
    # Start splitting
    split_and_save(all_items, 0, "", dist_dir)
    print("Finished reclassifying.")

if __name__ == "__main__":
    main()
