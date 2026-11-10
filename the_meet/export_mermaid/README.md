# the_meet — Mermaid export

Mermaid sources (`.mmd`) and their PNG renders for the six `the_meet` pages, so the
same six diagrams exist in editable text form as well as in the drawio pack.

| Page | Mermaid source | PNG | Diagram type |
|---|---|---|---|
| 01 · One framework, three experiences | `01-one-framework.mmd` | `01-one-framework.png` | flowchart TD, banded |
| 02 · Bots | `02-bots.mmd` | `02-bots.png` | sequenceDiagram, 3 lifelines |
| 03 · Enterprise Search | `03-enterprise-search.mmd` | `03-enterprise-search.png` | sequenceDiagram, 3 lifelines |
| 04 · Data Analyst | `04-data-analyst.mmd` | `04-data-analyst.png` | sequenceDiagram, 3 lifelines |
| 05 · Three lanes | `05-three-lanes.mmd` | `05-three-lanes.png` | flowchart LR, lanes |
| 06 · Capability matrix | `06-capability-matrix.mmd` | `06-capability-matrix.png` | block-beta, 4-column grid |

Content comes from `the_meet/generate.py` (the drawio source of truth) and the
exports in `the_meet/export/`. Wording is near-verbatim; layout is what mermaid
can express.

## Conventions

Deliberate, so edits stay consistent across the pack:

- **Exactly three actors, always: `CLIENT`, `AI-DESK`, `DATAHUB`.**
  The bot *is* the client — the configured bot lives in the client's product — so
  there is no separate `BOT` lifeline. AI-DESK is the one system that interfaces
  DATAHUB; the client only talks to AI-DESK.
- **Two system names only: `AI-DESK` and `DATAHUB`.** No `AI-DESK · Bots service`,
  no `· Search service`, no `· analysis service`.
- **The three services are sequence diagrams** (02, 03, 04): internal steps are
  self-messages on the AI-DESK lifeline, and the answer returns to the client as a
  dashed arrow.
- **AI-DESK never executes in the Bots flow.** It builds the query and hands it
  back to the client (dashed arrow); the client runs it on DATAHUB directly, so the
  model is out of the execution path. 05 and 06 say the same thing in their own
  form ("the client runs it directly on DATAHUB", "the client's bot, directly on
  DATAHUB").
- **04 wraps the client in a `box`.** AI-DESK is a shippable solution, so for the
  Data Analyst it runs *inside* the client: profiling, SQL and charts all happen in
  the browser and nothing is sent out to AI-DESK. Only DATAHUB sits outside the box,
  and only for a real table. 02 and 03 keep AI-DESK as a separate tier because there
  the client genuinely calls it.
- **`mirrorActors: false`** so mermaid does not print a second set of actor boxes at
  the bottom of the diagram — pointless on a slide.
- **`diagramMarginX/Y: 20`** so the last message is not flush with the image edge.
- **Every diagram has a title** in frontmatter, taken from the page title.
- **Flowcharts use `curve: step`** so connectors are orthogonal, like the drawio pages.

## Render

```bash
./render.sh                    # every .mmd -> PNG, via the local Mermaid MCP
./render.sh 02-bots.mmd        # one diagram
THEME=forest ./render.sh       # override theme (default: neutral)
```

`render.sh` POSTs each file to `http://127.0.0.1:1122/mcp`
(`generate_mermaid_diagram`, `outputType: base64`) and decodes the returned PNG.
The server is the self-hosted `mcp-mermaid` container; start it with
`../../scripts/mermaid-mcp.sh up`, check with `../../scripts/mermaid-mcp.sh status`.
No local mermaid-cli, no Chromium in this repo.

## Mermaid constraints hit while writing these

Each of these silently produces a worse diagram, so they shape the files:

- **Frontmatter must be the first thing in the file** — comments before `---` break
  parsing (`Parse error ... got 'LINK'`).
- **`Note over` renders as a dark block** in the `neutral` theme, against the pack's
  "no dark panels" rule. Internal steps are self-messages instead.
- **A self-message on the leftmost lifeline puts its label outside the actor column**,
  so CLIENT self-messages are kept short; everything else is said on AI-DESK.
- **`direction` inside a subgraph is ignored** when that subgraph has an edge crossing
  its boundary — 01 keeps its bands as single nodes for this reason.
- **A subgraph holding one node draws its label across that node**; use styled nodes
  for single elements.
- **Isolated subgraphs are placed bottom-up** under `flowchart LR`, so 05 defines its
  lanes ANALYST → SEARCH → BOTS to render BOTS first.
- **Flowcharts cannot align columns** — 06 uses `block-beta ... columns 4` for a real
  matrix, with a spanning first row for the title (block-beta ignores frontmatter
  titles).
- **Default `wrappingWidth` is 200px**, which turns wide bands into narrow columns;
  each flowchart sets it explicitly.
