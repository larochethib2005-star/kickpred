#!/usr/bin/env python3
"""Build the red/black Crowdfunding Success Prediction proposal deck."""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_LABEL_POSITION, XL_TICK_MARK
from pptx.oxml.ns import qn
import copy

# ---------- palette (dark theme) ----------
BLACK       = RGBColor(0x0D, 0x0D, 0x0D)   # page background
CHARCOAL    = RGBColor(0x1F, 0x1F, 0x1F)
CARD        = RGBColor(0x22, 0x22, 0x22)   # standard card on black bg
CARD2       = RGBColor(0x2B, 0x2B, 0x2B)   # alt row / secondary card shade
ACCENT_CARD = RGBColor(0x3A, 0x12, 0x16)   # maroon emphasis card (replaces old black-on-white accent)
WHITE       = RGBColor(0xFF, 0xFF, 0xFF)
OFFWHITE    = RGBColor(0xF7, 0xF5, 0xF5)
LIGHTGRAY   = RGBColor(0xEC, 0xEA, 0xEA)   # kept for the one light accent card (chart)
GRAY        = RGBColor(0x6B, 0x6B, 0x6B)
MUTED       = RGBColor(0x9A, 0x9A, 0x9A)
TXT_MUTED   = RGBColor(0xB8, 0xB4, 0xB4)   # secondary text on dark backgrounds
RED         = RGBColor(0xC8, 0x1E, 0x2C)
DARKRED     = RGBColor(0x7A, 0x0C, 0x14)
SOFTRED     = RGBColor(0xE3, 0x9A, 0xA0)

HEAD_FONT = "Cambria"
BODY_FONT = "Arial"

SW, SH = Inches(13.333), Inches(7.5)

prs = Presentation()
prs.slide_width = SW
prs.slide_height = SH
BLANK = prs.slide_layouts[6]


def add_slide(bg=WHITE):
    s = prs.slides.add_slide(BLANK)
    rect = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SW, SH)
    rect.fill.solid()
    rect.fill.fore_color.rgb = bg
    rect.line.fill.background()
    rect.shadow.inherit = False
    # send to back
    sp = rect._element
    sp.getparent().remove(sp)
    s.shapes._spTree.insert(2, sp)
    return s


def no_shadow(shape):
    shape.shadow.inherit = False


def textbox(slide, x, y, w, h, text, size, color, bold=False, italic=False,
            font=BODY_FONT, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
            line_spacing=1.0, space_after=0):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = 0
    tf.margin_right = 0
    tf.margin_top = 0
    tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    lines = text.split("\n")
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = line_spacing
        p.space_after = Pt(space_after)
        run = p.add_run()
        run.text = line
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.italic = italic
        run.font.name = font
        run.font.color.rgb = color
    return tb


def rounded_card(slide, x, y, w, h, fill, radius=0.08):
    shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
    try:
        shp.adjustments[0] = radius
    except Exception:
        pass
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill
    shp.line.fill.background()
    no_shadow(shp)
    return shp


def circle(slide, x, y, d, fill, text="", text_color=WHITE, size=16, bold=True, font=HEAD_FONT):
    shp = slide.shapes.add_shape(MSO_SHAPE.OVAL, x, y, d, d)
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill
    shp.line.fill.background()
    no_shadow(shp)
    if text:
        tf = shp.text_frame
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        tf.word_wrap = False
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        run = p.add_run()
        run.text = text
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.name = font
        run.font.color.rgb = text_color
    return shp


def kicker(slide, text, color=RED, x=Inches(0.6), y=Inches(0.5)):
    textbox(slide, x, y, Inches(6), Inches(0.35), text.upper(), 12, color,
            bold=True, font=BODY_FONT)


def section_tag(slide, idx, total=6, color=RED, dark_bg=False):
    textbox(slide, Inches(11.6), Inches(0.5), Inches(1.2), Inches(0.4),
            f"{idx} / {total}", 13, color, bold=True, align=PP_ALIGN.RIGHT)


def title(slide, text, y=Inches(0.85), size=38, color=WHITE, w=Inches(10.5)):
    textbox(slide, Inches(0.6), y, w, Inches(0.9), text, size, color, bold=True, font=HEAD_FONT)


def subtitle(slide, text, y=Inches(1.55), color=TXT_MUTED, size=15):
    textbox(slide, Inches(0.6), y, Inches(10.5), Inches(0.4), text, size, color, italic=True, font=BODY_FONT)


def footer(slide, page, total, source=""):
    txt = f"{page} / {total}"
    if source:
        txt += "  ·  " + source
    textbox(slide, Inches(0.6), Inches(7.08), Inches(12.1), Inches(0.3), txt, 10, MUTED, font=BODY_FONT)


def card_block(slide, x, y, w, h, label, body, label_color=RED, bg=CARD,
               body_color=WHITE, label_size=12, body_size=14, pad=0.22):
    rounded_card(slide, x, y, w, h, bg)
    textbox(slide, x + Inches(pad), y + Inches(pad*0.8), w - Inches(2*pad), Inches(0.3),
            label.upper(), label_size, label_color, bold=True, font=BODY_FONT)
    textbox(slide, x + Inches(pad), y + Inches(pad*0.8) + Inches(0.38), w - Inches(2*pad),
            h - Inches(pad*0.8) - Inches(0.5), body, body_size, body_color, font=BODY_FONT, line_spacing=1.08)


TOTAL_PAGES = 13

# =========================================================
# Slide 1 — Title
# =========================================================
s = add_slide(BLACK)
circle(s, Inches(10.6), Inches(-1.1), Inches(4.2), DARKRED)
circle(s, Inches(-1.5), Inches(5.3), Inches(3.4), CHARCOAL)
textbox(s, Inches(0.9), Inches(0.75), Inches(8), Inches(0.35),
        "PROPOSAL PRESENTATION · AI FOR BUSINESS AND SOCIETY", 12, SOFTRED, bold=True, font=BODY_FONT)
textbox(s, Inches(0.85), Inches(2.5), Inches(10.5), Inches(2.3),
        "Predicting\nCrowdfunding Success", 50, WHITE, bold=True, font=HEAD_FONT, line_spacing=1.0)
textbox(s, Inches(0.9), Inches(4.75), Inches(9), Inches(0.5),
        "A machine learning proposal for startup campaigns", 17, SOFTRED, italic=True, font=BODY_FONT)
textbox(s, Inches(0.9), Inches(6.55), Inches(9), Inches(0.5),
        "Thibault & Khoubeybe  ·  SKEMA Business School, BBA4", 13, WHITE, font=BODY_FONT)
notes = s.notes_slide.notes_text_frame
notes.text = ("[Speaker A, ~15s] Hello everyone, we are Thibault and Khoubeybe. Our proposal predicts "
              "whether a crowdfunding campaign will reach its funding goal, using machine learning.")

# =========================================================
# Slide 2 — Agenda
# =========================================================
s = add_slide(BLACK)
kicker(s, "Agenda")
title(s, "Structure of the Proposal", y=Inches(0.85))
items = [
    ("1", "Business problem"), ("2", "Objectives"), ("3", "Data & features"),
    ("4", "ML model selection"), ("5", "Expected application"), ("6", "Schedule"),
]
cw, ch, gx, gy = Inches(3.75), Inches(1.9), Inches(0.35), Inches(0.35)
x0, y0 = Inches(0.6), Inches(2.3)
for i, (num, label) in enumerate(items):
    col, row = i % 3, i // 3
    x = x0 + col * (cw + gx)
    y = y0 + row * (ch + gy)
    rounded_card(s, x, y, cw, ch, WHITE)
    circle(s, x + Inches(0.3), y + Inches(0.3), Inches(0.55), RED, text=num, size=18)
    textbox(s, x + Inches(0.3), y + Inches(1.05), cw - Inches(0.6), Inches(0.6),
            label, 16, BLACK, bold=True, font=HEAD_FONT)
textbox(s, Inches(0.6), Inches(6.5), Inches(11), Inches(0.4),
        "About 10 minutes, split between the two of us.", 14, TXT_MUTED, italic=True, font=BODY_FONT)
footer(s, 2, TOTAL_PAGES)
notes = s.notes_slide.notes_text_frame
notes.text = ("[Speaker A, ~20s] We follow the six parts of the course template: business problem, "
              "objectives, data and features, machine learning model, expected application, and schedule. "
              "We anchor our data and methodology to a real, documented GitHub project we found and verified.")

# =========================================================
# Slide 3 — Business problem
# =========================================================
s = add_slide(BLACK)
section_tag(s, 1)
kicker(s, "Business problem")
title(s, "Why Crowdfunding Needs a Prediction Tool", size=32)
subtitle(s, "What problem are we trying to solve?")
# big stat card
rounded_card(s, Inches(0.6), Inches(2.3), Inches(3.9), Inches(4.3), ACCENT_CARD)
textbox(s, Inches(0.9), Inches(2.7), Inches(3.3), Inches(1.3), "44%", 60, RED, bold=True, font=HEAD_FONT)
textbox(s, Inches(0.9), Inches(3.8), Inches(3.3), Inches(1.0),
        "of campaigns in our dataset failed to reach their funding goal\n(42.9% succeeded; the rest were canceled or still live).",
        14, WHITE, font=BODY_FONT, line_spacing=1.12)
textbox(s, Inches(0.9), Inches(5.9), Inches(3.3), Inches(0.6),
        "694,062 Kickstarter campaigns, 2009–2026", 11, SOFTRED, italic=True, font=BODY_FONT)
cards = [
    ("Who", "Startup founders running a campaign. Backers and platforms are affected too."),
    ("Today", "Founders rely on intuition, advice and a handful of similar campaigns — slow and hard to verify."),
    ("With ML", "A model trained on past campaigns estimates the chance of success before launch."),
]
for i, (lbl, body) in enumerate(cards):
    cx = Inches(4.85)
    cy_i = Inches(2.3) + i * Inches(1.5)
    card_block(s, cx, cy_i, Inches(7.9), Inches(1.3), lbl, body)
footer(s, 3, TOTAL_PAGES, 'Source: Kickstarter Full Campaigns dataset (694,062 projects, 2009-2026)')
notes = s.notes_slide.notes_text_frame
notes.text = ("[Speaker A, ~50s] Crowdfunding lets a startup collect small amounts from many backers, but "
              "it only works if the goal is reached. In the dataset we verified ourselves, 44% of campaigns "
              "failed and 43% succeeded, the rest canceled or still live. Founders carry this risk, and "
              "backers and platforms feel it too. Today founders mostly rely on intuition and a few "
              "comparable campaigns. Machine learning can instead learn patterns from hundreds of thousands "
              "of past campaigns and estimate the odds before a single dollar is spent on launch.")

# =========================================================
# Slide 4 — Objectives
# =========================================================
s = add_slide(BLACK)
section_tag(s, 2)
kicker(s, "Objectives")
title(s, "What We Want to Achieve", size=32)
subtitle(s, "What do we want to achieve, and why does it matter?")
rounded_card(s, Inches(0.6), Inches(2.25), Inches(12.1), Inches(1.15), ACCENT_CARD)
textbox(s, Inches(0.95), Inches(2.5), Inches(11.4), Inches(0.7),
        "Predict, before launch, whether a startup campaign will reach its funding goal.",
        19, WHITE, bold=True, font=HEAD_FONT, anchor=MSO_ANCHOR.MIDDLE)
objs = [
    ("Why it matters", "A failed campaign costs founders time and money. An early estimate lets them adjust before spending."),
    ("Who uses it", "Founders first. Platforms and backers can also use it to screen campaigns."),
    ("How it helps", "Beyond a yes/no answer, it shows which factors — goal, category, duration — matter most."),
]
ow, oh = Inches(3.85), Inches(2.9)
for i, (lbl, body) in enumerate(objs):
    x = Inches(0.6) + i * (ow + Inches(0.3))
    card_block(s, x, Inches(3.75), ow, oh, lbl, body)
footer(s, 4, TOTAL_PAGES)
notes = s.notes_slide.notes_text_frame
notes.text = ("[Speaker A, ~45s] Our objective is a before-launch prediction: will this campaign hit its "
              "goal, expressed as a probability. It matters because a failed campaign costs founders real "
              "time and money — an early signal lets them adjust goal, length or category before launch. "
              "Founders are the primary users; platforms and backers could screen campaigns the same way. "
              "And because we use an explainable model, we don't just get a prediction, we get the reasons "
              "behind it.")

# =========================================================
# Slide 5 — Data description
# =========================================================
s = add_slide(BLACK)
section_tag(s, 3)
kicker(s, "Data description")
title(s, "Our Dataset", size=32)
subtitle(s, "What data will we use?")
left_items = [
    ("Source", "Kaggle — “Kickstarter Full Campaigns” (scraped & curated through Apr. 2026)"),
    ("Records", "694,062 campaigns, 43 variables, global coverage"),
    ("Kept for the model", "~604,000: failed or successful only (canceled / live / other excluded)"),
    ("Period", "April 2009 to April 2026 — we verified this ourselves from raw timestamps"),
]
y = Inches(2.35)
for lbl, body in left_items:
    textbox(s, Inches(0.6), y, Inches(2.6), Inches(0.3), lbl.upper(), 11.5, RED, bold=True, font=BODY_FONT)
    textbox(s, Inches(0.6), y + Inches(0.32), Inches(5.6), Inches(0.75), body, 14, WHITE, font=BODY_FONT, line_spacing=1.05)
    y += Inches(1.12)

# right: donut-ish bar chart "how campaigns ended"
rounded_card(s, Inches(6.9), Inches(2.3), Inches(5.8), Inches(4.3), LIGHTGRAY)
textbox(s, Inches(7.2), Inches(2.55), Inches(5.2), Inches(0.35),
        "HOW THE CAMPAIGNS ENDED", 12, RED, bold=True, font=BODY_FONT)
chart_data = CategoryChartData()
chart_data.categories = ["Failed", "Successful", "Other"]
chart_data.add_series("Share", (44.25, 42.87, 12.88))
gframe = s.shapes.add_chart(XL_CHART_TYPE.BAR_CLUSTERED, Inches(7.1), Inches(3.0), Inches(5.4), Inches(3.3), chart_data)
chart = gframe.chart
chart.has_legend = False
chart.has_title = False
plot = chart.plots[0]
plot.has_data_labels = True
dls = plot.data_labels
dls.number_format = '0.0"%"'
dls.number_format_is_linked = False
dls.font.size = Pt(13)
dls.font.bold = True
dls.font.name = BODY_FONT
dls.font.color.rgb = WHITE
dls.position = XL_LABEL_POSITION.INSIDE_END
series = plot.series[0]
colors = [RED, BLACK, GRAY]
for i, pt in enumerate(series.points):
    pt.format.fill.solid()
    pt.format.fill.fore_color.rgb = colors[i]
cat_ax = chart.category_axis
cat_ax.tick_labels.font.size = Pt(13)
cat_ax.tick_labels.font.name = BODY_FONT
cat_ax.tick_labels.font.color.rgb = BLACK
cat_ax.format.line.fill.background()
cat_ax.major_tick_mark = XL_TICK_MARK.NONE
val_ax = chart.value_axis
val_ax.visible = False
val_ax.has_major_gridlines = False
textbox(s, Inches(7.2), Inches(6.35), Inches(5.3), Inches(0.3),
        '"Other" = canceled, live or in progress.', 10.5, GRAY, italic=True, font=BODY_FONT)
footer(s, 5, TOTAL_PAGES, "Source: Kaggle “Kickstarter Full Campaigns, May 2025–Apr 2026” (verified against raw CSV)")
notes = s.notes_slide.notes_text_frame
notes.text = ("[Speaker A, ~50s] We verified this dataset ourselves rather than trusting the Kaggle "
              "description blindly. It holds 694,062 campaigns across 43 columns, scraped monthly from "
              "2014 to April 2026, covering campaigns launched between 2009 and 2026. We keep only "
              "campaigns that ended as failed or successful, about 604,000 rows. The chart shows the real "
              "split we computed from the raw file: 44.25% failed, 42.87% succeeded, and about 13% other "
              "— canceled, live or in progress. So the two classes we actually train on are close to "
              "balanced, which is good news for modeling.")

# =========================================================
# Slide 6 — Resources / anchor project
# =========================================================
s = add_slide(BLACK)
kicker(s, "Our resources", color=SOFTRED)
title(s, "Kaggle & a Verified GitHub Benchmark", y=Inches(0.85), size=30, color=WHITE)
res = [
    ("Data", "Kaggle", "“Kickstarter Full Campaigns”: 694,062 projects, 43 variables, updated to April 2026."),
    ("Methodology", "GitHub", "rishabhRsinghvi/CrowdFunding-Campaign-Success-Prediction — notebooks for cleaning, EDA and modeling, which we ran and verified ourselves."),
    ("Benchmark", "5 models tested", "Logistic Regression, Decision Tree, Random Forest, AdaBoost, XGBoost — compared on 168,979 cleaned campaigns."),
]
rw = Inches(3.85)
for i, (tag, h, body) in enumerate(res):
    x = Inches(0.6) + i * (rw + Inches(0.3))
    rounded_card(s, x, Inches(2.25), rw, Inches(3.95), CHARCOAL)
    circle(s, x + Inches(0.3), Inches(2.55), Inches(0.5), RED, text=str(i+1), size=16)
    textbox(s, x + Inches(0.3), Inches(3.25), rw - Inches(0.6), Inches(0.3), tag.upper(), 11, SOFTRED, bold=True, font=BODY_FONT)
    textbox(s, x + Inches(0.3), Inches(3.58), rw - Inches(0.6), Inches(0.45), h, 18, WHITE, bold=True, font=HEAD_FONT)
    textbox(s, x + Inches(0.3), Inches(4.15), rw - Inches(0.6), Inches(1.9), body, 14, RGBColor(0xDD, 0xDD, 0xDD), font=BODY_FONT, line_spacing=1.12)
textbox(s, Inches(0.6), Inches(6.38), Inches(11.9), Inches(0.4),
        "We re-ran the repo's notebooks ourselves to confirm its reported results before relying on them.",
        13, SOFTRED, italic=True, font=BODY_FONT)
footer(s, 6, TOTAL_PAGES, "github.com/rishabhRsinghvi/CrowdFunding-Campaign-Success-Prediction")
notes = s.notes_slide.notes_text_frame
notes.text = ("[Speaker B, ~35s] We anchor our methodology to a specific, concrete project rather than a "
              "vague reference. On Kaggle we use the Kickstarter Full Campaigns dataset for our own data. "
              "On GitHub we found and actually ran a project by rishabhRsinghvi with three notebooks: data "
              "cleaning, exploratory analysis and modeling, trained on an earlier Kickstarter scrape. We "
              "verified its numbers ourselves instead of just citing them, and we reuse its feature and "
              "modeling logic, applied to our own richer, more recent dataset.")

# =========================================================
# Slide 7 — Features
# =========================================================
s = add_slide(BLACK)
section_tag(s, 3)
kicker(s, "Data & features")
title(s, "Which Variables Matter", size=32)
subtitle(s, "Which variables are important for the model?")
card_block(s, Inches(0.6), Inches(2.3), Inches(3.8), Inches(1.9), "What we predict",
           "Did the campaign reach its goal?\nSuccess = 1, Failure = 0", bg=ACCENT_CARD, body_color=WHITE, label_color=SOFTRED, body_size=14)
card_block(s, Inches(4.65), Inches(2.3), Inches(7.85), Inches(1.9), "Features known at launch",
           "Funding goal (USD)   ·   Main category & subcategory   ·   Country\nCampaign duration   ·   Launch month   ·   Blurb length   ·   Staff pick",
           body_size=14)
rounded_card(s, Inches(0.6), Inches(4.5), Inches(11.9), Inches(1.8), ACCENT_CARD)
textbox(s, Inches(0.95), Inches(4.75), Inches(11.2), Inches(0.35), "LEFT OUT ON PURPOSE", 12, SOFTRED, bold=True, font=BODY_FONT)
textbox(s, Inches(0.95), Inches(5.15), Inches(11.2), Inches(1.0),
        "Amount pledged and number of backers. Both are only known once a campaign is live, so using "
        "them would leak future information into a pre-launch prediction and make the model look "
        "excellent but practically useless.", 14, WHITE, font=BODY_FONT, line_spacing=1.12)
footer(s, 7, TOTAL_PAGES, "Variable logic adapted from the GitHub reference notebook")
notes = s.notes_slide.notes_text_frame
notes.text = ("[Speaker A, ~45s] The target is whether the campaign reached its goal, coded 1 or 0. The "
              "features are everything a founder already knows before launching: goal, category, "
              "subcategory, country, duration, launch month, blurb length, and whether it's a staff pick. "
              "We deliberately exclude backers count and amount pledged — both only exist once the "
              "campaign has started, so including them would be data leakage and defeat the whole purpose "
              "of a pre-launch tool.")

# =========================================================
# Slide 8 — ML problem type
# =========================================================
s = add_slide(BLACK)
section_tag(s, 4)
kicker(s, "Machine learning model")
title(s, "Identifying the Type of Problem", size=32)
subtitle(s, "Which type of machine learning problem do we have?")
qw = Inches(5.6)
rounded_card(s, Inches(0.6), Inches(2.5), qw, Inches(1.9), CARD)
textbox(s, Inches(0.95), Inches(2.72), qw-Inches(0.7), Inches(0.35), "QUESTION 1", 12, RED, bold=True, font=BODY_FONT)
textbox(s, Inches(0.95), Inches(3.1), qw-Inches(0.7), Inches(0.5), "Do we have labeled data?", 16, WHITE, bold=True, font=HEAD_FONT)
textbox(s, Inches(0.95), Inches(3.68), qw-Inches(0.7), Inches(0.6), "Yes — every past campaign has a known outcome (success or failure).", 13, TXT_MUTED, font=BODY_FONT)

rounded_card(s, Inches(7.15), Inches(2.5), qw, Inches(1.9), CARD)
textbox(s, Inches(7.5), Inches(2.72), qw-Inches(0.7), Inches(0.35), "QUESTION 2", 12, RED, bold=True, font=BODY_FONT)
textbox(s, Inches(7.5), Inches(3.1), qw-Inches(0.7), Inches(0.5), "Category or quantity?", 16, WHITE, bold=True, font=HEAD_FONT)
textbox(s, Inches(7.5), Inches(3.68), qw-Inches(0.7), Inches(0.6), "A category — success or failure, not an amount.", 13, TXT_MUTED, font=BODY_FONT)

rounded_card(s, Inches(2.4), Inches(5.0), Inches(8.5), Inches(1.5), ACCENT_CARD)
textbox(s, Inches(2.75), Inches(5.25), Inches(7.9), Inches(0.4), "RESULT", 12, SOFTRED, bold=True, font=BODY_FONT)
textbox(s, Inches(2.75), Inches(5.6), Inches(7.9), Inches(0.7),
        "Supervised classification — the model learns from past examples with known answers.",
        17, WHITE, bold=True, font=HEAD_FONT)
footer(s, 8, TOTAL_PAGES, "Decision logic adapted from the course's ML algorithms chart")
notes = s.notes_slide.notes_text_frame
notes.text = ("[Speaker B, ~40s] We use the course's decision chart. First: do we have labeled data? Yes — "
              "every past campaign has a known result. Second: category or quantity? A category, success "
              "or failure. That makes this supervised classification, not clustering (we're not looking "
              "for groups) and not regression (we're not predicting a dollar amount).")

# =========================================================
# Slide 9 — Chosen model: XGBoost
# =========================================================
s = add_slide(BLACK)
section_tag(s, 4)
kicker(s, "Machine learning model")
title(s, "Our Model: XGBoost", size=32)
subtitle(s, "How it works, and why it fits")
card_block(s, Inches(0.6), Inches(2.3), Inches(5.85), Inches(3.7), "How it works",
           "Builds decision trees one after another. Each new tree focuses on correcting the "
           "errors of the previous ones.\n\nThe trees' combined votes produce a success "
           "probability, not just a yes/no answer.", body_size=14, label_size=12)
card_block(s, Inches(6.65), Inches(2.3), Inches(5.85), Inches(3.7), "Why it fits",
           "Handles mixed numeric & categorical features (goal, category, country) without "
           "heavy preprocessing.\n\nCaptures non-linear effects, e.g. success odds dropping "
           "sharply above a goal threshold.\n\nRanks which features matter most — explainable, "
           "not a black box.", bg=ACCENT_CARD, body_color=WHITE, label_color=SOFTRED, body_size=14, label_size=12)
rounded_card(s, Inches(0.6), Inches(6.18), Inches(11.9), Inches(0.68), ACCENT_CARD)
textbox(s, Inches(0.9), Inches(6.27), Inches(11.3), Inches(0.5),
        "Evidence: in the reference project, tuned XGBoost was the best of 5 models tested — 75.1% accuracy, 76.1% precision.",
        14, SOFTRED, bold=True, font=BODY_FONT, anchor=MSO_ANCHOR.MIDDLE)
footer(s, 9, TOTAL_PAGES)
notes = s.notes_slide.notes_text_frame
notes.text = ("[Speaker B, ~55s] We choose XGBoost. In simple terms, it builds decision trees one after "
              "another, where each tree corrects the mistakes of the ones before it, and the combined "
              "votes give a success probability. It fits our problem well: it handles a mix of numeric "
              "and categorical features without much preprocessing, it captures non-linear effects — for "
              "example odds dropping sharply once the goal gets very high — and it ranks which features "
              "matter most. This isn't a guess: in the GitHub project we verified, tuned XGBoost beat "
              "logistic regression, decision tree, random forest and AdaBoost, reaching 75.1% accuracy.")

# =========================================================
# Slide 10 — Alternative models
# =========================================================
s = add_slide(BLACK)
section_tag(s, 4)
kicker(s, "Machine learning model")
title(s, "Benchmarking the Alternatives", size=32)
subtitle(s, "Results we verified on the reference project's 168,979 cleaned campaigns")

rows = [
    ("Model", "Test accuracy", "Note"),
    ("Logistic Regression", "72.1%", "Baseline — simple, explainable"),
    ("Decision Tree", "66.0%", "Overfits (99.9% on train)"),
    ("Random Forest", "73.6%", "Overfits (99.9% on train)"),
    ("AdaBoost", "69.6%", "Overfits (99.9% on train)"),
    ("XGBoost (tuned)", "75.1%", "Best result — our pick"),
]
tx, ty, tw, th = Inches(0.6), Inches(2.45), Inches(11.9), Inches(3.75)
gframe_tbl = s.shapes.add_table(len(rows), 3, tx, ty, tw, th)
table = gframe_tbl.table
table.columns[0].width = Inches(5.0)
table.columns[1].width = Inches(3.2)
table.columns[2].width = Inches(3.7)
for r, row in enumerate(rows):
    for c, val in enumerate(row):
        cell = table.cell(r, c)
        cell.text = val
        cell.margin_left = Inches(0.15)
        cell.margin_right = Inches(0.1)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        para = cell.text_frame.paragraphs[0]
        run = para.runs[0]
        is_header = (r == 0)
        is_winner = (r == len(rows) - 1)
        run.font.size = Pt(13.5 if not is_header else 13)
        run.font.name = BODY_FONT
        run.font.bold = is_header or is_winner or (c == 0)
        run.font.color.rgb = WHITE
        cell.fill.solid()
        if is_header:
            cell.fill.fore_color.rgb = ACCENT_CARD
        elif is_winner:
            cell.fill.fore_color.rgb = RED
        else:
            cell.fill.fore_color.rgb = CARD2 if r % 2 else CARD
table.first_row = False
textbox(s, Inches(0.6), Inches(6.45), Inches(11.9), Inches(0.5),
        "We compare all models with a 70/30 train-test split and track accuracy, precision, recall, F1 and ROC-AUC — not accuracy alone.",
        12.5, TXT_MUTED, italic=True, font=BODY_FONT)
footer(s, 10, TOTAL_PAGES, "Results verified by re-running github.com/rishabhRsinghvi's Modeling.ipynb")
notes = s.notes_slide.notes_text_frame
notes.text = ("[Speaker B, ~45s] We don't rely on a single model. We benchmarked five: logistic regression "
              "as our explainable baseline at 72.1%; decision tree, random forest and AdaBoost, which all "
              "scored near-perfect on training data but dropped to 66-74% on test data — a classic "
              "overfitting signature; and tuned XGBoost, which generalized best at 75.1% accuracy. We'll "
              "reuse this same comparison protocol — a 70/30 split and five metrics, not accuracy alone, "
              "since our classes are not perfectly balanced.")

# =========================================================
# Slide 11 — Expected application
# =========================================================
s = add_slide(BLACK)
section_tag(s, 5)
kicker(s, "Expected application")
title(s, "From Model to Decision", size=32)
subtitle(s, "How will the trained model be used in practice?")
steps = [
    ("User provides", "Funding goal, category, country, campaign duration, launch month."),
    ("Model computes", "XGBoost compares this campaign against hundreds of thousands of past ones."),
    ("Model produces", "A success probability — e.g. “63% chance to reach the goal.”"),
]
sw_, sh_ = Inches(3.75), Inches(2.6)
for i, (lbl, body) in enumerate(steps):
    x = Inches(0.6) + i * (sw_ + Inches(0.3))
    rounded_card(s, x, Inches(2.4), sw_, sh_, CARD if i != 2 else ACCENT_CARD)
    circle(s, x + Inches(0.3), Inches(2.65), Inches(0.5), RED, text=str(i+1), size=15)
    lcol = RED if i != 2 else SOFTRED
    textbox(s, x + Inches(0.3), Inches(3.35), sw_ - Inches(0.6), Inches(0.3), lbl.upper(), 11.5, lcol, bold=True, font=BODY_FONT)
    textbox(s, x + Inches(0.3), Inches(3.72), sw_ - Inches(0.6), Inches(1.15), body, 14, WHITE, font=BODY_FONT, line_spacing=1.1)
    if i < 2:
        textbox(s, x + sw_ + Inches(0.02), Inches(3.4), Inches(0.3), Inches(0.5), "→", 26, RED, bold=True, align=PP_ALIGN.CENTER)
rounded_card(s, Inches(0.6), Inches(5.35), Inches(11.9), Inches(1.15), ACCENT_CARD)
textbox(s, Inches(0.95), Inches(5.58), Inches(11.2), Inches(0.75),
        "Decision supported: launch as planned, lower the goal, or change the duration/category. "
        "Platforms and backers can use the same score to screen campaigns.",
        14, WHITE, font=BODY_FONT, anchor=MSO_ANCHOR.MIDDLE, line_spacing=1.1)
footer(s, 11, TOTAL_PAGES)
notes = s.notes_slide.notes_text_frame
notes.text = ("[Speaker B, ~45s] Picture a simple tool for founders. They enter what they're planning: "
              "goal, category, country, duration, launch month. The trained XGBoost model compares that "
              "plan against hundreds of thousands of past campaigns and returns a probability, say a 63% "
              "chance of success — illustrative only. That number supports a real decision: launch as "
              "planned, lower the goal, or adjust the category or duration and see the probability move. "
              "Platforms and backers could use the same score to screen or compare campaigns.")

# =========================================================
# Slide 12 — Schedule
# =========================================================
s = add_slide(BLACK)
section_tag(s, 6)
kicker(s, "Schedule")
title(s, "How We'll Complete the Project", size=32)
subtitle(s, "A realistic, five-week plan")
rows2 = [
    ("When", "Task", "Who"),
    ("Week 1", "Download, verify and clean the dataset (filter to failed/successful)", "Thibault"),
    ("Week 2", "Exploratory analysis, build features, check category balance", "Thibault"),
    ("Week 3", "Train baseline (Logistic Regression) and XGBoost", "Khoubeybe"),
    ("Week 4", "Compare all 5 models, tune XGBoost, read feature importance", "Khoubeybe"),
    ("Week 5", "Write the report, finalize the slides", "Both"),
]
tx, ty, tw, th = Inches(0.6), Inches(2.4), Inches(11.9), Inches(3.55)
gframe_tbl2 = s.shapes.add_table(len(rows2), 3, tx, ty, tw, th)
table2 = gframe_tbl2.table
table2.columns[0].width = Inches(1.7)
table2.columns[1].width = Inches(7.9)
table2.columns[2].width = Inches(2.3)
for r, row in enumerate(rows2):
    for c, val in enumerate(row):
        cell = table2.cell(r, c)
        cell.text = val
        cell.margin_left = Inches(0.15)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        para = cell.text_frame.paragraphs[0]
        run = para.runs[0]
        is_header = (r == 0)
        run.font.size = Pt(13 if not is_header else 13)
        run.font.name = BODY_FONT
        run.font.bold = is_header or c == 0
        run.font.color.rgb = WHITE
        cell.fill.solid()
        cell.fill.fore_color.rgb = ACCENT_CARD if is_header else (CARD2 if r % 2 else CARD)
table2.first_row = False
rounded_card(s, Inches(0.6), Inches(6.15), Inches(11.9), Inches(0.8), ACCENT_CARD)
textbox(s, Inches(0.95), Inches(6.3), Inches(11.2), Inches(0.5),
        "Feasible: public data, free tools (Python), and a verified reference project to build on.",
        14, SOFTRED, bold=True, font=BODY_FONT, anchor=MSO_ANCHOR.MIDDLE)
footer(s, 12, TOTAL_PAGES)
notes = s.notes_slide.notes_text_frame
notes.text = ("[Speaker B, ~40s] Five weeks. Week 1: download, verify and clean the data. Week 2: "
              "exploratory analysis and feature building. Week 3: train the baseline and XGBoost. Week 4: "
              "compare all five models and read feature importance. Week 5: write the report and finalize "
              "the slides. Thibault leads the data side, Khoubeybe leads modeling, and we write the report "
              "together. It's feasible because the data is public, the tools are free, and we already have "
              "a verified reference project to build on rather than starting from zero.")

# =========================================================
# Slide 13 — Thanks
# =========================================================
s = add_slide(BLACK)
circle(s, Inches(9.8), Inches(4.6), Inches(4.5), DARKRED)
circle(s, Inches(-1.8), Inches(-1.5), Inches(3.6), CHARCOAL)
textbox(s, Inches(0.9), Inches(3.0), Inches(9), Inches(1.2), "Thank you", 48, WHITE, bold=True, font=HEAD_FONT)
textbox(s, Inches(0.95), Inches(4.0), Inches(9), Inches(0.5), "Questions & discussion", 18, SOFTRED, italic=True, font=BODY_FONT)
notes = s.notes_slide.notes_text_frame
notes.text = "[~10s] Thank you for listening. We're happy to take your questions."

out_path = "out/Crowdfunding_Success_Prediction_Proposal.pptx"
import os
os.makedirs("out", exist_ok=True)
prs.save(out_path)
print("Saved:", out_path)
