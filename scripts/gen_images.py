#!/usr/bin/env python3
"""Generate Psweep landing images with Gemini 2.5 Flash Image (nano-banana)."""
import os, sys, json, base64, pathlib, urllib.request, urllib.error, time

API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    sys.exit("GEMINI_API_KEY not set")

MODEL = "gemini-2.5-flash-image"
ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"

OUT_DIR = pathlib.Path(__file__).parent.parent / "assets" / "generated"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Style brief — keep cohesive across all images
STYLE = (
    "Flat 2D illustration, friendly cartoon style, bold thick black outlines, "
    "vibrant brand palette: teal (#009E9B), violet (#6F4AFF), yellow (#FFB800), "
    "off-white background (#F7F7F5). Cheerful, modern, playful, NOT clinical, "
    "NOT pharmacy-like. Inspired by Duolingo / Notion mascots. No text in the image."
)

PROMPTS = {
    "hero-product": (
        "A cute friendly bottle of pet cleaning powder labeled 'Psweep', "
        "teal label with a happy paw print, yellow cap, white powder visible at top. "
        "PLAIN SOLID OFF-WHITE BACKGROUND (#F7F7F5), no checkered pattern, "
        "no transparency grid, no decorative tiles around the bottle. "
        "Just the bottle centered on a single flat background color. Square aspect. "
        f"{STYLE}"
    ),
    "step-1": (
        "A hand tipping a teal bottle, sprinkling white powder onto a small puddle on a tile floor, "
        "happy cartoon dog watching curiously from the side. Top-down 3/4 view. "
        f"{STYLE}"
    ),
    "step-2": (
        "A small puddle on tile floor turning into solid white gel chunks, "
        "sparkles and tiny stars around indicating transformation magic, "
        "a clock icon showing 2 minutes floating above. "
        f"{STYLE}"
    ),
    "step-3": (
        "A cheerful broom and yellow dustpan sweeping solid white gel chunks off a tile floor, "
        "motion lines indicating easy sweeping action. "
        f"{STYLE}"
    ),
    "step-4": (
        "A perfectly clean dry tile floor with a happy smiling dog and a happy cat sitting together, "
        "sparkles on the floor showing cleanliness, sun rays in soft yellow. "
        f"{STYLE}"
    ),
    "b2b-shelf": (
        "A modern pet shop retail shelf display with multiple Psweep bottles neatly aligned in rows, "
        "warm friendly lighting, price tags, a small 'NEW' burst label, "
        "wooden shelf base, friendly cartoon illustration. "
        f"{STYLE}"
    ),
    "demo-poster": (
        "Three-panel before/during/after illustration on a single image: "
        "LEFT panel shows a puddle on floor with a worried cat emoji; "
        "MIDDLE panel shows powder being sprinkled with sparkles; "
        "RIGHT panel shows clean floor with happy pet. "
        "Wide 16:9 cinematic aspect. Bold borders dividing the panels. "
        f"{STYLE}"
    ),
}

def generate(prompt: str, out_path: pathlib.Path, attempt: int = 1) -> bool:
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["IMAGE"]},
    }).encode()
    req = urllib.request.Request(
        ENDPOINT, data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read())
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", "replace")[:500]
        print(f"  ✗ HTTP {e.code}: {err}")
        if e.code in (429, 503) and attempt < 3:
            time.sleep(4 * attempt)
            return generate(prompt, out_path, attempt + 1)
        return False
    except Exception as e:
        print(f"  ✗ {type(e).__name__}: {e}")
        return False

    parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    for p in parts:
        inline = p.get("inlineData") or p.get("inline_data")
        if inline and inline.get("data"):
            out_path.write_bytes(base64.b64decode(inline["data"]))
            print(f"  ✓ {out_path.name} ({out_path.stat().st_size // 1024} KB)")
            return True
    print(f"  ✗ no image in response: {json.dumps(data)[:300]}")
    return False

ok = fail = 0
for name, prompt in PROMPTS.items():
    out = OUT_DIR / f"{name}.png"
    if out.exists() and out.stat().st_size > 5000:
        print(f"• {name} — skip (exists)")
        ok += 1
        continue
    print(f"• {name} …")
    if generate(prompt, out):
        ok += 1
    else:
        fail += 1
    time.sleep(0.4)

print(f"\nDone: {ok} ok, {fail} failed → {OUT_DIR}")
sys.exit(0 if fail == 0 else 1)
