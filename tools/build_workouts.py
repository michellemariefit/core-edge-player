"""
Build data/core.json from the Core Edge workout PDF.

    pip install pymupdf pillow
    python tools/build_workouts.py

Put "YAE The Core Edge Workouts.pdf" from Dropbox (PRODUCTS & PROGRAMS / The Core Edge)
in tools/pdf/core.pdf (ignored by git). It is one PDF with six workouts of three exercises.
The photo next to each exercise is saved as images/<video id>-pdf.webp and used until
grab_frames.py makes the start and end pair.

Writes data/core.json in the same shape as the YAE player's data file: one group ("core")
with six workouts, each one circuit of three exercises.
"""
import io, json, os, re, sys
import pymupdf
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF = os.path.join(ROOT, "tools", "pdf", "core.pdf")
IMAGES = os.path.join(ROOT, "images")
OUT = os.path.join(ROOT, "data", "core.json")
YT = re.compile(r"youtu\.be/([A-Za-z0-9_-]{11})")

# Michelle's lesson video, unlisted on YouTube, shown as "Watch Michelle explain this". Empty until she sends it.
GROUP_VIDEO = ""
# Rounds per workout. The PDF says 3 exercises, 15-20 reps each; rounds are Michelle's call.
ROUNDS = 2
REST_SECONDS = 30

GROUP = {
    "id": "core", "name": "The Core Edge",
    "intro": "Six core circuits. Go in order, 1 to 6, then start again.",
    "when": ("Off-season: 2 or 3 times a week. In season: 1 or 2. Add it to a strength or balance workout, "
             "do it on an off day before mobility or stretching, or after a running day. "
             "Never right before a practice or a game."),
}


def yt(uri):
    m = YT.search(uri or "")
    return m.group(1) if m else None


def parse():
    doc = pymupdf.open(PDF)
    workouts, header, cur_w, cur_e = [], [], None, None
    for page in doc:
        links = [(pymupdf.Rect(l["from"]), yt(l.get("uri"))) for l in page.get_links() if yt(l.get("uri"))]
        images = [(pymupdf.Rect(i["bbox"]), i["xref"]) for i in page.get_image_info(xrefs=True) if i["xref"]]
        for b in sorted(page.get_text("blocks"), key=lambda b: (round(b[1]), b[0])):
            if b[6] != 0:
                continue
            r = pymupdf.Rect(b[:4])
            lines = [re.sub(r"[ \t]+", " ", x).strip() for x in b[4].split("\n")]
            lines = [x for x in lines if x]
            if not lines or lines[0].startswith("T H E") or lines[0].startswith("The Youth Athlete Edge ·"):
                continue
            m = re.fullmatch(r"W\s*O\s*R\s*K\s*O\s*U\s*T\s*(\d+)", lines[0])
            if m:
                cur_w = {"n": int(m.group(1)), "exercises": []}
                workouts.append(cur_w)
                cur_e = None
                continue
            if cur_w is None:
                header.append(" ".join(lines))
                continue
            vids = [v for (lr, v) in links if lr.intersects(r)]
            if re.fullmatch(r"\d", lines[0]):
                cur_e = {"code": lines[0], "name": " ".join(lines[1:]), "video": vids[0] if vids else None, "note": "", "y": r.y0}
                cur_w["exercises"].append(cur_e)
                continue
            if cur_e and not lines[0].startswith("▶"):
                cur_e["note"] = (cur_e["note"] + " " + " ".join(lines)).strip()
        for w in workouts:
            for ex in w["exercises"]:
                if ex.get("photo") or ex.get("page_done"):
                    continue
                best = min(images, key=lambda im: abs(im[0].y0 - ex["y"] + 15), default=None)
                if best and abs(best[0].y0 - ex["y"]) < 60 and ex["video"]:
                    out = os.path.join(IMAGES, f"{ex['video']}-pdf.webp")
                    if not os.path.exists(out):
                        raw = doc.extract_image(best[1])["image"]
                        im = Image.open(io.BytesIO(raw)).convert("RGB")
                        im.thumbnail((720, 720))
                        im.save(out, "WEBP", quality=82)
                    ex["photo"] = "images/" + os.path.basename(out)
                ex["page_done"] = True
    return header, workouts


def main():
    os.makedirs(IMAGES, exist_ok=True)
    header, workouts = parse()
    text = " ".join(header)
    how = re.search(r"How to do it:\s*(.*?)(?:When to do it:|$)", text, re.S)
    how = re.sub(r"\s+", " ", how.group(1)).strip(" ·") if how else ""
    existing = {}
    if os.path.exists(OUT):
        for w in json.load(open(OUT))["groups"][0]["workouts"]:
            for b in w["blocks"]:
                for e in b["exercises"]:
                    if e.get("startPhoto"):
                        existing[e["video"]] = (e["startPhoto"], e["endPhoto"])
    group = {**GROUP, "video": GROUP_VIDEO, "workouts": []}
    n = 0
    for w in workouts:
        exs = []
        for e in w["exercises"]:
            e = {k: v for k, v in e.items() if k not in ("y", "page_done")}
            e["note"] = re.sub(r"\s+", " ", e["note"])
            if e["video"] in existing:
                e["startPhoto"], e["endPhoto"] = existing[e["video"]]
            exs.append(e); n += 1
        wid = f"core-{w['n']}"
        group["workouts"].append({
            "id": wid, "name": f"Core Workout {w['n']}", "group": "core",
            "how": how, "when": "", "tip": "",
            "sets": ROUNDS, "setsLabel": f"{ROUNDS} rounds", "reps": "15-20",
            "restSeconds": REST_SECONDS, "restLabel": f"{REST_SECONDS}s",
            "circuit": True, "blocks": [{"label": "Circuit", "exercises": exs}]})
        print(wid, "·", " / ".join(f"{x['name']} ({x['video']})" for x in exs))
    data = {"program": "CORE", "name": "The Core Edge", "groups": [group]}
    json.dump(data, open(OUT, "w"), indent=1, ensure_ascii=False)
    print(f"\n{n} exercise slots -> {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    sys.exit(main())
