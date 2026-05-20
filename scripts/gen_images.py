#!/usr/bin/env python3
"""Generate Psweep landing images with Gemini 2.5 Flash Image (nano-banana).

Uses a real product photo as reference so every generated scene contains the
exact P-SWEEP bottle (teal label, white body, white screw cap, paw prints).
"""
import os, sys, json, base64, pathlib, urllib.request, urllib.error, time

API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    sys.exit("GEMINI_API_KEY not set")

MODEL = "gemini-2.5-flash-image"
ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"

ROOT = pathlib.Path(__file__).parent.parent
OUT_DIR = ROOT / "assets" / "generated"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Reference images of the real product
REF_DIR = ROOT / "assets" / "reference"
REF_PRIMARY = REF_DIR / "product-stacked.png"           # clear front-facing label
REF_IN_USE = REF_DIR / "product-in-use.png"             # in-context shot on tile floor
REF_SHELF_STYLE = REF_DIR / "shelf-premium-style.png"   # premium shelf style ref

def load_ref(path: pathlib.Path) -> dict:
    return {
        "inlineData": {
            "mimeType": "image/png",
            "data": base64.b64encode(path.read_bytes()).decode(),
        }
    }

PRIMARY_PART = load_ref(REF_PRIMARY)
IN_USE_PART = load_ref(REF_IN_USE)
SHELF_STYLE_PART = load_ref(REF_SHELF_STYLE)

# Product description repeated in every prompt — anchors the model to the real bottle
PRODUCT = (
    "the exact P-SWEEP product bottle shown in the reference image: "
    "white cylindrical plastic bottle, white screw cap, teal/dark-cyan label "
    "with 'P-SWEEP' written in orange/yellow letters, lavender paw-print pattern "
    "on the label, white body with subtle purple paw prints, ~180g size. "
    "Keep the label, colors and bottle shape EXACTLY as in the reference. "
    "Do NOT redesign the label. Do NOT change the brand colors."
)

STYLE = (
    "Photorealistic, high quality product photography, natural soft daylight, "
    "shallow depth of field, clean modern Argentine home aesthetic, "
    "warm neutral tones with teal accents from the product, premium commercial feel. "
    "NOT illustration, NOT cartoon, NOT 3D render. Real-world camera look. "
    "No added text or watermarks in the image."
)

# Each entry: (prompt, list of reference parts to include)
PROMPTS = {
    "hero-product": (
        f"Lifestyle product photograph of {PRODUCT} "
        "displayed in the foreground of a pet supply store. "
        "Sharp focus on the single upright bottle, label facing the camera. "
        "Background is a softly blurred pet shop scene: wooden shelves stocked "
        "with colorful pet food bags, dog toys, leashes, treats and accessories. "
        "Warm store lighting, shallow depth of field bokeh in the background, "
        "natural shop atmosphere — clearly a retail pet store, not a home. "
        "Square framing, bottle centered, no text overlays. "
        f"{STYLE}",
        [PRIMARY_PART],
    ),
    "product-in-action": (
        f"Photograph of {PRODUCT} tipped on its side on a light grey ceramic "
        "tile floor, actively spilling pale off-white absorbent powder onto a "
        "spreading yellow puddle of pet urine. The powder is reacting with the "
        "liquid — partially absorbed, forming clumps where it meets the puddle. "
        "Bottle slightly off-center, action shot from a low 3/4 angle. "
        "Modern Argentine home interior softly blurred in background, warm light. "
        f"{STYLE}",
        [PRIMARY_PART, IN_USE_PART],
    ),
    "step-1": (
        "Close-up overhead photograph of a clearly visible bright yellow puddle "
        "of pet urine on a light grey ceramic tile floor. A hand enters from the "
        f"top right of the frame, tipping {PRODUCT} sideways and sprinkling fine "
        "off-white absorbent powder out of the open bottle directly onto the puddle. "
        "Powder mid-air, caught in motion. The yellow urine puddle must be the "
        "MAIN visible element — large, golden-yellow, with a clear glossy surface "
        "and visible edges on the tile. Modern Argentine home, blurred background. "
        f"{STYLE}",
        [PRIMARY_PART, IN_USE_PART],
    ),
    "step-2": (
        f"Close-up macro photograph of a tile floor where a small puddle has "
        "transformed into pale off-white solidified gel clumps and granules. "
        f"{PRODUCT} stands upright in the background, slightly out of focus. "
        "Light grey ceramic tile, soft natural daylight from a side window, "
        "no liquid visible anymore — only solid absorbent residue. "
        f"{STYLE}",
        [PRIMARY_PART, IN_USE_PART],
    ),
    "step-3": (
        f"Photograph of a wooden broom and metal dustpan sweeping pale off-white "
        "solidified gel granules off a clean ceramic tile floor into the dustpan. "
        f"{PRODUCT} sits to the side of the frame. "
        "Slight motion blur on broom bristles, side-low camera angle, "
        "modern Argentine home interior, warm daylight. "
        f"{STYLE}",
        [PRIMARY_PART],
    ),
    "step-4": (
        "Photograph of a friendly golden retriever and a calm tabby cat sitting "
        "together on a perfectly clean dry ceramic tile floor in a sunlit modern "
        f"Argentine living room. {PRODUCT} placed neatly on a side table or "
        "shelf in the background, clearly visible but not dominant. "
        "Soft window light from the left, warm and inviting. Floor is spotless. "
        f"{STYLE}",
        [PRIMARY_PART],
    ),
    "b2b-shelf": (
        "Premium retail shelf photograph: modern wooden shelves with warm strip "
        "LED lights mounted underneath each shelf, soft bokeh of a pet store in "
        "the background, low-angle three-quarter perspective showing two rows of "
        f"product. Every single bottle on the shelves must be {PRODUCT} — IDENTICAL "
        "bottles aligned in neat rows, no other products visible. "
        "CRITICAL: the bottles must have a WHITE screw cap (NOT yellow, NOT any "
        "other color — pure WHITE plastic cap), white cylindrical body, and the "
        "teal/dark-cyan label with 'P-SWEEP' in orange/yellow letters and "
        "lavender paw prints exactly as shown in the reference. "
        "NO price tags, NO shelf-edge labels, NO text overlays anywhere. "
        "Premium pet store aesthetic, shallow depth of field, square framing.",
        [PRIMARY_PART],
    ),
    "demo-poster": (
        f"Photographic triptych on a single horizontal image, 3 panels divided "
        f"by thin white gaps. {PRODUCT} appears in panels 2 and 3. "
        "LEFT panel: a small yellow puddle on a grey ceramic tile floor with a "
        "curious dog in the background. "
        f"MIDDLE panel: a hand sprinkling powder from {PRODUCT} onto that same puddle. "
        "RIGHT panel: same tile floor now completely dry and clean with a happy "
        f"dog sitting on it next to {PRODUCT}. "
        "Cohesive lighting and tile across all 3 panels. Wide cinematic 16:9 framing. "
        f"{STYLE}",
        [PRIMARY_PART, IN_USE_PART],
    ),
}

def generate(prompt: str, refs: list, out_path: pathlib.Path, attempt: int = 1) -> bool:
    parts = [{"text": prompt}] + refs
    body = json.dumps({
        "contents": [{"parts": parts}],
        "generationConfig": {"responseModalities": ["IMAGE"]},
    }).encode()
    req = urllib.request.Request(
        ENDPOINT, data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            data = json.loads(r.read())
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", "replace")[:500]
        print(f"  ✗ HTTP {e.code}: {err}")
        if e.code in (429, 503) and attempt < 3:
            time.sleep(4 * attempt)
            return generate(prompt, refs, out_path, attempt + 1)
        return False
    except Exception as e:
        print(f"  ✗ {type(e).__name__}: {e}")
        return False

    parts_out = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    for p in parts_out:
        inline = p.get("inlineData") or p.get("inline_data")
        if inline and inline.get("data"):
            out_path.write_bytes(base64.b64decode(inline["data"]))
            print(f"  ✓ {out_path.name} ({out_path.stat().st_size // 1024} KB)")
            return True
    print(f"  ✗ no image in response: {json.dumps(data)[:300]}")
    return False

ok = fail = 0
for name, (prompt, refs) in PROMPTS.items():
    out = OUT_DIR / f"{name}.png"
    if out.exists() and out.stat().st_size > 5000:
        print(f"• {name} — skip (exists)")
        ok += 1
        continue
    print(f"• {name} (refs={len(refs)}) …")
    if generate(prompt, refs, out):
        ok += 1
    else:
        fail += 1
    time.sleep(0.6)

print(f"\nDone: {ok} ok, {fail} failed → {OUT_DIR}")
sys.exit(0 if fail == 0 else 1)
