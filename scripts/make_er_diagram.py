"""Draw the diagram of the ten tables as docs/er-diagram.svg.

Standard library only. Run again after any change to the tables:
    python scripts/make_er_diagram.py
Notation: boxes with (PK) and (FK) and the cardinalities 1 and N, as in the
"schema and cardinalities" slides of the course.
"""
import os

W, HEADER, ROW = 240, 30, 22

# table -> (x, y, columns)
TABLES = {
    "person": (40, 70, ["person_id (PK)", "name"]),
    "entry_credit": (340, 70, ["entry_id (PK, FK)", "person_id (PK, FK)", "role (PK)"]),
    "bookmaker": (940, 70, ["bookmaker_id (PK)", "name"]),
    "country": (40, 250, ["country_code (PK)", "name"]),
    "song_entry": (340, 250, ["entry_id (PK)", "year (FK)", "country_code (FK)", "performer",
                         "song", "place_contest", "youtube_url", "lyrics"]),
    "contest": (640, 250, ["year (PK)"]),
    "betting_odds": (940, 250, ["bookmaker_id (PK, FK)", "entry_id (PK, FK)",
                                "round_id (PK, FK)", "odds"]),
    "vote": (40, 540, ["round_id (PK, FK)", "from_country (PK, FK)", "to_country (PK, FK)",
                       "total_points", "tele_points", "jury_points"]),
    "performance": (340, 540, ["entry_id (PK, FK)", "round_id (PK, FK)", "running_order",
                               "place", "points", "points_tele", "points_jury"]),
    "round": (640, 540, ["round_id (PK)", "year (FK)", "round_type"]),
}

# Each relationship: points of the line from the 1 side to the N side, and an optional label.
RELATIONSHIPS = [
    ([(280, 107), (340, 107)], None),                              # person - entry_credit
    ([(460, 250), (460, 166)], None),                              # entry - entry_credit
    ([(280, 287), (340, 287)], None),                              # country - entry
    ([(640, 276), (580, 276)], None),                              # contest - entry
    ([(760, 302), (760, 540)], None),                              # contest - round
    ([(460, 456), (460, 540)], None),                              # entry - performance
    ([(640, 588), (580, 588)], None),                              # round - performance
    ([(110, 324), (110, 540)], "gives"),                           # country - vote (from)
    ([(210, 324), (210, 540)], "receives"),                        # country - vote (to)
    ([(760, 636), (760, 760), (160, 760), (160, 702)], None),      # round - vote
    ([(1060, 144), (1060, 250)], None),                            # bookmaker - betting_odds
    ([(540, 250), (540, 210), (1000, 210), (1000, 250)], None),    # entry - betting_odds
    ([(880, 588), (1060, 588), (1060, 368)], None),                # round - betting_odds
]


def height(columns):
    return HEADER + ROW * len(columns)


def label_near(point, towards, text):
    """Place 1 or N beside the end of a line, a little away from the box."""
    (x, y), (tx, ty) = point, towards
    if x == tx:   # vertical line
        dy = 16 if ty > y else -8
        return f'<text x="{x + 7}" y="{y + dy}" class="card">{text}</text>'
    dx = 8 if tx > x else -16
    return f'<text x="{x + dx}" y="{y - 6}" class="card">{text}</text>'


def main():
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1220 830" width="1220" height="830">',
           "<style>"
           "text{font-family:Arial,Helvetica,sans-serif;fill:#1b2733}"
           ".title{font-size:20px;font-weight:bold}"
           ".head{font-size:15px;font-weight:bold;fill:#ffffff}"
           ".col{font-size:13px}"
           ".key{font-size:13px;font-weight:bold}"
           ".card{font-size:14px;font-weight:bold;fill:#0b6e6e}"
           ".note{font-size:12px;fill:#4a5866}"
           ".rel{font-size:12px;font-style:italic;fill:#4a5866}"
           "</style>",
           '<rect width="1220" height="830" fill="#ffffff"/>',
           '<text x="40" y="40" class="title">Eurovision database: tables and cardinalities</text>']

    for points, label in RELATIONSHIPS:
        path = " ".join(f"{x},{y}" for x, y in points)
        out.append(f'<polyline points="{path}" fill="none" stroke="#0b6e6e" stroke-width="2"/>')
        out.append(label_near(points[0], points[1], "1"))
        out.append(label_near(points[-1], points[-2], "N"))
        if label:
            (x1, y1), (x2, y2) = points[0], points[1]
            out.append(f'<text x="{x1 - 8}" y="{(y1 + y2) // 2 + 30}" class="rel" '
                       f'text-anchor="end">{label}</text>')

    for name, (x, y, columns) in TABLES.items():
        h = height(columns)
        out.append(f'<rect x="{x}" y="{y}" width="{W}" height="{h}" fill="#ffffff" '
                   f'stroke="#1b2733" stroke-width="1.5"/>')
        out.append(f'<rect x="{x}" y="{y}" width="{W}" height="{HEADER}" fill="#0b6e6e" '
                   f'stroke="#1b2733" stroke-width="1.5"/>')
        out.append(f'<text x="{x + 12}" y="{y + 20}" class="head">{name}</text>')
        for i, column in enumerate(columns):
            css = "key" if "PK" in column else "col"
            out.append(f'<text x="{x + 12}" y="{y + HEADER + ROW * i + 16}" class="{css}">{column}</text>')

    out.append('<text x="40" y="800" class="note">PK: primary key. FK: foreign key. '
               '1 and N: one row on the 1 side is related to many rows on the N side. '
               'Columns in bold belong to the primary key.</text>')
    out.append('<text x="40" y="818" class="note">entry_credit, performance, vote and betting_odds '
               'resolve N:N relationships.</text>')
    out.append("</svg>")

    os.makedirs("docs", exist_ok=True)
    with open("docs/er-diagram.svg", "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print("docs/er-diagram.svg written")


if __name__ == "__main__":
    main()
