#!/usr/bin/env python3
"""the_meet/aidesk-pack.drawio — six 16:9 pages about the AI-DESK framework.

Styling: monochrome navy/slate. One dark anchor band (AI-DESK), one light anchor
band (DataHub), white cards. A single warm accent is used only for the takeaway
line, so nothing competes with the content.
"""

import html
import os
import xml.dom.minidom

W, H = 1600, 900

INK, MUTED, FAINT = "#111A24", "#3E4A58", "#65717F"
LINE, HAIR = "#BCC7D4", "#D3DBE5"
PAPER, WASH = "#FFFFFF", "#F1F5F9"
# one light band for AI-DESK; cards on it stay white. No dark fills anywhere.
BAND, BAND_CARD, BAND_LINE = "#E4EAF1", "#FFFFFF", "#AEBACA"
SPINE = "#7C8A9C"                       # the 4px rule on each actor box
ARROW = "#62707F"                       # flow arrows and strong strokes
HUB_T, HUB_S = "#FFFFFF", "#AEBACA"
NOTE_T = "#F1F5F9"                      # "what this means" panel
WARM, WARM_T = INK, NOTE_T

cells: list[str] = []


def vert(cid, value, style, x, y, w, h, parent="1"):
    cells.append(
        f'<mxCell id="{cid}" value="{html.escape(str(value), quote=True)}" style="{style}" '
        f'vertex="1" parent="{parent}"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" '
        f'as="geometry"/></mxCell>')


def edge(cid, src, tgt, style, value="", pts=None):
    arr = ""
    if pts:
        arr = '<Array as="points">' + "".join(f'<mxPoint x="{a}" y="{b}"/>' for a, b in pts) + "</Array>"
    cells.append(
        f'<mxCell id="{cid}" value="{html.escape(str(value), quote=True)}" style="{style}" edge="1" '
        f'parent="1" source="{src}" target="{tgt}"><mxGeometry relative="1" as="geometry">{arr}'
        f'</mxGeometry></mxCell>')


def text(cid, value, x, y, w, h, size=16, bold=False, colour=INK, align="left",
         italic=False, spacing=0):
    style = (f"text;html=1;align={align};verticalAlign=middle;fontSize={size};fontColor={colour};"
             f"spacingLeft={spacing};spacingRight={spacing};whiteSpace=wrap;")
    if bold:
        style += "fontStyle=1;"
    if italic:
        style += "fontStyle=2;"
    vert(cid, value, style, x, y, w, h)


def box(cid, value, x, y, w, h, fill=PAPER, stroke=LINE, size=16, bold=False, align="left",
        spacing=16, dashed=False, radius=6, sw=1.5, colour=None, vcol=None):
    style = (f"rounded=1;arcSize={radius};whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};"
             f"strokeWidth={sw};fontSize={size};align={align};verticalAlign={vcol or 'middle'};"
             f"spacingLeft={spacing};spacingRight={spacing};fontColor={colour or INK};")
    if bold:
        style += "fontStyle=1;"
    if dashed:
        style += "dashed=1;dashPattern=8 6;"
    vert(cid, value, style, x, y, w, h)


def paper():
    """Page background: keeps every export exactly 1600x900 with equal margins."""
    vert("bg", "", f"rounded=0;html=1;fillColor={PAPER};strokeColor=none;", 0, 0, W, H)


def title(t, sub):
    text("t1", t, 60, 26, 1200, 34, size=33, bold=True)
    text("t2", sub, 60, 66, 1440, 22, size=16.5, colour=MUTED)


def seam(y, x0, x1, lx=None):
    style = f"html=1;rounded=0;strokeColor={FAINT};strokeWidth=1.5;dashed=1;dashPattern=7 7;endArrow=none;"
    cells.append(f'<mxCell id="seam" value="" style="{style}" edge="1" parent="1">'
                 f'<mxGeometry relative="1" as="geometry">'
                 f'<mxPoint x="{x0}" y="{y}" as="sourcePoint"/>'
                 f'<mxPoint x="{x1}" y="{y}" as="targetPoint"/></mxGeometry></mxCell>')
    w = 440
    x = lx if lx is not None else (x0 + x1) // 2 - w // 2
    vert("seamlabel", "<b>SEAMS</b> &nbsp;—&nbsp; the only way in: questions and answers, never your data",
         f"rounded=0;html=1;fillColor={PAPER};strokeColor=none;fontSize=11.5;align=left;"
         f"verticalAlign=middle;fontColor={MUTED};spacingLeft=2;",
         x, y - 12, w, 24)


def arrow(cid, src, tgt, colour=FAINT, label="", dashed=False, sw=1.5,
          ex=0.5, ey=1, nx=0.5, ny=0, pts=None):
    style = (f"edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;strokeColor={colour};strokeWidth={sw};"
             f"endArrow=block;endFill=1;endSize=6;exitX={ex};exitY={ey};entryX={nx};entryY={ny};"
             f"fontSize=11.5;fontColor={MUTED};labelBackgroundColor={PAPER};")
    if dashed:
        style += "dashed=1;dashPattern=6 5;"
    edge(cid, src, tgt, style, label, pts)


def numchip(cid, n, x, y):
    vert(cid, n, f"rounded=0;html=1;fillColor={BAND};strokeColor={BAND_LINE};strokeWidth=1;"
                 f"fontColor={INK};fontSize=10.5;fontStyle=1;align=center;verticalAlign=middle;",
         x, y, 20, 20)


# ───────────────────────────────────────────────────────────────── page 1
def page1():
    paper()
    title("One framework, three experiences",
          "Every experience starts at the client. AI-Desk powers the client, and AI-Desk uses DataHub.")

    text("clients_l", "CLIENTS", 60, 104, 300, 20, size=13.5, bold=True, colour=FAINT)
    for i, (pid, name, desc, c1, c2, note) in enumerate([
        ("p1", "BOTS", "configured bots, embedded in your product",
         "Structured", "Unstructured", "uses the chatbot builder and sits within the app"),
        ("p2", "ENTERPRISE SEARCH", "ask the whole estate in plain English",
         "Structured", "Unstructured", "one question across tables and documents"),
        ("p3", "DATA ANALYST", "ad-hoc analysis, on the analyst's own terms",
         "Files", "Tables", "bring your own key (BYOK) — the analyst's own files and tables"),
    ]):
        x = 60 + i * 500
        box(pid, "", x, 130, 470, 274, fill=WASH, stroke=LINE, radius=0)
        box(pid + "rule", "", x, 130, 4, 274, fill=SPINE, stroke=SPINE, radius=0, sw=0)
        numchip(pid + "n", f"0{i + 1}", x + 22, 152)
        text(pid + "t", name, x + 52, 150, 400, 26, size=19, bold=True)
        text(pid + "d", desc, x + 22, 182, 430, 20, size=14.5, colour=MUTED)
        box(pid + "c1", c1, x + 22, 214, 426, 58, size=16, align="center", spacing=8)
        box(pid + "c2", c2, x + 22, 282, 426, 58, size=16, align="center", spacing=8)
        text(pid + "note", note, x + 22, 350, 426, 40, size=13.5, colour=FAINT, italic=True)

    seam(452, 60, 1540, lx=826)

    # AI-DESK — the dark anchor
    box("aidesk", "", 60, 486, 1480, 214, fill=BAND, stroke=BAND_LINE, radius=4, sw=1)
    text("aidesk_t", "AI-DESK", 92, 496, 500, 30, size=25, bold=True, colour=INK)
    text("aidesk_x", "the GenAI framework we coined", 224, 502, 500, 24, size=16,
         colour=MUTED, italic=True)
    text("aidesk_s",
         "agentic AI · workflows · orchestration · analysis over structured <b>and</b> unstructured data "
         "· plus the in-browser analysis path the Data Analyst uses",
         92, 528, 1400, 20, size=14.5, colour=MUTED)

    caps = [("c1", "BOTS",
             "turns the question into a query<br>in the bot's own configured environment",
             "for configured bots"),
            ("c2", "ENTERPRISE SEARCH",
             "finds the data, queries it,<br>then infers over what comes back",
             "for the search experience"),
            ("c3", "UNSTRUCTURED",
             "chunks and embeds documents,<br>then cites the page it answered from",
             "for documents, whichever client asks")]
    for i, (cid, name, line, who) in enumerate(caps):
        x = 92 + i * 484
        box(cid, "", x, 556, 452, 96, fill=BAND_CARD, stroke=BAND_LINE, radius=5, sw=1)
        text(cid + "n", name, x + 18, 562, 416, 22, size=16, bold=True, colour=INK)
        text(cid + "l", line, x + 18, 586, 416, 32, size=13.5, colour=MUTED)
        text(cid + "w", who, x + 18, 620, 416, 18, size=12.5, colour=FAINT, italic=True)
    text("stack", "runs on &nbsp; Cloud Run &nbsp;·&nbsp; Cloud SQL for PostgreSQL + pgvector &nbsp;·&nbsp; "
                 "Cloud Storage (GCS) &nbsp;·&nbsp; Gemini",
         92, 664, 1200, 22, size=13.5, colour=FAINT)

    for pid, fx in [("p1", 0.18), ("p2", 0.5), ("p3", 0.82)]:
        arrow(pid + "_down", pid, "aidesk", colour=FAINT, sw=1.5, ex=0.5, ey=1, nx=fx, ny=0)
    arrow("to_hub", "aidesk", "hub", colour=ARROW, sw=1.5, ex=0.5, ey=1, nx=0.5, ny=0)

    box("hub", "", 60, 720, 1480, 124, fill=HUB_T, stroke=HUB_S, radius=4, sw=1)
    text("hub_t", "DATAHUB", 92, 728, 400, 24, size=19, bold=True, colour=INK)
    text("hub_x", "the system of record", 200, 732, 500, 20, size=14, colour=MUTED, italic=True)
    for i, s in enumerate(["repository catalogue", "source connections", "query engine",
                           "document corpus", "job queue"]):
        box(f"chip{i}", s, 84 + i * 288, 762, 272, 34, size=14, align="center", spacing=6, sw=1,
            fill=WASH)
    for i, s in enumerate(["Blob storage (GCS)", "Structured RDBMS", "Data warehouses"]):
        box(f"st{i}", s, 84 + i * 288, 800, 272, 32, size=13.5, align="center",
            spacing=6, sw=1, dashed=True, colour=MUTED, fill=WASH)

    text("foot", "<b>No long-running agents.</b> An ephemeral Cloud Run instance serves each request "
                 "and dies with it — nothing is de-coupled from the service.",
         60, 858, 1480, 24, size=14.5, colour=WARM)


# ──────────────────────────────────────────────────────── pages 2, 3, 4
CONFIG = {
    "bots": dict(
        title="Bots — configured once, then it answers on its own",
        sub="The bot brings the question. AI-Desk builds the query. The bot executes it on top of DataHub.",
        client="EMBEDDED BOT", client_note="sits within your product — uses the chatbot builder",
        cards=[("Structured", "answers from tables"),
               ("Unstructured", "answers from documents")],
        service="AI-DESK",
        steps=["understands the question in plain English",
               "knows which data this bot may touch",
               "builds the query from the bot's own context"],
        mid="THE BOT", mid_note="takes up the query and runs it on top of DataHub",
        mid_label="the bot takes up the query",
        hub_note="executes against the attached source and returns the rows",
        bullets=["<b>Configure once.</b> What the bot answers, and which data it may touch.",
                 "<b>The bot owns the answer.</b> AI-Desk only builds the query.",
                 "<b>Execution happens on DataHub.</b> Never on the client, never on the model.",
                 "<b>Nothing lingers.</b> The instance dies with the request."],
        stack=["Cloud Run — FastAPI · LangGraph", "Gemini for the reasoning",
               "through DataHub — Cloud SQL + pgvector"]),
    "search": dict(
        title="Enterprise Search — ask, look, infer",
        sub="The client asks. AI-Desk looks at the data DataHub reflects back, and infers before answering.",
        client="ENTERPRISE SEARCH", client_note="one search box over the whole estate",
        cards=[("Structured", "answers from tables"),
               ("Unstructured", "answers from documents")],
        service="AI-DESK",
        steps=["finds the right repository and tables", "writes the query",
               "validates it before anything runs"],
        mid="", mid_note="", mid_label="",
        hub_note="runs the query on the source and reflects the rows back",
        bullets=["<b>The agent looks at the data.</b> DataHub reflects it back; the agent reasons over it.",
                 "<b>Insight, not just rows.</b> Analysis and charts happen before the client sees anything.",
                 "<b>Documents too.</b> Contracts and BOL sit in the same experience.",
                 "<b>Nothing lingers.</b> The instance dies with the request."],
        stack=["Cloud Run — FastAPI · LangGraph", "Gemini for the reasoning",
               "Cloud SQL + pgvector for the built context"]),
    "analyst": dict(
        title="Data Analyst — in the analyst's own browser",
        sub="The analyst's own files, analysed where they already are. AI-Desk does the thinking; "
            "the rows stay in the browser.",
        client="DATA ANALYST",
        client_note="bring your own key (BYOK) — the analyst's own key, on their own files",
        cards=[("Files", "CSV, XLSX, JSON"),
               ("Tables", "a repository, when the question needs one")],
        service="AI-DESK",
        steps=["reads the file and profiles every column",
               "drafts the SQL and runs it in the browser",
               "renders charts and keeps the follow-ups"],
        mid="", mid_note="", mid_label="",
        hub_note="only when the analyst points at a table: catalogue and query execution",
        bullets=["<b>Private by default.</b> Rows never leave the analyst's browser.",
                 "<b>Works on what they have.</b> A spreadsheet is enough to start.",
                 "<b>Charts and follow-ups</b> in the same conversation.",
                 "<b>Bridge to the estate</b> when the question needs a real table."],
        stack=["in the browser — TypeScript · React · DuckDB-WASM",
               "Cloud Run only for the model proxy",
               "bring your own key — the analyst's own"]),
}


def service_page(kind):
    cfg = CONFIG[kind]
    paper()
    title(cfg["title"], cfg["sub"])

    box("client", "", 60, 120, 960, 118, fill=WASH, stroke=LINE, radius=0)
    box("client_rule", "", 60, 120, 4, 118, fill=SPINE, stroke=SPINE, radius=0, sw=0)
    text("client_t", cfg["client"], 84, 128, 500, 24, size=18, bold=True)
    text("client_n", cfg["client_note"], 84, 152, 860, 20, size=13.5, colour=MUTED, italic=True)
    for i, (ct, cd) in enumerate(cfg["cards"]):
        box(f"cc{i}", f"<b>{ct}</b><br><font color='{MUTED}' style='font-size:12.5px'>{cd}</font>",
            84 + i * 450, 180, 430, 46, size=14.5, align="center", spacing=8)

    seam(260, 60, 1020)

    sh = 46 + 30 * len(cfg["steps"]) + 24
    box("svc", "", 60, 292, 960, sh, radius=0)
    box("svc_rule", "", 60, 292, 4, sh, fill=SPINE, stroke=SPINE, radius=0, sw=0)
    text("svc_t", cfg["service"], 84, 300, 700, 26, size=18, bold=True)
    steps_top = 292 + 40
    for i, s in enumerate(cfg["steps"]):
        text(f"svc_s{i}", f"<b>{i + 1}</b>   {s}", 84, steps_top + i * 30, 900, 28, size=15)

    y = 292 + sh
    if cfg["mid"]:
        arrow("a_mid", "svc", "bot", colour=ARROW, label=cfg["mid_label"], ex=0.5, ey=1, nx=0.5, ny=0)
        box("bot", f"<b>{cfg['mid']}</b> &nbsp;—&nbsp; {cfg['mid_note']}", 60, y + 34, 960, 62,
            fill=BAND, stroke=BAND_LINE, size=15.5, align="center", spacing=10, colour=INK, radius=4)
        arrow("a_hub", "bot", "hub", colour=ARROW, ex=0.5, ey=1, nx=0.5, ny=0)
        huby, hubh = y + 170, 176
    else:
        arrow("a_hub", "svc", "hub", colour=ARROW, ex=0.5, ey=1, nx=0.5, ny=0)
        huby, hubh = y + 160, 176

    box("hub", f"<b>DATAHUB</b><br><font color='{MUTED}' style='font-size:14px'>{cfg['hub_note']}</font>"
               f"<br><br><font color='{FAINT}' style='font-size:11.0px'>repository catalogue · connections · "
               f"query engine · document corpus · job queue</font>"
               f"<br><font color='{FAINT}' style='font-size:11.0px'>on Cloud Run · Cloud SQL (PostgreSQL + "
               f"pgvector) · Cloud Storage (GCS)</font>",
        60, huby, 960, hubh, fill=HUB_T, stroke=HUB_S, size=17, align="center", spacing=14, radius=4)

    arrow("a_back", "hub", "client", colour=FAINT, dashed=True, ex=1, ey=0.5, nx=1, ny=0.62,
          pts=[(1046, huby + hubh // 2), (1046, 196)])

    box("notes", "", 1140, 120, 400, 330, fill=NOTE_T, stroke=LINE)
    text("notes_t", "What this means", 1162, 128, 356, 24, size=16, bold=True, colour=INK)
    for i, b in enumerate(cfg["bullets"]):
        text(f"nb{i}", "• " + b, 1162, 164 + i * 70, 356, 66, size=14)

    box("stackbox", "", 1140, 468, 400, 200, fill=WASH, stroke=LINE)
    text("stack_t", "TECH STACK", 1162, 476, 356, 20, size=12.5, bold=True, colour=FAINT)
    for i, line in enumerate(cfg["stack"]):
        text(f"stack{i}", "· " + line, 1162, 500 + i * 40, 356, 36, size=13.5, colour=MUTED)
    text("stack_x", "the instance is ephemeral: stateless, scales to zero", 1162, 626, 356, 22,
         size=12.5, colour=FAINT, italic=True)

    text("foot", "<b>No long-running agents</b> — every caller gets an ephemeral instance that dies "
                 "with the request.", 60, 850, 1480, 24, size=14, colour=WARM)


# ───────────────────────────────────────────────────────────────── page 5
def page5():
    paper()
    title("Three experiences, one framework",
          "One sheet for the walkthrough — three experiences, the same three tiers, the same seam.")

    lanes = [
        ("BOTS", [("The client asks", "in plain English"), ("AI-Desk builds", "the query"),
                  ("The bot executes", "on top of DataHub"), ("DataHub runs it", "on the source"),
                  ("The client answers", "with its rows")]),
        ("ENTERPRISE SEARCH", [("The client asks", "or searches"), ("AI-Desk writes", "and validates the query"),
                               ("DataHub runs it", "and reflects rows"), ("AI-Desk infers", "insight, charts"),
                               ("The client answers", "with evidence")]),
        ("DATA ANALYST", [("The analyst opens", "their own files"), ("AI-Desk profiles", "and drafts"),
                          ("DataHub, if needed", "for a real table"), ("Rows return", "to the browser"),
                          ("Charts and", "follow-ups")]),
    ]
    y = 150
    for li, (name, steps) in enumerate(lanes):
        box(f"lane{li}", "", 60, y, 1480, 176, fill=WASH, stroke=LINE, radius=0)
        text(f"lane{li}_t", name, 86, y + 10, 400, 24, size=14.5, bold=True, colour=MUTED)
        n, sw = len(steps), 262
        gap = (1400 - n * sw) // (n - 1)
        for i, (a, b) in enumerate(steps):
            x = 86 + i * (sw + gap)
            box(f"n{li}{i}",
                f"<b>{a}</b><br><font color='{MUTED}' style='font-size:12.5px'>{b}</font>",
                x, y + 58, sw, 76, size=14.5, align="center", spacing=8)
            if i:
                arrow(f"e{li}{i}", f"n{li}{i-1}", f"n{li}{i}", colour=ARROW, ex=1, ey=0.5, nx=0, ny=0.5)
        y += 205

    text("legend",
         "<b>Every lane is the same three tiers:</b> the client asks · AI-Desk does the thinking · "
         "DataHub touches the data · the answer returns to the client.",
         60, y + 26, 1480, 26, size=14, colour=WARM)


# ───────────────────────────────────────────────────────────────── page 6
def page6():
    paper()
    title("What each experience gets from the framework",
          "Capability comparison for scoping and selection — every experience meets DataHub, never another experience.")

    cols = [("BOTS", 300), ("ENTERPRISE SEARCH", 700), ("DATA ANALYST", 1100)]
    cw = 400
    box("hdr_l", "", 60, 126, 240, 46, fill=BAND, stroke=BAND_LINE, radius=0, sw=1)
    for name, x in cols:
        box(f"hdr_{name}", name, x, 126, cw, 46, fill=BAND, stroke=BAND_LINE, radius=0, sw=1,
            size=15, bold=True, align="center", spacing=6, colour=INK)

    rows = [
        ("Runs as", ["Cloud Run — FastAPI, LangGraph", "Cloud Run — FastAPI, LangGraph",
                     "the analyst's browser — TypeScript, React"]),
        ("Data it uses", ["warehouse tables, through a repository",
                          "warehouse tables and documents",
                          "the analyst's own files: CSV, XLSX, JSON"]),
        ("Who runs the query", ["the bot, on top of DataHub", "AI-Desk, through DataHub",
                                "the browser's own engine (DuckDB)"]),
        ("Where the rows live", ["returned to the bot, not cached",
                                 "reflected back for inference",
                                 "in the tab — rows never leave it"]),
        ("Documents", ["through the Unstructured service",
                       "contracts and BOL, in the same experience", "not used"]),
        ("Reads from DataHub", ["schema, business context, hints",
                                "schema, business context, document corpus",
                                "repository catalogue and table metadata"]),
        ("Writes to DataHub", ["nothing — read-only", "nothing — read-only",
                               "nothing — read-only"]),
        ("Model access", ["shared — the platform's key", "shared — the platform's key",
                           "bring your own key"]),
    ]
    y = 172
    rh = 78
    for i, (label, values) in enumerate(rows):
        fill = PAPER if i % 2 == 0 else "#FBFCFD"
        box(f"l{i}", label, 60, y, 240, rh, fill=WASH, stroke=HAIR, radius=0, sw=1,
            size=13.5, bold=True, align="left", spacing=14)
        for (name, x), v in zip(cols, values):
            box(f"r{i}_{name}", v, x, y, cw, rh, fill=fill, stroke=HAIR, radius=0, sw=1,
                size=13.5, align="left", spacing=14, colour=MUTED)
        y += rh

    text("foot", "One platform, one truth: no experience owns a copy of the data, and every one of them "
                 "reaches it through the same seam.", 60, 842, 1480, 26, size=14, colour=WARM)


# ─────────────────────────────────────────────────────────────── assemble
def diagram(did, name, builder):
    global cells
    cells = []
    builder()
    body = "\n        ".join(cells)
    return f'''  <diagram id="{did}" name="{name}">
    <mxGraphModel dx="1422" dy="798" grid="0" gridSize="10" guides="0" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="{W}" pageHeight="{H}" math="0" shadow="0">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        {body}
      </root>
    </mxGraphModel>
  </diagram>
'''


PAGES = [
    ("a1", "01 · One framework", page1),
    ("a2", "02 · Bots", lambda: service_page("bots")),
    ("a3", "03 · Enterprise Search", lambda: service_page("search")),
    ("a4", "04 · Data Analyst", lambda: service_page("analyst")),
    ("a5", "05 · Three lanes", page5),
    ("a6", "06 · Capability matrix", page6),
]

out = ['<mxfile host="app.diagrams.net" agent="pi" version="24.7.7">']
out += [diagram(d, n, f) for d, n, f in PAGES]
out.append("</mxfile>\n")
document = "".join(out)

xml.dom.minidom.parseString(document)
os.makedirs("the_meet", exist_ok=True)
with open("the_meet/aidesk-pack.drawio", "w", encoding="utf-8") as fh:
    fh.write(document)
print("written + XML valid: the_meet/aidesk-pack.drawio (6 pages)")
