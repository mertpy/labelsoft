import os
import json

def scan_classes_from_jsons(dataset_dir):
    """
    Scans all .json files in the given directory and returns a list
    of unique class names found within them.
    """
    classes = set()
    if not dataset_dir: return list(classes)
    
    for filename in os.listdir(dataset_dir):
        if filename.endswith('.json'):
            json_path = os.path.join(dataset_dir, filename)
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if "shapes" in data:
                        for shape in data["shapes"]:
                            cname = shape.get("label")
                            if cname:
                                classes.add(cname)
            except Exception:
                pass
                
    return sorted(list(classes))
