import os
import json
from PIL import Image
import numpy as np
from scipy.ndimage import label, find_objects

# --- CONFIGURATION ---
IMAGE_DIR = "images"
OUTPUT_JSON = os.path.join("static", "hitboxes.json")
TOLERANCE = 50
TARGET_HEX = [0x52DB22, 0x52E23F]
TARGET_RGB = [((h >> 16) & 255, (h >> 8) & 255, h & 255) for h in TARGET_HEX]

def extract_hitbox_rects(img_path, tol=TOLERANCE):
    img = Image.open(img_path).convert("RGB")
    arr = np.array(img, dtype=np.int16)
    mask = np.zeros(arr.shape[:2], dtype=bool)
    for tgt in TARGET_RGB:
        diff = np.abs(arr - np.array(tgt))
        mask |= np.all(diff <= tol, axis=2)
    # Label connected regions
    labeled, num_features = label(mask)
    rects = []
    for sl in find_objects(labeled):
        if sl is None:
            continue
        y0, y1 = sl[0].start, sl[0].stop
        x0, x1 = sl[1].start, sl[1].stop
        rects.append([int(x0), int(y0), int(x1), int(y1)])
    return rects

def main():
    os.makedirs("static", exist_ok=True)
    hitbox_data = {}
    for fname in os.listdir(IMAGE_DIR):
        if fname.lower().endswith(".png"):
            path = os.path.join(IMAGE_DIR, fname)
            rects = extract_hitbox_rects(path)
            hitbox_data[fname] = rects
            print(f"{fname}: {rects}")
    with open(OUTPUT_JSON, "w") as f:
        json.dump(hitbox_data, f, indent=2)
    print(f"Saved hitbox rectangles to {OUTPUT_JSON}")

if __name__ == "__main__":
    main()