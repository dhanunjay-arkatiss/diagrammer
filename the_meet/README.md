# the_meet — the AI-DESK pack

Six 16:9 pages describing the framework the way it was reviewed with leadership:
**clients at the top, AI-Desk in the middle, DataHub underneath.**

| Page | What it answers |
|---|---|
| `01 · One framework` | The whole picture: three client experiences, the services AI-Desk hosts, DataHub, attached sources, the stack |
| `02 · Bots` | A configured bot asks; AI-Desk builds the query; **the bot executes it on DataHub** |
| `03 · Enterprise Search` | The client asks; the agent looks at the data DataHub reflects back and infers before answering |
| `04 · Data Analyst` | The analyst's own files, analysed where they are; rows stay in the browser, with the analyst's own key |
| `05 · Three lanes` | The same stories on one sheet for the walkthrough |
| `06 · Capability matrix` | What each experience gets from the framework — for scoping and selection |

## Files

| | |
|---|---|
| `aidesk-pack.drawio` | the six pages, generated |
| `generate.py` | source of truth — geometry, wording, palette |
| `export/` | PNG at `-s 2` (3202x1802, ~240 dpi) plus SVG for every page |
| `aidesk-pack.pptx` | the presentation: 10 slides, 16:9, speaker notes |
| `export_mermaid/hi/` | the three sequence diagrams, re-rendered from `.mmd` via SVG at 3400px |
| `make_pptx.py` | builds the deck from `export/` |

## Vocabulary

- **AI-DESK** — the GenAI framework we coined. It hosts the services for Bots, Enterprise Search and
  Unstructured (DocuQA), and adds the in-browser analysis path the Data Analyst uses.
- **SEAMS** — the boundary between client and framework: questions and answers cross it, never the data.
- **DataHub** — the system of record: catalogue, connections, query engine, document corpus, job queue.
- No internal mode names appear on these pages (no `no-data` / `yes-data`).

## Tech stack shown (kept deliberately short)

- **Compute** — Cloud Run, ephemeral and stateless; scales to zero.
- **Data** — Cloud SQL for PostgreSQL + pgvector; Cloud Storage (GCS) for documents and bytes.
- **Services** — FastAPI + LangGraph (both AI-Desk services), Gemini for reasoning,
  TypeScript/React + DuckDB-WASM + OPFS in the browser for the Data Analyst, bring your own key there.
- **Sources** — structured RDBMS and data warehouses (Oracle, PostgreSQL, BigQuery), attached through
  DataHub's connections; the assistant never reaches them directly.

## Styling

One neutral slate family, no dark panels and no heavy contrast — it should read as a technical document.

| Element | Treatment |
|---|---|
| Paper | white `#FFFFFF` |
| Ink / muted / faint | `#111A24` · `#3E4A58` · `#65717F` |
| Borders | `#BCC7D4`, 1px; row separators `#D3DBE5` |
| AI-DESK band | light wash `#E4EAF1` with a 1px border; the service cards on it are white |
| DataHub band | white with a 1px border; its chips are a light wash |
| Actor boxes | white or `#F1F5F9`, with a 4px slate spine (`#7C8A9C`) and a numbered chip |
| Arrows | `#62707F`, 1.5px |
| Footer takeaway | ink, bold lead-in — no accent colour |

There is no colour accent anywhere in the pack. Emphasis comes from weight, the spine rule and the
one light band that marks the framework.

Type is set large on purpose — page titles 33px, section titles 25px, and nothing on the page below
12.5px, so the deck stays readable when projected or printed small. Colour values are deliberately
darker than a pastel palette: mid-slate text on white, not pale grey.

Every page carries a full-bleed white background cell, so each export is exactly 1600x900 with equal
margins.

## Handing this to another team

Two editable sources, everything else is generated:

| Edit this | To change | Then run |
|---|---|---|
| `generate.py` | layout, wording, colours of the six pages | `python3 the_meet/generate.py`, re-export, `make_pptx.py` |
| `export_mermaid/*.mmd` | the Mermaid/sequence set | `cd the_meet/export_mermaid && ./render.sh` |

Editing the `.drawio` by hand works too — it is plain uncompressed XML, one `<diagram>` per page — but
the next `generate.py` run overwrites it. Prefer editing the generator, or fork the `.drawio` before
hand-editing.

Things to know before changing anything:

- Every value is `html.escape`d at write time, so write real text (`&` not `&amp;`); a literal `<br>`
  inside a value means "line break".
- `PAPER`, `INK`, `MUTED`, `BAND`, `SPINE`, `ARROW` at the top of `generate.py` are the whole palette.
  There is no accent colour by design.
- Every page starts with a full-bleed background cell; that is what keeps exports exactly 16:9.
- `-s 2` (3202x1802) is the working resolution, `-s 4` (6402x3602) the print master. **`-s 6` clips**
  the page vertically around 4515 px and silently loses the footer and the bottom of the DataHub band.
- Mermaid flowcharts (01, 05, 06) use HTML labels, so their SVG text does not survive `rsvg-convert`;
  render those with `render.sh`, not by rasterising the SVG.

## Regenerating

```bash
python3 the_meet/generate.py                                            # .drawio, 6 pages
./scripts/drawio-export.sh -f png -s 2 the_meet/aidesk-pack.drawio      # PNG for slides
./scripts/drawio-export.sh -f svg the_meet/aidesk-pack.drawio           # SVG for zoom/docs
python3 the_meet/make_pptx.py                                           # aidesk-pack.pptx

cd the_meet/export_mermaid && ./render.sh                               # Mermaid sources -> PNG
```

## Presenting

`aidesk-pack.pptx` is 13.333 x 7.5 in (16:9) and runs: title, `01 One framework`, `02 Bots`, the Bots
sequence, `03 Enterprise Search`, its sequence, `04 Data Analyst`, its sequence, `06 Capability
matrix`, thank you. `05 Three lanes` is deliberately not in the deck — the per-service sequences say
it better. Every slide carries speaker notes: a summary of what the page says, then a cue for the room.

Pages are embedded at `-s 2` (3202 x 1802, ~240 dpi at slide size — sharp enough when projected or
printed, and quick to regenerate); the sequence slides use the 3400 px renders in
`export_mermaid/hi/`. Raise to `-s 4` (6402 x 3602) for a print master. **`-s 6` is broken** —
draw.io clips the page vertically past roughly 4515 px, silently dropping the footer and the bottom
of the DataHub band, so never raise the scale without checking a render.

Export speed trick: rendering the six-page file in one container takes minutes and can wedge, and
six containers in parallel deadlock on the shared `:Z` mount. Split the pages into single-page
`.drawio` files and export them **one at a time** with a direct `podman run` — all six at `-s 2` take
about 16 seconds total. The `scripts/drawio-export.sh` wrapper has been observed hanging; calling
`podman run` directly is reliable.

## Mermaid export

`the_meet/export_mermaid/` holds a Mermaid version of each of the six pages — `.mmd`
source plus rendered `.png` — written from the same wording and structure as the
drawio pages, and rendered through the local Mermaid MCP server. See
[`export_mermaid/README.md`](export_mermaid/README.md) for the page map, and for the
mermaid layout constraints that shaped them (subgraph `direction`, column alignment,
note colouring, wrap width).

`generate.py` is the source of truth — geometry, wording and colours live there. Values are HTML-escaped
at write time, so never hand-write `<br>` into the XML.
