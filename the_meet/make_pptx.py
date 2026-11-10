#!/usr/bin/env python3
"""the_meet/make_pptx.py — turns the six exported pages into a presentation.

16:9 widescreen (13.333 x 7.5 in). A title slide, one full-bleed page per slide,
a closing slide, and speaker notes throughout. Images are embedded at the export
resolution (9602 x 5402, ~720 dpi at slide size) so nothing is soft when projected
or zoomed. Run after generate.py + drawio-export.sh.
"""

import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

INK = RGBColor(0x11, 0x1A, 0x24)
MUTED = RGBColor(0x3E, 0x4A, 0x58)
FAINT = RGBColor(0x65, 0x71, 0x7F)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
FONT = "Arial"

EXPORT = "the_meet/export"
OUT = "the_meet/aidesk-pack.pptx"
W, H = 13.333, 7.5

SLIDES = [
    ("aidesk-pack-01-·-One-framework.png", "One framework, three experiences",
     "The whole picture. Every experience starts at the client; AI-Desk powers the client and "
     "AI-Desk uses DataHub. Three client groups sit above the seam, the AI-DESK band holds the three "
     "services it hosts, and DataHub is the system of record underneath with the attached sources.",
     "Open here. Point out the seam: questions and answers cross it, data never does. Everything "
     "below the dashed line belongs to the platform."),
    ("aidesk-pack-02-·-Bots.png", "Bots — configured once, then it answers on its own",
     "A configured bot brings the question. AI-Desk understands it, checks which data the bot may "
     "touch, and builds the query. The bot takes the query up and executes it on top of DataHub, "
     "which is the only component that touches the source database.",
     "The key line is 'the bot owns the answer' — AI-Desk only builds the query. Emphasise that the "
     "instance is ephemeral and nothing lingers between requests."),
    ("aidesk-pack-03-·-Enterprise-Search.png", "Enterprise Search — behind the seam",
     "The client asks; AI-Desk finds the right repository and tables, writes the query and validates "
     "it before anything runs. DataHub runs it on the source and reflects the rows back, so the agent "
     "can reason over the data and return insight, not just rows.",
     "This is the experience that shows the framework looking at data rather than only moving it. "
     "Documents from the same estate land here too, through the Unstructured service."),
    ("aidesk-pack-04-·-Data-Analyst.png", "Data Analyst — in the analyst's own browser",
     "The analyst brings their own key and their own files. AI-Desk profiles the file, drafts the SQL "
     "and runs it in the browser; DataHub is touched only when the analyst points at a real table. "
     "The rows never leave the analyst's browser.",
     "Where the Bots story is embedded and the Search story is enterprise-wide, this one is private "
     "by default. It is the on-ramp: a spreadsheet is enough to start."),
    ("aidesk-pack-06-·-Capability-matrix.png", "What each experience gets from the framework",
     "Capability comparison for scoping and selection: how each experience runs, what data it uses, "
     "who runs the query, where the rows live, whether documents are involved, what it reads from and "
     "writes to DataHub, and how it reaches a model.",
     "Leave this up during questions. Three rows answer most of them: who runs the query, where the "
     "rows live, and model access — shared for the first two, BYOK for the analyst."),
]


def blank(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg.fill.solid()
    bg.fill.fore_color.rgb = WHITE
    bg.line.fill.background()
    bg.shadow.inherit = False
    return s


def text(slide, x, y, w, h, lines, size, colour=INK, bold=False, italic=False,
         spacing=1.0, tracking=None):
    if isinstance(lines, str):
        lines = [lines]
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.TOP
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.LEFT
        p.line_spacing = spacing
        r = p.add_run()
        r.text = line
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.italic = italic
        r.font.color.rgb = colour
        r.font.name = FONT
        if tracking:
            r.font._rPr.set("spc", str(tracking))
    return tb


def ink_rule(slide, x, y, w):
    r = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Pt(2))
    r.fill.solid()
    r.fill.fore_color.rgb = INK
    r.line.fill.background()
    r.shadow.inherit = False


SEQ = {
    "aidesk-pack-02-·-Bots.png": (
        "the_meet/export_mermaid/hi/02-bots.png", "Bots — how a question travels",
        ["A bot is configured once: what it answers, and which data it may touch.",
         "AI-Desk resolves the question into a query — the model never runs it.",
         "AI-Desk hands the query back; the bot executes it directly on DataHub.",
         "Rows return to the bot, and the bot owns the answer. Nothing is cached."]),
    "aidesk-pack-03-·-Enterprise-Search.png": (
        "the_meet/export_mermaid/hi/03-enterprise-search.png", "Enterprise Search — behind the seam",
        ["One question across the estate: warehouse tables and documents.",
         "AI-Desk finds the repository, writes the query, validates it.",
         "DataHub runs it on the source and reflects the rows back.",
         "The agent reasons over them, then the client sees insight and charts."]),
    "aidesk-pack-04-·-Data-Analyst.png": (
        "the_meet/export_mermaid/hi/04-data-analyst.png", "Data Analyst — where the analysis happens",
        ["BYOK: the analyst brings their own key and their own files.",
         "The file is profiled and the SQL drafted inside the browser.",
         "DataHub is the bridge, used only when a real table is needed.",
         "Rows never leave the tab; charts and follow-ups stay in one conversation."]),
}


def sequence_slide(prs, img, heading, bullets):
    from PIL import Image
    s = blank(prs)
    text(s, 0.75, 0.62, 7.6, 0.9, heading, 27, INK, bold=True)
    ink_rule(s, 0.75, 1.42, 1.6)
    iw, ih = Image.open(img).size
    box_w, box_h = 7.6, 5.1
    scale = min(box_w / iw, box_h / ih)
    w, h = iw * scale, ih * scale
    s.shapes.add_picture(img, Inches(0.75), Inches(1.75), width=Inches(w), height=Inches(h))
    text(s, 8.75, 1.55, 3.9, 0.3, "THE SEQUENCE", 11, FAINT, bold=True, tracking=300)
    y = 1.95
    for b in bullets:
        text(s, 8.75, y, 3.95, 0.95, b, 15, MUTED)
        y += 1.15
    text(s, 8.75, 6.45, 3.9, 0.3, "same seam · same DataHub", 12.5, FAINT, italic=True)
    s.notes_slide.notes_text_frame.text = heading + " — " + " ".join(bullets)
    return s


def build():
    prs = Presentation()
    prs.slide_width = Inches(W)
    prs.slide_height = Inches(H)

    # ── opening slide
    s = blank(prs)
    text(s, 1.0, 1.30, 9.0, 0.3, "AI-DESK", 12, FAINT, bold=True, tracking=400)
    text(s, 1.0, 1.62, 11.0, 1.75, ["One framework,", "three experiences"], 50, INK,
         bold=True, spacing=0.95)
    ink_rule(s, 1.0, 3.42, 2.2)
    text(s, 1.0, 3.74, 9.2, 1.0,
         "How AI-Desk powers Enterprise Search, Bots and the Data Analyst — "
         "and how it uses DataHub.", 19, MUTED)
    text(s, 1.0, 6.45, 9.0, 0.3, "Architecture walkthrough", 12.5, FAINT, italic=True)
    s.notes_slide.notes_text_frame.text = (
        "This pack answers one question: what does a client actually get, and who does what behind "
        "the seam. Three experiences, one framework, one system of record.")

    # ── one slide per page, image at full slide size
    for name, _heading, summary, cue in SLIDES:
        path = os.path.join(EXPORT, name)
        if not os.path.exists(path):
            raise SystemExit("missing export: " + path)
        sl = prs.slides.add_slide(prs.slide_layouts[6])
        sl.shapes.add_picture(path, 0, 0, width=prs.slide_width, height=prs.slide_height)
        sl.notes_slide.notes_text_frame.text = summary + "\n\n" + cue
        if name in SEQ:
            img, heading, bullets = SEQ[name]
            sequence_slide(prs, img, heading, bullets)

    # ── closing slide, mirroring the opening
    s = blank(prs)
    text(s, 1.0, 2.30, 9.0, 0.3, "AI-DESK", 12, FAINT, bold=True, tracking=400)
    text(s, 1.0, 2.62, 11.0, 1.0, "Thank you", 54, INK, bold=True)
    ink_rule(s, 1.0, 3.74, 2.2)
    text(s, 1.0, 4.04, 9.2, 0.9,
         "Questions and discussion — on the framework, the three experiences, or what each one "
         "needs from DataHub.", 19, MUTED)
    text(s, 1.0, 6.45, 9.0, 0.3, "Architecture walkthrough", 12.5, FAINT, italic=True)
    s.notes_slide.notes_text_frame.text = (
        "Close on the one platform idea: one framework, three experiences, one system of record. "
        "The capability matrix on the previous slide is the right thing to leave on screen while "
        "questions come in.")

    prs.save(OUT)
    print("wrote %s — %d slides, %.1f MB" % (OUT, len(prs.slides),
                                             os.path.getsize(OUT) / 1048576))


if __name__ == "__main__":
    build()
