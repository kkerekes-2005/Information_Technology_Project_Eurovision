"""Eurovision explorer: charts and tables built on the SQL queries of the project.

    streamlit run app/streamlit_app.py

Rules followed in this file:
- Every number comes from a SQL query in sql/queries/ or sql/app/, run in PostgreSQL.
- Every value chosen by the user reaches SQL as a bound parameter (:name), never as text
  pasted into the SQL. The user never types SQL.
- Python only passes the parameters, then copies the returned rows into the chart.
  Rows are not filtered, grouped, sorted or combined here.
The look of the page is in app/style.py.
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import streamlit as st
from matplotlib.ticker import MaxNLocator

APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR.parent / "src"))
sys.path.insert(0, str(APP_DIR))

st.set_page_config(page_title="Eurovision Explorer", page_icon="🎤")

import style  # noqa: E402
from style import CARD, GRID, INK, INK_2, MUTED, SERIES  # noqa: E402

style.apply()

try:
    from sqlalchemy.exc import SQLAlchemyError

    from db import read_query, read_sql, run_query
except FileNotFoundError:
    st.error("password.txt was not found in the project folder. Create it with only the "
             "password of the PostgreSQL user inside, then reload this page.")
    st.stop()

MAX_COUNTRIES = len(SERIES)
AUTHOR = "Kinga Kerekes"
SOURCE = "Data: Spijkervet, The Eurovision Dataset (CC BY 4.0)"


# ---------------------------------------------------------------------------
# Database access with error handling
# ---------------------------------------------------------------------------

def fetch(name, params=None, app_query=False):
    """Run one query file with its parameters. Return the rows, or None after an error."""
    try:
        sql = read_sql(f"sql/app/{name}.sql") if app_query else read_query(name)
        return run_query(sql, params)
    except SQLAlchemyError as e:
        st.error("The database could not answer this question. Check that PostgreSQL is "
                 "running and that the data is loaded.")
        with st.expander("Technical detail"):
            st.code(str(e.orig if hasattr(e, "orig") else e))
        return None


def show_source(name, rows):
    """The returned rows and the SQL behind a chart, folded under the chart."""
    with st.expander("Data and SQL"):
        st.dataframe(rows, hide_index=True, width="stretch")
        st.code(read_query(name), language="sql")


def has_rows(rows, empty_message=None):
    """False after an error or for an empty result; an empty result shows a message."""
    if rows is None:
        return False
    if not rows:
        st.info(empty_message or "No results for these filters. Try a wider year range "
                                 "or a lower threshold.")
        return False
    return True


# ---------------------------------------------------------------------------
# Chart helpers: they only draw the lists they receive
# ---------------------------------------------------------------------------

def new_figure(height=4.0):
    fig, ax = plt.subplots(figsize=(9, height))
    fig.patch.set_facecolor(CARD)
    ax.set_facecolor(CARD)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(MUTED)
    ax.tick_params(colors=INK_2, labelsize=9)
    ax.set_axisbelow(True)
    return fig, ax


def finish(fig, ax, xlabel, ylabel, value_axis="y"):
    ax.set_xlabel(xlabel, color=INK_2, fontsize=10)
    ax.set_ylabel(ylabel, color=INK_2, fontsize=10)
    ax.grid(axis=value_axis, color=GRID, linewidth=0.8)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close(fig)


def horizontal_bars(labels, values, xlabel, color=SERIES[0]):
    """Bars from top to bottom in the order the query returned them."""
    fig, ax = new_figure(height=max(2.5, 0.28 * len(labels) + 0.8))
    positions = list(range(len(labels)))
    ax.barh(positions, values, color=color, height=0.7)
    ax.set_yticks(positions, labels)
    ax.invert_yaxis()
    for position, value in zip(positions, values):
        ax.text(value, position, f" {value}", va="center", fontsize=8, color=INK_2)
    if all(isinstance(v, int) for v in values):  # counts: whole numbers on the axis
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    finish(fig, ax, xlabel, "", value_axis="x")


# ---------------------------------------------------------------------------
# Filter values and headline numbers that come from the database
# ---------------------------------------------------------------------------

style.hero(AUTHOR, SOURCE)

countries = fetch("countries", app_query=True)
years = fetch("years", app_query=True)
headline = fetch("headline", app_query=True)
if not countries or not years or not headline:
    st.stop()

NAMES = {row["country_code"]: row["name"] for row in countries}
CODES = [row["country_code"] for row in countries]
FIRST_YEAR, LAST_YEAR = years[0]["first_year"], years[0]["last_year"]
h = headline[0]
style.cards([(f"{h['contests']}", "contests"), (f"{h['entries']:,}", "song entries"),
             (f"{h['countries']}", "countries"), (f"{h['votes']:,}", "votes cast")])


def country_menu(label, key, default="se"):
    return st.selectbox(label, CODES, index=CODES.index(default) if default in CODES else 0,
                        format_func=NAMES.get, key=key)


def year_range(key, low, high, default_low, default_high):
    return st.slider("Years", low, high, (default_low, default_high), key=key)


# ---------------------------------------------------------------------------
# Page
# ---------------------------------------------------------------------------

tab_results, tab_votes, tab_juries, tab_songs, tab_tables = st.tabs(
    ["Winners and places", "Voting", "Juries, public and bookmakers", "Songs", "More tables"])

# --- Winners and places ----------------------------------------------------
with tab_results:
    with st.container(border=True, key="card_q01"):
        style.section("Q01", "Which countries have won most often?",
                      "Victories per country in the chosen years")
        year_from, year_to = year_range("q01_years", FIRST_YEAR, LAST_YEAR, 1957, LAST_YEAR)
        rows = fetch("q01_wins_by_country", {"year_from": year_from, "year_to": year_to})
        if has_rows(rows):
            horizontal_bars([r["country"] for r in rows], [r["wins"] for r in rows], "Wins")
            show_source("q01_wins_by_country", rows)

    with st.container(border=True, key="card_q05"):
        style.section("Q05", "How did a country's place change over time?",
                      "Place in each final", "Place 1 is at the top of the chart.")
        country = country_menu("Country", "q05_country")
        rows = fetch("q05_place_over_time", {"country": country})
        if has_rows(rows, f"{NAMES[country]} never reached a final, so it has no place to "
                          "show. It took part only in semi-finals."):
            fig, ax = new_figure()
            ax.plot([r["year"] for r in rows], [r["place"] for r in rows],
                    color=SERIES[0], linewidth=2, marker="o", markersize=4)
            ax.invert_yaxis()
            finish(fig, ax, "Year", "Place in the final")
            show_source("q05_place_over_time", rows)

    with st.container(border=True, key="card_q10"):
        style.section("Q10", "Does performing later in the final help?",
                      "Average place for each position in the running order",
                      "A lower bar is a better average.")
        c1, c2 = st.columns([3, 1])
        with c1:
            year_from, year_to = year_range("q10_years", FIRST_YEAR, LAST_YEAR, 2004, LAST_YEAR)
        with c2:
            min_performances = st.number_input("Minimum finals per position", 1, 50, 10,
                                               key="q10_min")
        rows = fetch("q10_running_order", {"year_from": year_from, "year_to": year_to,
                                           "min_performances": min_performances})
        if has_rows(rows):
            fig, ax = new_figure()
            ax.bar([r["running_order"] for r in rows],
                   [float(r["average_place"]) for r in rows], color=SERIES[0], width=0.7)
            finish(fig, ax, "Position in the running order", "Average place")
            show_source("q10_running_order", rows)

    with st.container(border=True, key="card_q09"):
        style.section("Q09", "How did top finishes accumulate?",
                      f"Running total of top finishes, up to {MAX_COUNTRIES} countries",
                      "The query runs once for each country chosen.")
        c1, c2 = st.columns([3, 1])
        with c1:
            chosen = st.multiselect("Countries", CODES, default=["se", "ie", "gb", "ua"],
                                    format_func=NAMES.get, max_selections=MAX_COUNTRIES,
                                    key="q09_countries")
        with c2:
            max_place = st.number_input("Top places counted", 1, 10, 5, key="q09_place")
        # A country keeps its colour while it stays selected, so removing one does not
        # repaint the others.
        colours = st.session_state.setdefault("q09_colours", {})
        for code in list(colours):
            if code not in chosen:
                del colours[code]
        for code in chosen:
            if code not in colours:
                colours[code] = next(c for c in SERIES if c not in colours.values())
        if not chosen:
            st.info("Choose at least one country.")
        else:
            fig, ax = new_figure()
            results = []  # (country, its own rows), one query per country
            for code in chosen:
                rows = fetch("q09_cumulative_top_places",
                             {"countries": [code], "max_place": max_place})
                if rows:
                    ax.step([r["year"] for r in rows],
                            [r["cumulative_top_finishes"] for r in rows],
                            where="post", color=colours[code], linewidth=2, label=NAMES[code])
                    ax.text(rows[-1]["year"], rows[-1]["cumulative_top_finishes"],
                            f"  {NAMES[code]}", color=INK_2, fontsize=8, va="center")
                    results.append((code, rows))
            if results:
                legend = ax.legend(frameon=False, fontsize=9, loc="upper left")
                for text in legend.get_texts():
                    text.set_color(INK)
                finish(fig, ax, "Year", f"Finishes in the top {max_place}, running total")
                with st.expander("Data and SQL"):
                    for code, rows in results:
                        st.caption(NAMES[code])
                        st.dataframe(rows, hide_index=True, width="stretch")
                    st.code(read_query("q09_cumulative_top_places"), language="sql")
            else:
                plt.close(fig)
                st.info(f"None of these countries finished in the top {max_place}.")

# --- Voting ------------------------------------------------------------------
with tab_votes:
    with st.container(border=True, key="card_q04"):
        style.section("Q04", "Who gives a country the most points?",
                      "Average points given in the final",
                      "Default years 1975 to 2015, when every country gave 1 to 12 points, "
                      "so the averages are comparable.")
        c1, c2 = st.columns([1, 1])
        with c1:
            country = country_menu("Country receiving the points", "q04_country")
            top_n = st.number_input("How many givers", 1, 20, 5, key="q04_top")
        with c2:
            year_from, year_to = year_range("q04_years", FIRST_YEAR, LAST_YEAR, 1975, 2015)
            min_contests = st.number_input("Minimum contests", 1, 40, 10, key="q04_min")
        rows = fetch("q04_top_givers", {"country": country, "year_from": year_from,
                                        "year_to": year_to, "min_contests": min_contests,
                                        "top_n": top_n})
        if has_rows(rows, f"No country gave {NAMES[country]} points in at least "
                          f"{min_contests} finals between {year_from} and {year_to}. "
                          "Try a wider year range or fewer contests."):
            horizontal_bars([r["giver"] for r in rows],
                            [float(r["average_points"]) for r in rows],
                            f"Average points given to {NAMES[country]}")
            show_source("q04_top_givers", rows)

    with st.container(border=True, key="card_q06"):
        style.section("Q06", "Which pairs give each other high points?",
                      "Pairs whose average in both directions reaches the threshold")
        c1, c2, c3 = st.columns([3, 1, 1])
        with c1:
            year_from, year_to = year_range("q06_years", FIRST_YEAR, LAST_YEAR, 1975, 2015)
        with c2:
            min_average = st.number_input("Minimum average", 0.0, 12.0, 6.0, 0.5, key="q06_avg")
        with c3:
            min_contests = st.number_input("Minimum contests", 1, 40, 10, key="q06_min")
        rows = fetch("q06_mutual_voting", {"year_from": year_from, "year_to": year_to,
                                           "min_contests": min_contests,
                                           "min_average": min_average})
        if has_rows(rows):
            st.dataframe(rows, hide_index=True, width="stretch")
            with st.expander("SQL"):
                st.code(read_query("q06_mutual_voting"), language="sql")

# --- Juries, public and bookmakers ----------------------------------------
with tab_juries:
    with st.container(border=True, key="card_q07"):
        style.section("Q07", "Did the public and the juries agree?",
                      "Rank with the public against rank with the juries, finals since 2016",
                      "Each point is one entry. On the dashed diagonal both agree.")
        c1, c2 = st.columns([3, 1])
        with c1:
            year_from, year_to = year_range("q07_years", 2016, LAST_YEAR, 2016, LAST_YEAR)
        with c2:
            min_gap = st.number_input("Minimum difference in rank", 0, 25, 0, key="q07_gap")
        rows = fetch("q07_jury_vs_televote", {"year_from": year_from, "year_to": year_to,
                                              "min_gap": min_gap})
        if has_rows(rows):
            fig, ax = new_figure(height=5)
            ax.plot([1, 26], [1, 26], color=MUTED, linewidth=1, linestyle="--")
            ax.scatter([r["tele_rank"] for r in rows], [r["jury_rank"] for r in rows],
                       s=42, color=SERIES[2], edgecolors=CARD, linewidths=1.5, zorder=3)
            ax.invert_xaxis()
            ax.invert_yaxis()
            finish(fig, ax, "Rank with the public (televote)", "Rank with the juries",
                   value_axis="both")
            show_source("q07_jury_vs_televote", rows)

    with st.container(border=True, key="card_q11"):
        style.section("Q11", "Where did the bookmakers' favourite finish?",
                      "Real place of the entry with the lowest average odds",
                      "2020 has odds but no final, so it does not appear.")
        year_from, year_to = year_range("q11_years", 2015, LAST_YEAR, 2015, LAST_YEAR)
        rows = fetch("q11_bookmakers", {"year_from": year_from, "year_to": year_to,
                                        "max_odds_rank": 1})
        if has_rows(rows):
            fig, ax = new_figure()
            labels = [f"{r['year']}\n{r['country']}" for r in rows]
            ax.bar(labels, [r["real_place"] for r in rows], color=SERIES[0], width=0.6)
            for i, r in enumerate(rows):
                ax.text(i, r["real_place"], str(r["real_place"]), ha="center", va="bottom",
                        fontsize=9, color=INK)
            ax.yaxis.set_major_locator(MaxNLocator(integer=True))
            finish(fig, ax, "", "Real place of the favourite (1 = won)")
            show_source("q11_bookmakers", rows)
        with st.expander("The top favourites of each year"):
            max_rank = st.number_input("Favourites per year", 1, 10, 3, key="q11_rank")
            rows = fetch("q11_bookmakers", {"year_from": year_from, "year_to": year_to,
                                            "max_odds_rank": max_rank})
            if has_rows(rows):
                st.dataframe(rows, hide_index=True, width="stretch")

# --- Songs -------------------------------------------------------------------
with tab_songs:
    with st.container(border=True, key="card_q14"):
        style.section("Q14", "How often do the lyrics contain a word?",
                      "Share of each decade's entries whose lyrics contain it")
        word = st.text_input("Word or phrase", "love", max_chars=40, key="q14_word").strip()
        if not word:
            st.info("Type a word to search the lyrics.")
        else:
            # The word is sent as a parameter. % and _ are escaped so they are searched as
            # characters, not used as LIKE wildcards.
            escaped = word.lower().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            rows = fetch("q14_word_in_lyrics", {"pattern": f"%{escaped}%"})
            if has_rows(rows):
                fig, ax = new_figure()
                ax.bar([str(r["decade"]) + "s" for r in rows],
                       [float(r["percent"]) for r in rows], color=SERIES[0], width=0.6)
                ax.set_ylim(0, 100)  # a share: the axis always shows 0 to 100 %
                finish(fig, ax, "Decade", f'Entries whose lyrics contain "{word}" (%)')
                show_source("q14_word_in_lyrics", rows)

    with st.container(border=True, key="card_q12"):
        style.section("Q12", "Which composers wrote the most entries?",
                      "Songwriters behind many entries, often for several countries")
        min_entries = st.number_input("Minimum entries", 1, 20, 6, key="q12_min")
        rows = fetch("q12_composers", {"min_entries": min_entries})
        if has_rows(rows):
            st.dataframe(rows, hide_index=True, width="stretch")

# --- More tables -------------------------------------------------------------
with tab_tables:
    with st.container(border=True, key="card_q02"):
        style.section("Q02", "Best average place in the final",
                      "Countries with at least the chosen number of finals")
        min_finals = st.number_input("Minimum finals", 1, 60, 20, key="q02_min")
        rows = fetch("q02_best_average_place", {"min_finals": min_finals})
        if has_rows(rows):
            st.dataframe(rows, hide_index=True, width="stretch")

    with st.container(border=True, key="card_q03"):
        style.section("Q03", "Countries that never won", "And how close they came")
        min_entries = st.number_input("Minimum entries", 1, 60, 10, key="q03_min")
        rows = fetch("q03_never_won", {"min_entries": min_entries})
        if has_rows(rows):
            st.dataframe(rows, hide_index=True, width="stretch")

    with st.container(border=True, key="card_q08"):
        style.section("Q08", "Countries never in a final", "Entries sent and years active")
        rows = fetch("q08_never_in_a_final")
        if has_rows(rows):
            st.dataframe(rows, hide_index=True, width="stretch")

style.footer(f"{AUTHOR} · Project B", SOURCE)
