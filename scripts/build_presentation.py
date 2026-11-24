"""Fill the music template with the Eurovision project content (one-off build script, paths refer to the build machine)."""
import copy

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Emu, Inches, Pt

SHOTS = "/tmp/shots/"
DOCS = "/mnt/user-data/outputs/eurovision-db/docs/"
prs = Presentation("/tmp/deck/base.pptx")
S = list(prs.slides)


def shape(slide, name):
    for sh in slide.shapes:
        if sh.name == name:
            return sh
    raise KeyError(name)


def remove(slide, *names):
    for name in names:
        el = shape(slide, name)._element
        el.getparent().remove(el)


def set_text(slide, name, lines):
    """Replace the text of a box, keeping the formatting of its first run in each paragraph."""
    if isinstance(lines, str):
        lines = [lines]
    tf = shape(slide, name).text_frame
    paras = tf.paragraphs
    while len(paras) < len(lines):  # clone the last paragraph
        tf._txBody.append(copy.deepcopy(paras[-1]._p))
        paras = tf.paragraphs
    for p, line in zip(paras, lines):
        runs = p.runs
        runs[0].text = line
        for r in runs[1:]:
            r._r.getparent().remove(r._r)
    for p in paras[len(lines):]:
        p._p.getparent().remove(p._p)


def picture(slide, path, x, y, w, h, name):
    """Add an image fitted inside the box (x, y, w, h) in inches, centred, aspect kept."""
    iw, ih = Image.open(path).size
    scale = min(w / iw, h / ih)
    pw, ph = iw * scale, ih * scale
    pic = slide.shapes.add_picture(path, Inches(x + (w - pw) / 2), Inches(y + (h - ph) / 2),
                                   Inches(pw), Inches(ph))
    pic.name = name
    return pic


def textbox(slide, x, y, w, h, runs, size=20, name="Text"):
    """runs: list of paragraphs; each paragraph a list of (text, colour hex, bold)."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tb.name = name
    tf = tb.text_frame
    tf.word_wrap = True
    for i, para in enumerate(runs):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(2)
        for text, colour, bold in para:
            r = p.add_run()
            r.text = text
            r.font.size = Pt(size)
            r.font.bold = bold
            r.font.name = "Open Sauce Bold" if bold else "Open Sauce"
            r.font.color.rgb = RGBColor.from_string(colour)
    return tb


def widen(slide, name, w):
    shape(slide, name).width = Inches(w)


def notes(slide, text):
    """Speaker notes are intentionally not written."""
    return


# 1. Title -----------------------------------------------------------------
s = S[0]
set_text(s, "TextBox 19", "Information Technology · Project B")
set_text(s, "TextBox 17", "Eurovision Explorer")
set_text(s, "TextBox 20", "A relational database of the Song Contest")
set_text(s, "TextBox 18", "68 contests, 1956 to 2023, answered in SQL")
set_text(s, "TextBox 14", "Presented By:")
set_text(s, "TextBox 15", "Kinga Kerekes")
set_text(s, "TextBox 16", ["25 November", "2026"])
notes(s, "Hello. My project turns the Eurovision Song Contest dataset into a PostgreSQL "
         "database: profiled, modelled, cleaned and loaded from Python, queried in SQL, and shown "
         "in a Streamlit app. About 45 seconds per slide, live demo at the end.")

# 2. Data ------------------------------------------------------------------
s = S[1]
set_text(s, "TextBox 7", ["The Data", "Source"])
set_text(s, "TextBox 8", "The Eurovision Dataset · CC BY 4.0")
set_text(s, "TextBox 13", "contestants.csv")
set_text(s, "TextBox 9", "1,734 rows: one per song, with places, points, running order, "
                         "composers and lyrics")
set_text(s, "TextBox 14", "votes.csv")
set_text(s, "TextBox 10", "51,354 rows: the points one country gave another in each round")
set_text(s, "TextBox 15", "betting_offices.csv")
set_text(s, "TextBox 11", "9,453 rows: odds from 33 bookmakers, 2015 to 2023")
set_text(s, "TextBox 16", "Why this dataset")
set_text(s, "TextBox 12", "Real and open, three files that share year and country, one "
                          "table above 10,000 rows")
set_text(s, "TextBox 17", "Spijkervet, release 2023 · DOI 10.5281/zenodo.4036457")
widen(s, "TextBox 17", 6.2)
notes(s, "The data is The Eurovision Dataset by Janne Spijkervet, release 2023, licensed CC BY "
         "4.0. Three CSV files: contestants, one row per song; votes, the points between "
         "countries, 51 thousand rows, so large enough for indexes to matter; and bookmaker "
         "odds. The files share the year and the country, which makes the data relational. "
         "A script downloads them; they are not in the repository.")

# 3. Profile ---------------------------------------------------------------
s = S[2]
set_text(s, "TextBox 15", ["Profiling", "the Raw Data"])
set_text(s, "TextBox 16", "40 SQL queries on the untouched files")
set_text(s, "TextBox 17", "Raw files loaded unchanged into text tables and examined "
                          "only with SQL.")
set_text(s, "TextBox 18", "sql/profiling.sql, queries P01 to P40")
shape(s, "TextBox 18").left = Inches(5.2)
widen(s, "TextBox 18", 5.6)
set_text(s, "TextBox 22", "259")
set_text(s, "TextBox 19", "country names in the code column")
set_text(s, "TextBox 21", "20")
set_text(s, "TextBox 20", "repeated keys")
notes(s, "Before modelling I loaded the raw files unchanged into text-only staging tables and "
         "profiled them with 40 SQL queries. Two examples: 259 rows have a full country name "
         "where a two-letter code should be, so the column could not be a foreign key. And "
         "year plus country is not a key: 20 pairs repeat, five because in 1956 each country "
         "sent two songs, fifteen because 2023 entries are split over two rows. Other findings: "
         "1,975 self-votes with zero points, decimals like 27.0, and lists of composers in "
         "one cell.")

# 4. Preprocessing ---------------------------------------------------------
s = S[3]
set_text(s, "TextBox 7", ["Cleaning", "and Why"])
set_text(s, "TextBox 8", "16 rules, each counted in the cleaning log")
set_text(s, "TextBox 13", "Country codes")
set_text(s, "TextBox 9", "259 names turned into codes and 11 name variants unified, so the "
                         "code can be a foreign key")
set_text(s, "TextBox 14", "One song, one row")
set_text(s, "TextBox 10", "15 split 2023 entries merged, with one result per round")
set_text(s, "TextBox 15", "Lists and formats")
set_text(s, "TextBox 11", "Composer lists split per person, 27.0 made 27, empty cells kept "
                          "NULL")
set_text(s, "TextBox 16", "Placeholders")
set_text(s, "TextBox 12", "1956 places set to NULL, 2020 odds loaded once, self-votes kept and "
                          "excluded in SQL")
set_text(s, "TextBox 17", "src/etl/clean.py · docs/cleaning-log.md")
widen(s, "TextBox 17", 6.2)
notes(s, "Cleaning happens in Python while reading the files, because the project asks the "
         "load script to transform the data; analysis stays in SQL. Country names become codes "
         "so the column can be a foreign key. The split 2023 entries are merged. Composer lists "
         "are split into one row per person, which is first normal form. Placeholders: 1956 "
         "gives place 2 to every song including the winner, so those places become NULL; the "
         "2020 odds are repeated under three rounds, so one copy is loaded; the self-votes "
         "are kept and excluded in the queries, so nothing is filtered outside SQL. Missing "
         "values stay NULL; nothing is invented.")

# 5. Design ----------------------------------------------------------------
s = S[4]
remove(s, "Group 2", "Group 4", "Freeform 8", "Freeform 6", "Freeform 7")
set_text(s, "TextBox 9", "Design")
set_text(s, "TextBox 10", ["From Diagram", "to Tables"])
shape(s, "TextBox 11").left, shape(s, "TextBox 11").top = Inches(1.86), Inches(5.35)
set_text(s, "TextBox 11", "10 tables in third normal form")
box = shape(s, "TextBox 12")
box.left, box.top, box.width = Inches(1.86), Inches(6.35), Inches(6.6)
set_text(s, "TextBox 12", "Six entities, seven relationships. Four link tables resolve the "
                          "many-to-many relationships: performance, vote, entry_credit and "
                          "betting_odds. Surrogate keys, because year and country is not "
                          "unique.")
picture(s, DOCS + "er-conceptual.png", 9.3, 1.2, 9.9, 8.9, "ER diagram")
notes(s, "Six entities: country, contest, round, song entry, person, bookmaker. A country sends "
         "an entry, an entry performs in rounds, countries vote for countries in a round, and "
         "bookmakers quote odds for an entry in a round. Each many-to-many relationship becomes "
         "its own table. Exceptions I justify in the report: surrogate keys because of 1956; "
         "total points stored although from 2016 it equals jury plus televote, because before "
         "2016 the parts do not exist; and votes linked to countries, not to entries.")

# 6. Load ------------------------------------------------------------------
s = S[5]
remove(s, "Group 5")
set_text(s, "TextBox 11", ["Loading", "the Data"])
set_text(s, "TextBox 12", "All or nothing, in one transaction")
set_text(s, "TextBox 13", "The schema script creates the empty tables; load.py cleans the "
                          "files and inserts all ten tables in one transaction. One bad row, "
                          "a vote for the country zz, and everything is rolled back.")
set_text(s, "TextBox 14", "python src/etl/load.py --fail")
widen(s, "TextBox 14", 6.5)
picture(s, "/tmp/deck/rollback.png", 10.88, 1.2, 7.4, 5.3, "Rollback output")
notes(s, "schema.sql creates the tables with all constraints first; the load only inserts. "
         "load.py uses psycopg2 and execute_values inside one with-connection block, so it "
         "commits only if everything succeeds. With the fail option it adds one vote for a "
         "country that does not exist: five tables were already inserted, the foreign key "
         "rejects the vote, and every table ends with zero rows. After a normal load the "
         "script compares the rows prepared with COUNT star in every table.")

# 7. Constraints and indexes -----------------------------------------------
s = S[6]
remove(s, "Group 2", "Freeform 9", "Freeform 12")
set_text(s, "TextBox 14", ["Constraints", "and Indexes"])
set_text(s, "TextBox 13", "Checked after the load")
set_text(s, "TextBox 15", "21 keys and unique rules, 14 CHECK rules and 26 NOT NULL columns "
                          "are in place; six wrong inserts are each rejected. An index on "
                          "vote.to_country replaces a full scan.")
set_text(s, "TextBox 17", "25×")
set_text(s, "TextBox 16", "faster with the index")
picture(s, "/tmp/deck/explain.png", 11.2, 1.12, 6.9, 9.0, "Query plans")
notes(s, "After loading I list every constraint from the information schema and try six "
         "inserts that break one rule each: a duplicate key, an unknown country, a duplicate "
         "name, a missing performer, negative points, an unknown round type. All are "
         "rejected. The primary key of vote starts with round id, so searching by receiving "
         "country scans all 51 thousand rows: 6 milliseconds. With an index it reads only the "
         "193 matching rows: 0.24 milliseconds. For a condition half the table meets, the "
         "planner ignores the index, which is correct.")

# 8. Queries list ----------------------------------------------------------
s = S[7]
for sh in list(s.shapes):
    if sh.name.startswith("Freeform"):
        sh._element.getparent().remove(sh._element)
set_text(s, "TextBox 5", ["14 Questions", "in SQL"])
set_text(s, "TextBox 6", "Joins, GROUP BY with HAVING, subqueries, window functions, CTEs "
                         "and a transaction: every required construct appears")
C, W, G = "20FFFF", "FFFFFF", "C3C2B7"
left = [("Q01", "Who won most often?", "4-table join"),
        ("Q02", "Best average place in finals", "HAVING"),
        ("Q03", "Who never won?", "subquery NOT IN"),
        ("Q04", "Who gives a country most points?", "CTE + RANK"),
        ("Q05", "A country's place over time", "LAG"),
        ("Q06", "Pairs voting for each other", "self-join"),
        ("Q07", "Public against juries", "two RANKs")]
right = [("Q08", "Countries never in a final", "LEFT JOIN"),
         ("Q09", "Top finishes, running total", "SUM OVER"),
         ("Q10", "Does running order matter?", "HAVING"),
         ("Q11", "Did the favourite win?", "CTE + RANK"),
         ("Q12", "Most prolific composers", "N:N join"),
         ("Q13", "Add a contest, all or nothing", "transaction"),
         ("Q14", "Words in the lyrics", "LIKE + share")]
for col, items in ((8.6, left), (14.3, right)):
    for i, (q, text, how) in enumerate(items):
        textbox(s, col, 1.25 + i * 1.3, 5.5, 1.2,
                [[(q + "  ", C, True), (text, W, True)], [("        " + how, G, False)]],
                size=18, name=f"{q} line")
notes(s, "Fourteen queries, all mine, each in its own file with named parameters so the app "
         "can bind filter values. Every construct the project requires appears: joins of up to "
         "five tables, GROUP BY with HAVING, a NOT IN subquery, window functions RANK, LAG and a "
         "running SUM, CTEs, and Q13, which inserts a whole contest in one transaction and shows "
         "a failing transaction being rolled back.")

# 9. Results: winners and votes --------------------------------------------
s = S[8]
remove(s, "Group 2", "Group 4", "Freeform 9", "Freeform 10")
set_text(s, "TextBox 11", ["Winners", "and Votes"])
set_text(s, "TextBox 12", "Q01, Q04 and Q06")
set_text(s, "TextBox 13", "Sweden and Ireland share the record with seven wins. From 1975 to "
                          "2015 Denmark gave Sweden 8.0 points on average; Cyprus and Greece "
                          "are the strongest mutual pair.")
set_text(s, "TextBox 14", "Defaults: years 1975 to 2015, at least 10 contests")
widen(s, "TextBox 14", 7.0)
picture(s, SHOTS + "card_q04.png", 1.72, 1.2, 7.4, 5.3, "Q04 chart")
picture(s, SHOTS + "card_q06.png", 14.1, 6.6, 5.6, 3.4, "Q06 table")
notes(s, "Some answers. Sweden and Ireland have seven wins each. Q04 ranks the countries that "
         "give a chosen country the most points, with RANK partitioned by receiver in a CTE: "
         "for Sweden it is Denmark, then Norway. Q06 joins the averages with themselves to find "
         "pairs that give each other high points both ways: Cyprus and Greece lead. I use "
         "1975 to 2015 by default because only then did every country give 1 to 12 points.")

# 10. Results: juries and bookmakers ---------------------------------------
s = S[9]
remove(s, "Group 5", "Group 7", "Freeform 11")
set_text(s, "TextBox 13", "Q07 and Q11")
set_text(s, "TextBox 14", ["Juries and", "Bookmakers"])
set_text(s, "TextBox 15", "Ranks compared inside each year")
set_text(s, "TextBox 16", "Since 2016 the public and the juries often disagree: points far "
                          "from the diagonal. The bookmakers' favourite won 5 of the 8 finals "
                          "from 2015 to 2023.")
set_text(s, "TextBox 17", "2020 had odds but no final")
widen(s, "TextBox 17", 6.0)
picture(s, SHOTS + "card_q07.png", 1.6, 1.0, 7.9, 4.75, "Q07 chart")
picture(s, SHOTS + "card_q11.png", 1.6, 5.95, 7.9, 4.75, "Q11 chart")
notes(s, "Q07 ranks every final entry since 2016 twice inside its year, by televote and by "
         "jury points; points far from the diagonal are songs the public loved and the juries "
         "did not, or the reverse. Q11 averages the odds of all bookmakers per entry, ranks "
         "them, and compares the favourite with the real result: the favourite won five of "
         "the eight finals.")

# 11. App ------------------------------------------------------------------
s = S[10]
remove(s, "Group 2", "Freeform 6")
set_text(s, "TextBox 7", "app/streamlit_app.py")
set_text(s, "TextBox 8", ["Building", "the App"])
set_text(s, "TextBox 9", "Streamlit and SQLAlchemy, SQL only")
set_text(s, "TextBox 10", "Each chart sends its query file with bound parameters and draws "
                          "the rows as returned. Every chart shows its rows and SQL. Bad "
                          "input and empty results give messages; typed text never runs as "
                          "SQL.")
picture(s, "/tmp/deck/app_strip.png", 2.0, 1.2, 16.0, 4.9, "App screenshots")
notes(s, "The app has five tabs, eight charts and seven tables. One module, db.py, holds the "
         "engine and run_query, which sends a query file with text() and bound parameters. "
         "Python takes the returned columns as lists for matplotlib; it never groups or sorts. "
         "Where a chart has several countries, the query runs once per country. Sliders and "
         "number boxes have limits, so invalid values are impossible; a failed or empty query "
         "shows a message. The look follows this template.")

# 12. Demo -----------------------------------------------------------------
s = S[11]
set_text(s, "TextBox 5", ["Live", "Demo"])
set_text(s, "TextBox 6", ["1. Change the years of Q01", "2. Andorra: an explained empty result",
                         "3. The Data and SQL panel", "4. An injection attempt in the lyrics search"])
box = shape(s, "TextBox 6")
box.top, box.width = Inches(5.6), Inches(4.6)
notes(s, "Demo. First, Q01 with the years from 1997: the ranking changes because the query "
         "runs again with the new parameter. Second, choose Andorra in Q05: it never reached a "
         "final, and the app says so instead of showing an empty chart. Third, open Data and "
         "SQL under a chart. Fourth, type quote OR quote 1 equals 1 into the lyrics search: it is "
         "searched as words and found nowhere, because it is a parameter value, never SQL.")

# 13. Thank you ------------------------------------------------------------
s = S[12]
set_text(s, "TextBox 23", "Eurovision Explorer")
set_text(s, "TextBox 19", ["Thank You", "Questions?"])
set_text(s, "TextBox 20", "Kinga Kerekes")
set_text(s, "TextBox 21", "Project B")
set_text(s, "TextBox 22", "Data: Spijkervet, CC BY 4.0")
set_text(s, "TextBox 18", "streamlit run app/streamlit_app.py")
shape(s, "TextBox 18").left = Inches(10.31)
widen(s, "TextBox 18", 7.8)
set_text(s, "TextBox 17", "68 contests, 10 tables, 14 questions: every number on these slides "
                          "comes from a SQL query.")
notes(s, "Thank you. I am happy to take questions on any part: the profile, the model, the "
         "load, the queries or the app.")

prs.save("/tmp/deck/eurovision-presentation.pptx")
print("saved")
