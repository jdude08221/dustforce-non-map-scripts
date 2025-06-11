import os
import io
from flask import Flask, request, send_file, jsonify, send_from_directory
from PIL import Image, ImageDraw
import numpy as np

# --- Constants and mappings ---
SCALE_FACTOR = 48.0 / 95.0
PIXELS_PER_UNIT = 1.0 / SCALE_FACTOR
TOLERANCE = 50
LINE_WIDTH = 3

ATTACK_MAP = {
    'ul': 'Grounded Up Light', 'sl': 'Grounded Side Light', 'dl': 'Grounded Down Light',
    'aul': 'Aerial Up Light', 'adl': 'Aerial Down Light', 'asl': 'Aerial Side Light',
    'uh': 'Grounded Up Heavy', 'sh': 'Grounded Side Heavy', 'dh': 'Grounded Down Heavy',
    'auh': 'Aerial Up Heavy', 'ash': 'Aerial Side Heavy', 'adh': 'Aerial Down Heavy'
}
CHAR_MAP = {'dm': 'dustman', 'dg': 'dustgirl', 'dk': 'dustkid', 'dw': 'dustworth'}
CHAR_OUTLINE_HEX = {'dw': 0x96ad66, 'dm': 0x8199d3, 'dk': 0xb37ed4, 'dg': 0xbb584d}
CHAR_COLORS = {k: ((v >> 16) & 255, (v >> 8) & 255, v & 255) for k, v in CHAR_OUTLINE_HEX.items()}
TARGET_HEX = [0x52DB22, 0x52E23F]
TARGET_RGB = [((h >> 16) & 255, (h >> 8) & 255, h & 255) for h in TARGET_HEX]

IMAGE_DIR = os.path.abspath("images")

def extract_hit_mask(pil_img, tol=TOLERANCE):
    arr = np.array(pil_img.convert("RGB"), dtype=np.int16)
    combined = np.zeros(arr.shape[:2], dtype=bool)
    for tgt in TARGET_RGB:
        diff = np.abs(arr - np.array(tgt))
        combined |= np.all(diff <= tol, axis=2)
    return Image.fromarray((combined.astype(np.uint8) * 255), mode="L")

def compose_outline_overlay(filepaths):
    # Use the original image size for overlay
    if not filepaths:
        return Image.new("RGBA", (95, 96), (0,0,0,0))
    with Image.open(filepaths[0]) as first_img:
        w, h = first_img.size

    canvas = Image.new("RGBA", (w, h), (0,0,0,0))
    draw = ImageDraw.Draw(canvas)

    for fp in filepaths:
        base = os.path.splitext(os.path.basename(fp))[0]
        if "_" in base:
            atk, ch = base.split("_", 1)
        else:
            atk, ch = "", ""
        col = CHAR_COLORS.get(ch, (0,0,0))
        with Image.open(fp) as im:
            mask = extract_hit_mask(im)
            bbox = mask.getbbox()
            if "adh" in base:  # or use the exact filename for aerial down heavy
                print(f"Aerial Down Heavy bbox for {fp}: {bbox}")
            if bbox:
                # Draw directly in image pixel coordinates
                rect = (bbox[0], bbox[1], bbox[2], bbox[3])
                draw.rectangle(rect, outline=col+(200,), width=LINE_WIDTH)
    return canvas

def build_tree():
    char_dict = {k: [] for k in CHAR_MAP}
    atk_dict = {k: [] for k in ATTACK_MAP}
    for fn in sorted(os.listdir(IMAGE_DIR)):
        if fn.lower().endswith(".png"):
            base = os.path.splitext(fn)[0]
            if "_" not in base: continue
            atk, ch = base.split("_", 1)
            if ch in char_dict:
                char_dict[ch].append({'file': fn, 'atk': atk})
            if atk in atk_dict:
                atk_dict[atk].append({'file': fn, 'ch': ch})

    def is_aerial(atk):
        return atk.startswith('a')

    def is_light(atk):
        return atk.endswith('l')

    def is_heavy(atk):
        return atk.endswith('h')

    def clean_attack_label(atk):
        label = ATTACK_MAP.get(atk, atk)
        if label.lower().startswith("grounded "):
            label = label[len("grounded "):]
        if label.lower().startswith("aerial "):
            label = label[len("aerial "):]
        if label.lower().startswith("light "):
            label = label[len("light "):]
        if label.lower().startswith("heavy "):
            label = label[len("heavy "):]
        return label

    # Characters root
    chars_root = {
        'label': 'Characters',
        'children': []
    }
    for ch, files in char_dict.items():
        ch_node = {'label': CHAR_MAP.get(ch, ch).title(), 'children': []}
        for mode, mode_label in [(False, 'Grounded'), (True, 'Aerial')]:
            mode_files = [f for f in files if is_aerial(f['atk']) == mode]
            if not mode_files:
                continue
            mode_node = {'label': mode_label, 'children': []}
            for strength, strength_label in [(True, 'Heavy'), (False, 'Light')]:
                strength_files = [f for f in mode_files if (is_heavy(f['atk']) if strength else is_light(f['atk']))]
                if not strength_files:
                    continue
                strength_node = {
                    'label': strength_label,
                    'children': [
                        {'label': clean_attack_label(f['atk']), 'file': f['file']}
                        for f in strength_files
                    ]
                }
                mode_node['children'].append(strength_node)
            ch_node['children'].append(mode_node)
        chars_root['children'].append(ch_node)

    # Attacks root, grouped similarly
    atks_root = {
        'label': 'Attacks',
        'children': []
    }
    for mode, mode_label in [(False, 'Grounded'), (True, 'Aerial')]:
        mode_attacks = [atk for atk in atk_dict if is_aerial(atk) == mode]
        if not mode_attacks:
            continue
        mode_node = {'label': mode_label, 'children': []}
        for strength, strength_label in [(True, 'Heavy'), (False, 'Light')]:
            strength_attacks = [atk for atk in mode_attacks if (is_heavy(atk) if strength else is_light(atk))]
            if not strength_attacks:
                continue
            strength_node = {'label': strength_label, 'children': []}
            for atk in strength_attacks:
                atk_node = {
                    'label': clean_attack_label(atk),
                    'children': [
                        {'label': CHAR_MAP.get(f['ch'], f['ch']).title(), 'file': f['file']}
                        for f in atk_dict[atk]
                    ]
                }
                strength_node['children'].append(atk_node)
            mode_node['children'].append(strength_node)
        atks_root['children'].append(mode_node)

    return [chars_root, atks_root]

app = Flask(__name__)

@app.route("/api/tree")

def api_tree():
    return jsonify(build_tree())

@app.route("/api/compose", methods=["POST"])
def api_compose():
    data = request.json
    files = data.get("files", [])
    filepaths = [os.path.join(IMAGE_DIR, f) for f in files]
    img = compose_outline_overlay(filepaths)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/<path:path>")
def static_proxy(path):
    return send_from_directory("static", path)

if __name__ == "__main__":
    app.run(debug=True)