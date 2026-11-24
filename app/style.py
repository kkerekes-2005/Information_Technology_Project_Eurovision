"""Look of the Eurovision explorer: colours, fonts, header, cards and section titles.

The style follows the "Pink and Black Modern Music Presentation" template chosen by the
author: near-black background, purple and magenta blocks, cyan and yellow accents, dotted
chevrons and music notes. Only colours and shapes are reused; no image from the template
is included. Nothing in this file touches the data.
"""
import html

import streamlit as st

# Page colours, taken from the template.
BLACK = "#150F15"
CARD = "#1E1620"
PURPLE = "#9F30FF"
MAGENTA = "#FF39F7"
PINK = "#FFA4FB"
CYAN = "#20FFFF"
YELLOW = "#FFF73A"
WHITE = "#FFFFFF"

# Chart colours: the template hues toned down until they pass the colour checks on the
# dark background (lightness band, colour-blind separation, contrast). Fixed order.
SERIES = ["#E52DDE", "#9A8D00", "#00A3A8", "#A24BFF"]
INK, INK_2, MUTED, GRID = "#F0EFEC", "#C3C2B7", "#898781", "#3A2F3D"

FONTS = ("https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700"
         "&family=Inter:ital,wght@0,400;0,600;0,700;1,400&display=swap")


def chevrons(width=260, height=150, colour=PINK):
    """Dotted chevrons pointing left, drawn as SVG circles (the template's motif)."""
    dots = []
    step = 7
    for k in range(3):
        base = 20 + k * 78
        for row in range(-6, 7):
            for thick in range(3):
                x = base + abs(row) * step + thick * step
                y = height / 2 + row * step
                opacity = 0.35 + 0.65 * (1 - abs(row) / 6)
                dots.append(f'<circle cx="{x}" cy="{y}" r="2.2" fill="{colour}" '
                            f'opacity="{opacity:.2f}"/>')
    return (f'<svg viewBox="0 0 {width} {height}" width="100%" height="{height}" '
            f'xmlns="http://www.w3.org/2000/svg" aria-hidden="true">{"".join(dots)}</svg>')


CSS = f"""
<style>
@import url('{FONTS}');

html, body, [data-testid="stAppViewContainer"], [data-testid="stMarkdownContainer"] p,
[data-testid="stWidgetLabel"] p, .stCaption, input, textarea, button {{
    font-family: 'Inter', sans-serif;
}}
h1, h2, h3, .ev-title, .ev-h2 {{
    font-family: 'Sora', sans-serif !important;
    letter-spacing: -0.01em;
}}
[data-testid="stAppViewContainer"] {{ background: {BLACK}; }}
[data-testid="stHeader"] {{ background: transparent; }}
[data-testid="stAppDeployButton"] {{ display: none; }}
.block-container {{ padding-top: 2.2rem; max-width: 1000px; }}

/* Header, after the template's title slide */
.ev-hero {{ display: grid; grid-template-columns: 1.4fr 1fr; border-radius: 22px;
            overflow: hidden; margin-bottom: 1.4rem; }}
.ev-hero-main {{ background: {MAGENTA}; padding: 2.1rem 2.2rem 1.6rem; }}
.ev-hero-side {{ background: {BLACK}; display: flex; align-items: center;
                 padding: 0 1.2rem; border: 2px solid {MAGENTA}; border-left: none;
                 border-radius: 0 22px 0 0; }}
.ev-hero-strip {{ grid-column: 1 / 3; background: {PURPLE}; padding: 0.9rem 2.2rem;
                  display: flex; justify-content: space-between; color: {WHITE};
                  font-size: 0.82rem; }}
.ev-kicker {{ color: {WHITE}; font-size: 0.78rem; font-style: italic; opacity: 0.9; }}
.ev-title {{ color: {YELLOW}; font-size: 2.9rem; line-height: 1.05; font-weight: 600;
             margin: 0.6rem 0 0.9rem; }}
.ev-sub {{ color: {WHITE}; font-weight: 700; font-size: 0.98rem; margin: 0; }}
.ev-note {{ color: {WHITE}; font-style: italic; font-size: 0.88rem; margin-top: 0.6rem; }}
.ev-notes {{ font-size: 1.6rem; color: {CYAN}; margin-left: 0.4rem; }}

/* Headline numbers, after the template's coloured "98 %" cards */
.ev-cards {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.8rem;
             margin: 0 0 1.6rem; }}
.ev-card {{ border-radius: 14px; padding: 0.9rem 1rem; }}
.ev-card b {{ display: block; font-family: 'Sora', sans-serif; font-size: 1.7rem;
              line-height: 1.1; }}
.ev-card span {{ font-size: 0.78rem; }}
.ev-card.c1 {{ background: {CYAN}; color: {PURPLE}; }}
.ev-card.c2 {{ background: {MAGENTA}; color: {YELLOW}; }}
.ev-card.c3 {{ background: {PURPLE}; color: {WHITE}; }}
.ev-card.c4 {{ background: {YELLOW}; color: {BLACK}; }}

/* Tabs as pills */
[role="tablist"] {{ gap: 0.45rem; border: none !important; box-shadow: none !important;
                   flex-wrap: wrap; }}
[data-testid="stTab"] {{ background: {CARD}; border-radius: 999px; padding: 0.45rem 1.05rem !important;
                        border: 1px solid #3a2b40 !important; height: auto !important; }}
[data-testid="stTab"] p {{ font-weight: 600; color: {INK_2}; }}
[data-testid="stTab"][aria-selected="true"] {{ background: {MAGENTA}; border-color: {MAGENTA} !important; }}
[data-testid="stTab"][aria-selected="true"] p {{ color: {WHITE}; }}
[data-testid="stTab"]::after, [role="tablist"]::after {{ display: none !important; }}

/* Section cards: containers created with a key that starts with "card" */
[class*="st-key-card"] {{ background: {CARD}; border-radius: 20px !important;
    border: 1px solid #3a2b40 !important; padding: 1.3rem 1.4rem 1.1rem !important;
    position: relative; overflow: hidden; }}
[class*="st-key-card"]::before {{ content: ""; position: absolute; left: 0; top: 0; bottom: 0;
    width: 5px; background: linear-gradient({MAGENTA}, {PURPLE}); }}
.ev-section {{ margin-bottom: 0.4rem; }}
.ev-section .ev-q {{ color: {CYAN}; font-size: 0.78rem; font-weight: 700;
                     letter-spacing: 0.08em; }}
.ev-section .ev-h2 {{ color: {WHITE}; font-size: 1.55rem; font-weight: 600; margin: 0.2rem 0 0.3rem; }}
.ev-section .ev-lead {{ color: {WHITE}; font-weight: 700; font-size: 0.9rem; margin: 0; }}
.ev-section .ev-text {{ color: {INK_2}; font-size: 0.86rem; margin: 0.2rem 0 0; }}

[data-testid="stAlert"] > div {{ background: #2A1F2E !important; border-left: 4px solid {CYAN};
                                 border-radius: 12px; }}
[data-testid="stAlert"] p {{ color: {WHITE} !important; }}

[data-testid="stExpander"] details {{ border: 1px solid {PURPLE}66; border-radius: 12px;
                                      background: {BLACK}; }}
[data-testid="stExpander"] summary p {{ color: {PINK}; font-weight: 600; }}

/* SQL code blocks in the palette of the page */
[data-testid="stCode"] pre {{ background: {BLACK} !important; border: 1px solid #3a2b40;
                              border-radius: 12px; }}
[data-testid="stCode"] code {{ color: {WHITE} !important; }}
[data-testid="stCode"] .token.keyword {{ color: {MAGENTA} !important; font-weight: 600; }}
[data-testid="stCode"] .token.function {{ color: {CYAN} !important; }}
[data-testid="stCode"] .token.string,
[data-testid="stCode"] .token.number,
[data-testid="stCode"] .token.boolean {{ color: {YELLOW} !important; }}
[data-testid="stCode"] .token.comment {{ color: {MUTED} !important; font-style: italic; }}
[data-testid="stCode"] .token.operator,
[data-testid="stCode"] .token.variable {{ color: {PINK} !important; }}
[data-testid="stCode"] .token.punctuation {{ color: {INK_2} !important; }}

.ev-footer {{ margin-top: 2rem; padding: 1rem 1.4rem; border-radius: 16px; background: {PURPLE};
              color: {WHITE}; font-size: 0.82rem; display: flex; justify-content: space-between; }}
</style>
"""


def apply():
    st.markdown(CSS, unsafe_allow_html=True)


def hero(author, source):
    st.markdown(f"""
<div class="ev-hero">
  <div class="ev-hero-main">
    <div class="ev-kicker">Project B · Information Technology</div>
    <div class="ev-title">Eurovision<br>Explorer <span class="ev-notes">♪♫</span></div>
    <p class="ev-sub">Sixty-eight contests in a relational database</p>
    <p class="ev-note">Every chart below is a SQL query run in PostgreSQL</p>
  </div>
  <div class="ev-hero-side">{chevrons()}</div>
  <div class="ev-hero-strip"><span>Presented by: {html.escape(author)}</span>
    <span>{html.escape(source)}</span></div>
</div>""", unsafe_allow_html=True)


def cards(items):
    """items: list of (value, label). Values come from a SQL query."""
    parts = [f'<div class="ev-card c{i + 1}"><b>{html.escape(str(value))}</b>'
             f'<span>{html.escape(label)}</span></div>' for i, (value, label) in enumerate(items)]
    st.markdown(f'<div class="ev-cards">{"".join(parts)}</div>', unsafe_allow_html=True)


def section(query_id, title, lead, text=""):
    extra = f'<p class="ev-text">{html.escape(text)}</p>' if text else ""
    st.markdown(f"""
<div class="ev-section">
  <div class="ev-q">☆ QUERY {html.escape(query_id)}</div>
  <div class="ev-h2">{html.escape(title)}</div>
  <p class="ev-lead">{html.escape(lead)}</p>{extra}
</div>""", unsafe_allow_html=True)


def footer(text_left, text_right):
    st.markdown(f'<div class="ev-footer"><span>{html.escape(text_left)}</span>'
                f'<span>{html.escape(text_right)}</span></div>', unsafe_allow_html=True)
