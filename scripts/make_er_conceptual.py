"""Draw the conceptual entity-relationship diagram as docs/er-conceptual.svg.

    python scripts/make_er_conceptual.py

Notation: entities as rectangles with their attributes (key underlined),
relationships as diamonds, cardinalities 1 and N on the lines, and the
attributes of a relationship written next to its diamond.
Standard library only. Positions are fixed lists, edit them if the model changes.
"""
import os

W_ENTITY, HEADER, ROW = 200, 30, 20
DW, DH = 58, 30  # half width and half height of a diamond

# entity -> (x, y, key attributes, other attributes)
ENTITIES = {
    "PERSON": (40, 80, ["person_id"], ["name"]),
    "SONG ENTRY": (480, 80, ["entry_id"], ["performer", "song", "place_contest",
                                           "youtube_url", "lyrics"]),
    "CONTEST": (980, 80, ["year"], []),
    "COUNTRY": (40, 350, ["country_code"], ["name"]),
    "ROUND": (980, 350, ["round_id"], ["round_type"]),
    "BOOKMAKER": (980, 630, ["bookmaker_id"], ["name"]),
}

# relationship -> (centre x, centre y, attributes written beside it, where to write them)
RELATIONSHIPS = {
    "is credited on": (360, 115, "role", "below"),
    "takes part in": (840, 115, "", "below"),
    "sends": (360, 385, "", "below"),
    "has": (1080, 240, "", "right"),
    "performs in": (840, 385, "running_order, place, points, points_tele, points_jury", "below"),
    "quotes odds for": (840, 570, "odds", "above"),
    "votes for": (360, 610, "total_points, tele_points, jury_points", "right"),
}

# lines: list of points, cardinality, and the index of the segment end where it is written
LINES = [
    ([(240, 115), (302, 115)], "N", 0),                      # PERSON - is credited on
    ([(418, 115), (480, 115)], "N", 1),                      # is credited on - SONG ENTRY
    ([(680, 115), (782, 115)], "N", 0),                      # SONG ENTRY - takes part in
    ([(898, 115), (980, 115)], "1", 1),                      # takes part in - CONTEST
    ([(240, 385), (302, 385)], "1", 0),                      # COUNTRY - sends
    ([(360, 355), (360, 180), (480, 180)], "N", 2),          # sends - SONG ENTRY
    ([(1080, 130), (1080, 210)], "1", 0),                    # CONTEST - has
    ([(1080, 270), (1080, 350)], "N", 1),                    # has - ROUND
    ([(650, 238), (650, 385), (782, 385)], "N", 0),          # SONG ENTRY - performs in
    ([(898, 385), (980, 385)], "N", 1),                      # performs in - ROUND
    ([(560, 238), (560, 570), (782, 570)], "N", 0),          # SONG ENTRY - quotes odds for
    ([(898, 570), (1030, 570), (1030, 428)], "N", 2),        # quotes odds for - ROUND
    ([(840, 600), (840, 665), (980, 665)], "N", 2),          # quotes odds for - BOOKMAKER
    ([(150, 428), (150, 610), (302, 610)], "N", 0),          # COUNTRY - votes for
    ([(360, 640), (360, 745), (1215, 745), (1215, 385), (1180, 385)], "N", 4),  # votes for - ROUND
]

ROLES = []


def entity_height(keys, others):
    return HEADER + ROW * (len(keys) + len(others)) + 8


def cardinality(points, text, at):
    x, y = points[at]
    ox, oy = points[at - 1] if at > 0 else points[1]
    if x == ox:                      # the line arrives vertically
        dx, dy = 8, (-8 if oy < y else 18)
        if at == 0:
            dy = 18 if oy > y else -8
    else:                            # the line arrives horizontally
        dy = -7
        dx = (-18 if ox < x else 8) if at > 0 else (8 if ox > x else -18)
    return f'<text x="{x + dx}" y="{y + dy}" class="card">{text}</text>'


def main():
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1260 820" width="1260" height="820">',
           "<style>"
           "text{font-family:Arial,Helvetica,sans-serif;fill:#1b2733}"
           ".title{font-size:20px;font-weight:bold}"
           ".ent{font-size:14px;font-weight:bold;fill:#ffffff}"
           ".attr{font-size:13px}"
           ".key{font-size:13px;font-weight:bold}"
           ".rel{font-size:12px;font-weight:bold}"
           ".relattr{font-size:11.5px;font-style:italic;fill:#4a5866}"
           ".card{font-size:14px;font-weight:bold;fill:#0b6e6e}"
           ".note{font-size:12px;fill:#4a5866}"
           "</style>",
           '<rect width="1260" height="820" fill="#ffffff"/>',
           '<text x="40" y="42" class="title">Eurovision database: entity-relationship diagram</text>']

    for points, text, at in LINES:
        path = " ".join(f"{x},{y}" for x, y in points)
        out.append(f'<polyline points="{path}" fill="none" stroke="#1b2733" stroke-width="1.6"/>')
        out.append(cardinality(points, text, at))

    for x, y, text, anchor in ROLES:
        out.append(f'<text x="{x}" y="{y}" class="relattr" text-anchor="{anchor}">{text}</text>')

    for name, (cx, cy, attributes, where) in RELATIONSHIPS.items():
        out.append(f'<polygon points="{cx - DW},{cy} {cx},{cy - DH} {cx + DW},{cy} {cx},{cy + DH}" '
                   f'fill="#e8f3f3" stroke="#0b6e6e" stroke-width="1.6"/>')
        out.append(f'<text x="{cx}" y="{cy + 4}" class="rel" text-anchor="middle">{name}</text>')
        if attributes:
            if where == "below":
                out.append(f'<text x="{cx}" y="{cy + DH + 16}" class="relattr" '
                           f'text-anchor="middle">{attributes}</text>')
            elif where == "above":
                out.append(f'<text x="{cx + 12}" y="{cy - DH - 6}" class="relattr">{attributes}</text>')
            else:
                out.append(f'<text x="{cx + DW + 10}" y="{cy - 12}" class="relattr">{attributes}</text>')

    for name, (x, y, keys, others) in ENTITIES.items():
        h = entity_height(keys, others)
        out.append(f'<rect x="{x}" y="{y}" width="{W_ENTITY}" height="{h}" fill="#ffffff" '
                   f'stroke="#1b2733" stroke-width="1.6"/>')
        out.append(f'<rect x="{x}" y="{y}" width="{W_ENTITY}" height="{HEADER}" fill="#0b6e6e" '
                   f'stroke="#1b2733" stroke-width="1.6"/>')
        out.append(f'<text x="{x + W_ENTITY / 2}" y="{y + 20}" class="ent" text-anchor="middle">{name}</text>')
        for i, attribute in enumerate(keys + others):
            css = "key" if attribute in keys else "attr"
            ty = y + HEADER + ROW * i + 18
            out.append(f'<text x="{x + 12}" y="{ty}" class="{css}">{attribute}</text>')
            if attribute in keys:  # underline drawn as a line, so every viewer shows it
                out.append(f'<line x1="{x + 12}" y1="{ty + 3}" x2="{x + 12 + 7.6 * len(attribute)}" '
                           f'y2="{ty + 3}" stroke="#1b2733" stroke-width="1.2"/>')

    out.append('<text x="40" y="785" class="note">Rectangle: entity, with its key attribute underlined. '
               'Diamond: relationship. 1, N: cardinalities. Text in italics beside a diamond: '
               'attributes of that relationship.</text>')
    out.append('<text x="40" y="803" class="note">"votes for" and "quotes odds for" link three entities. '
               'In "votes for" a country gives points to another country in a round.</text>')
    out.append("</svg>")

    os.makedirs("docs", exist_ok=True)
    with open("docs/er-conceptual.svg", "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print("docs/er-conceptual.svg written")


if __name__ == "__main__":
    main()
