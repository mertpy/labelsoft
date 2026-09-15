import os

def load_classes_txt(dataset_dir):
    classes = {}
    if not dataset_dir: return classes
    classes_path = os.path.join(dataset_dir, 'classes.txt')
    if os.path.exists(classes_path):
        with open(classes_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line: continue
                if ':' in line:
                    parts = line.split(':', 1)
                    try:
                        cid = int(parts[0].strip())
                        cname = parts[1].strip()
                        classes[cid] = cname
                    except ValueError:
                        pass
    else:
        open(classes_path, 'w').close()
    return classes

def save_classes_txt(dataset_dir, classes):
    if not dataset_dir: return
    classes_path = os.path.join(dataset_dir, 'classes.txt')
    try:
        with open(classes_path, 'w', encoding='utf-8') as f:
            for cid, cname in sorted(classes.items()):
                f.write(f"{cid}: {cname}\n")
    except Exception as e:
        print(f"classes.txt kaydedilemedi: {e}")
