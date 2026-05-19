#!/usr/bin/env python3
"""Generate Psweep landing images with Gemini 2.5 Flash Image (nano-banana).

Realistic / photorealistic variant. Reuses the same filenames as the cartoon
set so the HTML doesn't need updating.
"""
import os, sys, json, base64, pathlib, urllib.request, urllib.error, time

API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    sys.exit("GEMINI_API_KEY not set")

MODEL = "gemini-2.5-flash-image"
ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"

OUT_DIR = pathlib.Path(__file__).parent.parent / "assets" / "generated"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Style brief — keep cohesive across all images. PHOTOREALISTIC variant.
STYLE = (
    "Photorealistic, high quality product photography, natural soft daylight, "
    "shallow depth of field, clean modern Argentine home aesthetic, "
    "warm neutral tones with subtle teal accents, premium commercial feel. "
    "NOT illustration, NOT cartoon, NOT 3D render. Real-world camera look, "
    "as if shot on a Sony A7 with 50mm prime lens. No text overlays in image."
)

PROMPTS = {
    "hero-product": (
        "Product photography of a white plastic bottle of pet cleaning powder, "
        "matte finish, teal label with a minimal paw-print logo and the word 'Psweep' subtle, "
        "yellow screw cap. Centered on a plain off-white seamless studio background (#F7F7F5). "
        "Soft top-left lighting, gentle drop shadow under the bottle. Square framing. "
        f"{STYLE}"
    ),
    "step-1": (
        "Close-up overhead photograph: a hand sprinkling fine white absorbent powder "
        "out of an open teal bottle onto a small puddle of yellow-tinted liquid on a "
        "light grey ceramic tile floor. The powder is mid-air, caught in motion. "
        "Modern Argentine home setting, slightly blurred wooden floor in background. "
        f"{STYLE}"
    ),
    "step-2": (
        "Close-up macro photograph of a tile floor where a small puddle has been transformed "
        "into solid pale-white gel granules and clumps — the absorbent material has reacted. "
        "Light grey ceramic tile, soft natural daylight from a window, no liquid visible anymore. "
        f"{STYLE}"
    ),
    "step-3": (
        "Photograph of a wooden broom and a metal dustpan on a clean ceramic tile floor, "
        "sweeping pale-white solidified gel granules into the dustpan. Action shot from "
        "side-low angle, slight motion blur on the broom bristles. Modern home interior. "
        f"{STYLE}"
    ),
    "step-4": (
        "Photograph of a friendly golden retriever and a calm grey cat sitting together "
        "on a perfectly clean dry tile floor in a sunlit modern living room. "
        "Soft window light from the left, warm and inviting. Floor is spotless. "
        f"{STYLE}"
    ),
    "b2b-shelf": (
        "Photograph of a modern pet shop retail shelf with multiple identical bottles "
        "of Psweep (teal label, yellow cap) arranged in neat rows. Wooden shelving, "
        "warm overhead store lighting, a small price tag visible. Crisp focus on front row, "
        "soft bokeh in background. Wide horizontal framing. "
        f"{STYLE}"
    ),
    "demo-poster": (
        "Photographic triptych on a single horizontal image, 3 panels divided by thin white gaps: "
        "LEFT panel — a small yellow puddle on a grey tile floor with a curious dog in the background, "
        "MIDDLE panel — a hand sprinkling white powder onto that same puddle, "
        "RIGHT panel — same tile floor now completely dry and clean with a happy dog sitting on it. "
        "Cohesive lighting and tile across all 3 panels. Wide cinematic 16:9 framing. "
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
