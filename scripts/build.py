"""Draws every graphic in this profile. Standard library plus the `gh` CLI.

    python3 scripts/build.py

Text is drawn as outlines from glyphs.json (Inter and Inter Tight, SIL OFL), so it
looks the same on every device. Edit the lists below to change the content.
"""
import html
import json
import math
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"
LOGIN = "Pushkar-Shahi"
FONTS = json.loads((ROOT / "scripts" / "glyphs.json").read_text())

BG, PAPER, MUTED, DEEP = "#17144A", "#F2F3FF", "#B4B2EA", "#282473"
# each solid is (top face, left face, right face)
COBALT = ("#7D93FF", "#3D5AFE", "#2A3CB8")
MARIGOLD = ("#FFD477", "#FFB020", "#BD7C0C")
MINT = ("#8CF0D0", "#35D0A5", "#1B8F70")
CORAL = ("#FFB4A8", "#FF7A68", "#B94A3C")
SLATE = ("#3A358F", "#2B2776", "#201D5C")

CARDS = [
    ("hackradar", "HackRadar", "Finds hackathons across platforms and keeps track of every deadline.",
     "React, Hono, Cloudflare Workers, D1", COBALT),
    ("qrdrop", "QRDrop", "Scan a QR code to send files browser to browser. Nothing touches a server.",
     "TypeScript, React, WebRTC", MINT),
    ("reconai", "ReconAI", "Matches bank statements to the ledger with rules, then a Gemini agent checks the rest.",
     "Python, FastAPI, React, Gemini", MARIGOLD),
    ("clubs", "Club Tracker", "Multi-campus clubs with rotating QR check-in, rubric scoring and verifiable certificates.",
     "FastAPI, PostgreSQL, JavaScript", CORAL),
    ("bgremover", "BG Remover", "Removes backgrounds from images and video, on the GPU when one is available.",
     "Python, rembg, OpenCV, FFmpeg", MINT),
    ("integrity", "Integrity Engine", "Anchors config file hashes on a local blockchain and flags tampering as it happens.",
     "Python, Solidity, Hardhat, Streamlit", COBALT),
]

# voxels (x, y, z) that make each card's small sculpture
SCULPTURES = {
    "hackradar": [(x, y, 0) for x in range(3) for y in range(3) if (x, y) != (1, 1)] + [(1, 1, 0), (1, 1, 1), (1, 1, 2)],
    "qrdrop": [(0, 0, 0), (1, 0, 0), (0, 1, 0), (2, 0, 0), (3, 1, 0), (1, 2, 0), (3, 3, 0), (2, 3, 0), (0, 3, 0), (2, 2, 1)],
    "reconai": [(0, 1, 0), (0, 1, 1), (0, 1, 2), (2, 1, 0), (2, 1, 1), (2, 1, 2), (1, 1, 2)],
    "clubs": [(0, 0, 0), (2, 0, 0), (2, 0, 1), (0, 2, 0), (0, 2, 1), (2, 2, 0), (1, 1, 0), (1, 1, 1), (1, 1, 2)],
    "bgremover": [(x, y, 0) for x in range(3) for y in range(3) if (x, y) != (1, 1)] + [(1, 1, 2)],
    "integrity": [(0, 2, 0), (1, 2, 0), (1, 1, 0), (1, 1, 1), (2, 1, 1), (2, 0, 1), (2, 0, 2)],
}

TOOLS = [
    ("Languages", MARIGOLD, ["Python", "JavaScript", "TypeScript", "HTML", "CSS"]),
    ("Machine learning", MINT, ["PyTorch", "OpenCV", "MLflow", "Hugging Face"]),
    ("Local AI", CORAL, ["Ollama", "n8n"]),
    ("Web and data", COBALT, ["FastAPI", "React", "Node.js", "Tailwind", "PostgreSQL", "Supabase"]),
    ("Infrastructure", ("#E4E5FF", "#C4C6FF", "#8D90D6"), ["Docker", "Kubernetes", "Linux", "Cloudflare", "GitHub Actions"]),
    ("Everyday tools", ("#FFFFFF", "#F2F3FF", "#B9BBD8"), ["Git", "Figma", "VS Code"]),
]

BUTTONS = [("portfolio", "Portfolio", MARIGOLD), ("linkedin", "LinkedIn", COBALT),
           ("email", "Email", MINT), ("x", "X", ("#E4E5FF", "#C4C6FF", "#8D90D6"))]

# 5 x 7 pixel letters for the name
VOXEL = {
    "P": "1111. 1...1 1...1 1111. 1.... 1.... 1....",
    "S": ".1111 1.... 1.... .111. ....1 ....1 1111.",
    "u": "..... ..... 1...1 1...1 1...1 1..11 .11.1",
    "s": "..... ..... .1111 1.... .111. ....1 1111.",
    "h": "1.... 1.... 1.11. 11..1 1...1 1...1 1...1",
    "k": "1... 1... 1..1 1.1. 11.. 1.1. 1..1",
    "a": "..... ..... .111. ....1 .1111 1...1 .1111",
    "r": ".... .... 1.11 11.. 1... 1... 1...",
    "i": ".1. ... 11. .1. .1. .1. 111",
}


def n(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


def poly(points, fill, extra=""):
    pts = " ".join(f"{n(x)},{n(y)}" for x, y in points)
    return f'<polygon points="{pts}" fill="{fill}"{extra}/>'


class Svg:
    def __init__(self, w, h, label):
        self.w, self.h, self.label = w, h, label
        self.parts, self.defs, self.css = [], {}, ""

    def add(self, *s):
        self.parts.extend(s)

    @staticmethod
    def width(s, size, font="text"):
        f = FONTS[font]
        return sum(f["glyphs"][c][0] for c in s) * size / f["upm"]

    def text(self, x, y, s, size, fill=PAPER, font="text", anchor="start"):
        f = FONTS[font]
        x -= {"start": 0, "middle": 0.5, "end": 1}[anchor] * self.width(s, size, font)
        scale = size / f["upm"]
        adv, uses = 0, []
        for c in s:
            width, d = f["glyphs"][c]
            if d:
                gid = f"{font[0]}{ord(c)}"
                self.defs[gid] = d
                uses.append(f'<use href="#{gid}" x="{adv}"/>')
            adv += width
        self.add(f'<g fill="{fill}" transform="translate({n(x)} {n(y)}) scale({scale:.5f} {-scale:.5f})">{"".join(uses)}</g>')

    def wrap(self, s, size, width, font="text"):
        lines = [""]
        for word in s.split():
            trial = f"{lines[-1]} {word}".strip()
            if lines[-1] and self.width(trial, size, font) > width:
                lines.append(word)
            else:
                lines[-1] = trial
        return lines

    def box(self, x, y, a, h, colors):
        """Isometric block. (x, y) is the centre of its footprint, a the half width."""
        b = a / 2
        top, left, right = colors
        self.add(
            poly([(x - a, y - h), (x, y + b - h), (x, y + b), (x - a, y)], left),
            poly([(x, y + b - h), (x + a, y - h), (x + a, y), (x, y + b)], right),
            poly([(x, y - b - h), (x + a, y - h), (x, y + b - h), (x - a, y - h)], top),
        )

    def key(self, x, y, w, h, d, colors):
        """Raised key seen from slightly above and to the right."""
        top, front, side = colors
        self.add(
            poly([(x, y), (x + d, y - d), (x + w + d, y - d), (x + w, y)], top),
            poly([(x + w, y), (x + w + d, y - d), (x + w + d, y + h - d), (x + w, y + h)], side),
            f'<rect x="{n(x)}" y="{n(y)}" width="{n(w)}" height="{n(h)}" fill="{front}"/>',
        )

    def save(self, name):
        glyphs = "".join(
            f'<path id="{gid}" d="{d}"/>' for gid, d in sorted(self.defs.items()))
        (OUT / name).write_text(
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" height="{self.h}" '
            f'role="img" aria-label="{html.escape(self.label)}">'
            + (f"<style>{self.css}</style>" if self.css else "")
            + f"<defs>{glyphs}</defs>" + "".join(self.parts) + "</svg>\n")


def panel(svg):
    svg.add(f'<rect width="{svg.w}" height="{svg.h}" rx="14" fill="{BG}"/>')


# ---------------------------------------------------------------- hero

def voxel_word(svg, word, x, y, cell):
    cells, col = set(), 0
    for ch in word:
        if ch == " ":
            col += 3
            continue
        rows = VOXEL[ch].split()
        cells |= {(col + c, r) for r, row in enumerate(rows) for c, v in enumerate(row) if v == "1"}
        col += len(rows[0]) + 1
    d = cell * 0.65
    for c, r in sorted(cells):
        px, py = x + c * cell, y + r * cell
        if (c, r - 1) not in cells:
            svg.add(poly([(px, py), (px + d, py - d), (px + cell + d, py - d), (px + cell, py)], COBALT[0]))
        if (c + 1, r) not in cells:
            svg.add(poly([(px + cell, py), (px + cell + d, py - d), (px + cell + d, py + cell - d), (px + cell, py + cell)], COBALT[2]))
    for c, r in sorted(cells):
        svg.add(f'<rect x="{n(x + c * cell)}" y="{n(y + r * cell)}" width="{n(cell)}" height="{n(cell)}" '
                f'fill="{PAPER}" stroke="#C9CCF5" stroke-width="0.8"/>')


def icosahedron(svg, cx, cy, radius, frames=12, seconds=3.2):
    """A turning solid. Spun about a five-fold axis, so 72 degrees loops seamlessly."""
    lat, k = math.atan(0.5), math.cos(math.atan(0.5))
    verts = [(0, 1, 0), (0, -1, 0)]
    for i in range(5):
        for sign, offset in ((1, 0), (-1, 36)):
            a = math.radians(i * 72 + offset)
            verts.append((k * math.cos(a), sign * math.sin(lat), k * math.sin(a)))
    edge = min(math.dist(verts[0], v) for v in verts[1:]) * 1.01
    faces = [(i, j, m) for i in range(12) for j in range(i + 1, 12) for m in range(j + 1, 12)
             if max(math.dist(verts[i], verts[j]), math.dist(verts[j], verts[m]), math.dist(verts[i], verts[m])) <= edge]
    assert len(faces) == 20
    tilt, light = 0.42, (-0.5, 0.65, 0.57)

    def turn(v, a):
        x, y, z = v
        x, z = x * math.cos(a) + z * math.sin(a), -x * math.sin(a) + z * math.cos(a)
        return x, y * math.cos(tilt) - z * math.sin(tilt), y * math.sin(tilt) + z * math.cos(tilt)

    def shade(t):
        lo, mid, hi = (22, 110, 92), (53, 208, 165), (214, 255, 241)
        p, q, t = (lo, mid, t * 2) if t < 0.5 else (mid, hi, t * 2 - 1)
        return "#" + "".join(f"{round(p[i] + (q[i] - p[i]) * t):02X}" for i in range(3))

    states = []
    for f in range(frames + 1):
        spun = [turn(v, math.radians(72) * f / frames) for v in verts]
        state = []
        for face in faces:
            centre = [sum(spun[i][axis] for i in face) / 3 for axis in range(3)]
            length = math.hypot(*centre)
            normal = [c / length for c in centre]
            lit = max(0, min(1, sum(a * b for a, b in zip(normal, light)) * 0.62 + 0.4))
            pts = " ".join(f"{n(cx + radius * spun[i][0])},{n(cy - radius * spun[i][1])}" for i in face)
            state.append((pts, shade(lit), "visible" if normal[2] > 0 else "hidden"))
        states.append(state)

    flips = ";".join(["0"] + [f"{(f - 0.5) / frames:.5f}" for f in range(1, frames + 1)])
    still, moving = [], []
    for i in range(20):
        pts, fill, vis = states[0][i]
        if vis == "visible":
            still.append(f'<polygon points="{pts}" fill="{fill}"/>')
        series = [s[i] for s in states]
        if all(s[2] == "hidden" for s in series):
            continue
        anim = "".join(
            f'<animate attributeName="{attr}" dur="{seconds}s" repeatCount="indefinite"{mode} values="{";".join(s[col] for s in series)}"/>'
            for col, attr, mode in ((0, "points", ""), (1, "fill", ""), (2, "visibility", f' calcMode="discrete" keyTimes="{flips}"')))
        moving.append(f'<polygon points="{pts}" fill="{fill}" visibility="{vis}">{anim}</polygon>')
    svg.add(f'<g class="move">{"".join(moving)}</g><g class="still">{"".join(still)}</g>')


def hero(wide):
    w, h = (880, 450) if wide else (600, 650)
    svg = Svg(w, h, "Pushkar Shahi, MLOps and AI systems engineer. A model moves through data, train, register, deploy and monitor.")
    svg.css = (".still{display:none}.flow{animation:flow 1.2s linear infinite}@keyframes flow{to{stroke-dashoffset:-24}}"
               "@media (prefers-reduced-motion:reduce){.move{display:none}.still{display:inline}.flow{animation:none}}")
    panel(svg)
    # floor grid in the same 2:1 isometric as every block
    lines = "".join(f"M{x} 0l{2 * h} {h}M{x} 0l{-2 * h} {h}" for x in range(-2 * h, w + 2 * h, 88))
    svg.add(f'<clipPath id="c"><rect width="{w}" height="{h}" rx="14"/></clipPath>'
            f'<path clip-path="url(#c)" d="{lines}" stroke="{DEEP}" stroke-width="1" fill="none" opacity="0.55"/>')

    if wide:
        voxel_word(svg, "Pushkar Shahi", 42, 52, 9.8)
        svg.text(42, 166, "MLOps and AI systems engineer", 30, font="display")
        svg.text(42, 198, "B.Tech student at Mirai School of Technology, India", 18, MUTED)
        xs, ys, a, label = [96, 268, 440, 612, 784], [302, 378], 44, 18
    else:
        voxel_word(svg, "Pushkar", 38, 52, 12.8)
        voxel_word(svg, "Shahi", 38, 164, 12.8)
        svg.text(38, 303, "MLOps and AI systems engineer", 33, font="display")
        svg.text(38, 345, "B.Tech student at Mirai School", 27, MUTED)
        svg.text(38, 379, "of Technology, India", 27, MUTED)
        xs, ys, a, label = [66, 183, 300, 417, 534], [496, 555], 36, 25
    points = [(x, ys[i % 2]) for i, x in enumerate(xs)]
    track = "M" + " L".join(f"{x} {y}" for x, y in points)
    svg.add(f'<path d="{track}" fill="none" stroke="#100E38" stroke-width="{a * 0.55}" stroke-linejoin="round" transform="translate(0 7)"/>',
            f'<path d="{track}" fill="none" stroke="#332E8C" stroke-width="{a * 0.55}" stroke-linejoin="round"/>',
            f'<path class="flow" d="{track}" fill="none" stroke="{MUTED}" stroke-width="2.5" stroke-dasharray="8 16"/>')
    # the model travelling along the line; it passes behind each station
    s = a * 0.26
    packet = Svg(0, 0, "")
    packet.box(0, 0, s, s * 1.15, MARIGOLD)
    svg.add(f'<g class="move">{"".join(packet.parts)}<animateMotion dur="9s" repeatCount="indefinite" path="{track}"/></g>',
            f'<g class="still" transform="translate({(xs[0] + xs[1]) / 2} {(ys[0] + ys[1]) / 2})">{"".join(packet.parts)}</g>')

    u = a / 44
    for i, name in sorted(enumerate(["Data", "Train", "Register", "Deploy", "Monitor"]), key=lambda p: points[p[0]][1]):
        x, y = points[i]
        svg.box(x, y, a, 8 * u, SLATE)
        base = y - 8 * u
        if name == "Data":
            for level in range(3):
                svg.box(x, base - level * 17 * u, a * 0.62, 11 * u, COBALT)
        elif name == "Train":
            svg.box(x, base, a * 0.46, 10 * u, MINT)
            icosahedron(svg, x, base - 62 * u, 39 * u)
        elif name == "Register":
            q = a * 0.3
            for dx, dy, tall in ((0, -q / 2, 24), (-q, 0, 38), (q, 0, 16), (0, q / 2, 28)):
                svg.box(x + dx, base + dy, q * 0.9, tall * u, MARIGOLD)
        elif name == "Deploy":
            for level in range(4):
                svg.box(x, base - level * 17 * u, a * 0.5, 13 * u, MINT if level == 3 else COBALT)
        else:
            q = a * 0.26
            for k, tall in enumerate((22, 46, 33)):
                svg.box(x + (k - 1) * q * 1.2, base + (k - 1) * q * 0.6, q, tall * u, CORAL)
        svg.text(x, y + a / 2 + label + 6, name, label, font="display", anchor="middle")
    svg.save(f"hero-{'wide' if wide else 'compact'}.svg")


# ---------------------------------------------------------------- cards, buttons, tools

def card(slug, title, blurb, tech, colors):
    svg = Svg(400, 258, f"{title}. {blurb} Built with {tech}.")
    d, w, h = 11, 387, 231
    svg.add(poly([(2, d + 1), (d + 2, 1), (w + d + 1, 1), (w + 1, d + 1)], colors[0]),
            poly([(w + 1, d + 1), (w + d + 1, 1), (w + d + 1, h), (w + 1, h + d + 1)], colors[2]),
            f'<rect x="1" y="{d + 1}" width="{w}" height="{h}" fill="{BG}" stroke="{colors[1]}" stroke-width="2"/>')
    voxels = SCULPTURES[slug]
    a = 10.5
    place = [((x - y) * a, (x + y) * a / 2 - z * a, x + y, z, x) for x, y, z in voxels]
    left, right = min(p[0] for p in place) - a, max(p[0] for p in place) + a
    ox, oy = 368 - right, 52 - (min(p[1] - a * 1.5 for p in place) + max(p[1] + a / 2 for p in place)) / 2 + 12
    for sx, sy, _, _, _ in sorted(place, key=lambda p: (p[3], p[2], p[4])):
        svg.box(ox + sx, oy + sy, a, a, colors)
    room = ox + left - 36
    size = 30
    while svg.width(title, size, "display") > room:
        size -= 1
    svg.text(24, 62, title, size, font="display")
    lines = svg.wrap(blurb, 19, 344)
    assert len(lines) <= 3, f"{slug}: description is too long"
    for i, line in enumerate(lines):
        svg.text(24, 120 + i * 28, line, 19)
    svg.text(24, 220, tech, 16, colors[0])
    svg.save(f"card-{slug}.svg")


def button(slug, label, colors):
    svg = Svg(144, 56, label)
    svg.key(3, 11, 130, 40, 8, colors)
    svg.text(68, 38, label, 19, "#FFFFFF" if colors is COBALT else BG, "display", "middle")
    svg.save(f"btn-{slug}.svg")


def toolbox(wide):
    w = 880 if wide else 600
    size, kh, d, gap, pad = (17, 40, 8, 10, 1.3) if wide else (25, 54, 9, 13, 1.5)
    left = 208 if wide else 26
    placed, y = [], 30
    for group, colors, names in TOOLS:
        if not wide:
            placed.append(("label", 26, y + 26, group))
            y += 50
        else:
            placed.append(("label", 28, y + d + kh / 2 + 6, group))
        x = left
        for name in names:
            kw = Svg.width(name, size, "display") + size * pad
            if x + kw + d > w - 20:
                x, y = left, y + kh + d + gap
            placed.append(("key", x, y + d, name, kw, colors))
            x += kw + d + gap
        y += kh + d + (20 if wide else 26)
    svg = Svg(w, int(y + 14), "Toolbox. " + ". ".join(f"{g}: {', '.join(t)}" for g, _, t in TOOLS) + ".")
    panel(svg)
    for item in placed:
        if item[0] == "label":
            svg.text(item[1], item[2], item[3], 18 if wide else 26, MUTED)
        else:
            _, x, ky, name, kw, colors = item
            svg.key(x, ky, kw, kh, d, colors)
            svg.text(x + kw / 2, ky + kh / 2 + size * 0.36, name, size,
                     "#FFFFFF" if colors is COBALT else BG, "display", "middle")
    svg.save(f"toolbox-{'wide' if wide else 'compact'}.svg")


# ---------------------------------------------------------------- live data

def gh(*args):
    return json.loads(subprocess.run(["gh", "api", *args], check=True, capture_output=True, text=True).stdout)


def fetch():
    query = """query($login:String!){user(login:$login){
      contributionsCollection{contributionCalendar{totalContributions
        weeks{contributionDays{date weekday contributionCount contributionLevel}}}}
      repositories(first:100,ownerAffiliations:OWNER,isFork:false,privacy:PUBLIC){nodes{name
        languages(first:10,orderBy:{field:SIZE,direction:DESC}){edges{size node{name}}}}}}}"""
    user = gh("graphql", "-f", f"query={query}", "-f", f"login={LOGIN}")["data"]["user"]
    prs = gh("-X", "GET", "search/issues", "-f", f"q=author:{LOGIN} is:pull-request is:merged is:public -user:{LOGIN}",
             "-f", "per_page=100")["items"]
    merged = []
    for pr in prs:
        repo = pr["repository_url"].split("/repos/")[1]
        if "practice" not in repo.lower():
            merged.append({"repo": repo, "title": pr["title"], "url": pr["html_url"],
                           "number": pr["number"], "when": pr["pull_request"]["merged_at"]})
    sizes = {}
    for repo in user["repositories"]["nodes"]:
        if repo["name"] != LOGIN:
            for edge in repo["languages"]["edges"]:
                sizes[edge["node"]["name"]] = sizes.get(edge["node"]["name"], 0) + edge["size"]
    total = sum(sizes.values()) or 1
    languages = [(name, size / total) for name, size in sorted(sizes.items(), key=lambda p: -p[1])[:5]]
    calendar = user["contributionsCollection"]["contributionCalendar"]
    return calendar, sorted(merged, key=lambda p: p["when"], reverse=True), languages


def longest_streak(days):
    best = run = 0
    for day in days:
        run = run + 1 if day["contributionCount"] else 0
        best = max(best, run)
    return best


LEVELS = {"NONE": ("#2F2A7C", "#241F63", "#1D1952"), "FIRST_QUARTILE": COBALT,
          "SECOND_QUARTILE": ("#B7C3FF", "#8296FF", "#5566C4"), "THIRD_QUARTILE": MINT, "FOURTH_QUARTILE": MARIGOLD}


def skyline(svg, weeks, ox, oy, a, tallest, peak):
    cells = [(w + d["weekday"], w, d["weekday"], d) for w, week in enumerate(weeks) for d in week["contributionDays"]]
    for _, w, row, day in sorted(cells, key=lambda c: (c[0], c[1])):
        count = day["contributionCount"]
        height = 5 + tallest * math.sqrt(count / peak) if count else 3
        svg.box(ox + (w - row) * a, oy + (w + row + 1) * a / 2, a * 0.92, height, LEVELS[day["contributionLevel"]])


def graph(wide, calendar, merged, languages):
    days = [d for w in calendar["weeks"] for d in w["contributionDays"]]
    peak = max(d["contributionCount"] for d in days) or 1
    stats = [(f"{calendar['totalContributions']:,}", "contributions in the past year", MARIGOLD[1]),
             (str(longest_streak(days)), "days in the longest streak", MINT[1]),
             (str(len(merged)), "pull requests merged upstream", COBALT[0])]
    weeks = calendar["weeks"] if wide else calendar["weeks"][-26:]
    w, h = (880, 580) if wide else (600, 1000)
    svg = Svg(w, h, "3D skyline of GitHub contributions. " + ". ".join(f"{v} {t}" for v, t, _ in stats) + ".")
    panel(svg)

    def legend(right, y, size):
        x = right - svg.width("Less", size) - svg.width("More", size) - 22 - 27 * len(LEVELS) + 6
        svg.text(x, y, "Less", size, MUTED)
        x += svg.width("Less", size) + 22
        for colors in LEVELS.values():
            svg.box(x, y - 5, 11, 7, colors)
            x += 27
        svg.text(x - 6, y, "More", size, MUTED)

    def bars(x, y, name_w, bar_w, row, size):
        top = languages[0][1] if languages else 1
        for i, (name, share) in enumerate(languages):
            yy = y + i * row
            length = max(6, bar_w * share / top)
            svg.text(x, yy + size * 0.95, name, size)
            svg.key(x + name_w, yy, length, size * 1.15, 6, (COBALT, MINT, MARIGOLD, CORAL, LEVELS["SECOND_QUARTILE"])[i])
            svg.text(x + name_w + length + 16, yy + size * 0.95, f"{share:.0%}", size, MUTED)

    if wide:
        skyline(svg, weeks, 40 + 7 * 13.4, 112, 13.4, 84, peak)
        for i, (value, label, color) in enumerate(stats):
            y = 70 + i * 74
            svg.text(846, y, value, 44, color, "display", "end")
            svg.text(846, y + 24, label, 16, MUTED, anchor="end")
        svg.text(32, 396, "Code in my public repositories", 18, font="display")
        bars(32, 418, 104, 150, 30, 15)
        legend(848, 544, 15)
    else:
        for i, (value, label, color) in enumerate(stats):
            y = 72 + i * 74
            svg.text(150, y, value, 54, color, "display", "end")
            svg.text(168, y - 8, label, 25, MUTED)
        svg.text(28, 306, "Last 26 weeks", 30, font="display")
        skyline(svg, weeks, 28 + 7 * 16.5, 372, 16.5, 80, peak)
        legend(572, 410, 22)
        svg.text(28, 730, "Code in my public repositories", 30, font="display")
        bars(28, 762, 160, 280, 45, 24)
    svg.save(f"graph-{'wide' if wide else 'compact'}.svg")


def stl(calendar):
    """The same year as an ASCII STL, which GitHub shows as a model you can rotate."""
    peak = max(d["contributionCount"] for w in calendar["weeks"] for d in w["contributionDays"]) or 1
    faces = [((0, 0, -1), (0, 3, 2, 1)), ((0, 0, 1), (4, 5, 6, 7)), ((0, -1, 0), (0, 1, 5, 4)),
             ((1, 0, 0), (1, 2, 6, 5)), ((0, 1, 0), (2, 3, 7, 6)), ((-1, 0, 0), (3, 0, 4, 7))]
    out = ["solid contributions"]

    def cuboid(x0, y0, z0, x1, y1, z1):
        v = [(x, y, z) for z in (z0, z1) for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
        for normal, (a, b, c, d) in faces:
            for tri in ((a, b, c), (a, c, d)):
                out.append("facet normal %d %d %d\nouter loop" % normal)
                out.extend("vertex " + " ".join(n(q) for q in v[i]) for i in tri)
                out.append("endloop\nendfacet")

    cuboid(-1, -1, -1.5, len(calendar["weeks"]) + 1, 8, 0)
    for w, week in enumerate(calendar["weeks"]):
        for day in week["contributionDays"]:
            if day["contributionCount"]:
                y = 6 - day["weekday"]
                cuboid(w + 0.08, y + 0.08, 0, w + 0.92, y + 0.92, round(0.6 + 9 * math.sqrt(day["contributionCount"] / peak), 1))
    out.append("endsolid contributions")
    (OUT / "skyline.stl").write_text("\n".join(out) + "\n")


def upstream_markdown(merged):
    def safe(s):
        return re.sub(r"([\\`*_\[\]|~])", r"\\\1", html.escape(s, quote=False))

    repos = {}
    for pr in merged:
        repos.setdefault(pr["repo"], []).append(pr)
    mine = f"author%3A{LOGIN}+is%3Apr+is%3Amerged"
    lines = [f"[{len(merged)} pull requests merged](https://github.com/search?q={mine}+-user%3A{LOGIN}&type=pullrequests) "
             f"into {len(repos)} open-source projects that other people maintain.", ""]
    for repo, prs in list(repos.items())[:10]:
        latest = prs[0]
        lines.append(f"- **[{repo}](https://github.com/{repo}/pulls?q={mine})** ({len(prs)} merged)<br />"
                     f"[{safe(latest['title'])}]({latest['url']})")
    return "\n".join(lines)


def update_readme(merged):
    path = ROOT / "README.md"
    start, end = "<!-- upstream:start -->", "<!-- upstream:end -->"
    text = path.read_text()
    assert start in text and end in text, "README.md lost its upstream markers"
    head, rest = text.split(start, 1)
    tail = rest.split(end, 1)[1]
    path.write_text(f"{head}{start}\n{upstream_markdown(merged)}\n{end}{tail}")


def main():
    calendar, merged, languages = fetch()  # fetch first, so an API failure changes nothing
    OUT.mkdir(exist_ok=True)
    for wide in (True, False):
        hero(wide)
        toolbox(wide)
        graph(wide, calendar, merged, languages)
    for c in CARDS:
        card(*c)
    for b in BUTTONS:
        button(*b)
    stl(calendar)
    update_readme(merged)


if __name__ == "__main__":
    main()
