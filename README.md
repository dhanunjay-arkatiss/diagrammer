# DataHub & AI-DESK diagram packs

Three generated diagram packs plus the deck, built from source in this repository:

| Pack | Pages | For | Built from |
|---|---|---|---|
| **exec** | 4 — One platform · Capability matrix · Who owns what · Footprint & trust boundary | leadership, commercial conversations | `src/exec/datahub-exec-pack.drawio` |
| **exec / aidesk** | 6 — One framework · Bots · Enterprise Search · Data Analyst · Three lanes · Capability matrix, plus a Mermaid set and a 10-slide deck | client-facing AI-DESK story | `src/exec/aidesk/generate.py` |
| **tech** | 8 — System context · Inside DataHub · Text-SQL transports · DocuQA · WebBot-Lite · Integration contract · Ownership matrix · Flows | engineering, integration | `src/tech/datahub-tech-pack.drawio` |

```bash
./scripts/build.sh          # rebuild all three packs (~2 min)
```

## Layout

```
.
├── README.md                  this file — the only README
├── model/facts.md             every claim traced to a source doc; diagrams must not exceed it
├── src/                       everything editable
│   ├── exec/
│   │   ├── datahub-exec-pack.drawio     the 4-page executive pack
│   │   └── aidesk/
│   │       ├── generate.py              the 6 AI-DESK pages (geometry, wording, palette)
│   │       ├── make_pptx.py             the deck
│   │       └── mermaid/                 .mmd sources + render.sh
│   └── tech/
│       └── datahub-tech-pack.drawio     the 8-page technical pack
├── scripts/
│   ├── build.sh               the one command: generate → export → mermaid → deck
│   ├── drawio-export.sh       ad-hoc export of any single .drawio
│   ├── drawio-mcp.sh          optional draw.io MCP server lifecycle
│   └── mermaid-mcp.sh         the Mermaid service that render.sh needs
└── out/                       generated — the only thing you ship
    ├── exec/
    │   ├── datahub-exec-pack.drawio
    │   ├── export/            4 × PNG + 4 × SVG
    │   └── aidesk/
    │       ├── aidesk-pack.drawio
    │       ├── aidesk-pack.pptx
    │       ├── export/        6 × PNG + 6 × SVG
    │       └── mermaid/       6 × PNG, hi/ for the 3 sequence diagrams
    └── tech/
        ├── datahub-tech-pack.drawio
        └── export/            8 × PNG + 8 × SVG
```

`out/` is written by `scripts/build.sh`, is committed deliberately (it is the shippable artifact
set), and is safe to delete — it rebuilds from `src/`. Never hand-edit inside it.

## Editing

| Edit | To change | Rebuild |
|---|---|---|
| `src/exec/datahub-exec-pack.drawio` | the 4 executive pages | `./scripts/build.sh exec` |
| `src/tech/datahub-tech-pack.drawio` | the 8 technical pages | `./scripts/build.sh tech` |
| `src/exec/aidesk/generate.py` | layout, wording, colours of the 6 AI-DESK pages | `./scripts/build.sh aidesk` |
| `src/exec/aidesk/mermaid/*.mmd` | the Mermaid / sequence set | `./scripts/build.sh aidesk` |

The two DataHub packs are hand-authored `.drawio` XML (uncompressed, one `<diagram>` per page) and are
exported as-is. The AI-DESK pack is generated — edit `generate.py`, never the generated
`out/exec/aidesk/aidesk-pack.drawio`.

In `generate.py` the palette is the block of constants at the top (`INK`/`MUTED`/`FAINT`, `LINE`/`HAIR`,
`PAPER`/`WASH`, `BAND*`, `SPINE`, `ARROW`); page copy lives in `page1()`, `CONFIG[...]` and `page6()`.
Every value is `html.escape`d on write, so type real characters (`&`, not `&amp;`); a literal `<br>`
inside a value means a line break.

## House rules for the diagrams

- **No framework-internal jargon.** No Flyway, no ADR numbers, no `no-data` / `yes-data` on any page.
  Tooling detail belongs in `model/facts.md`, not on a slide.
- **No rounded-corner card soup.** Pages are laid out in bands and lanes; cards are square with a spine
  rule, not floating bubbles.
- **Nothing may overflow its box**, and no arrow may cross text. Both are checked by eye on every
  render before a page is called done.
- **Type is large on purpose** — 33px titles, nothing below 12.5px — so pages survive projection.
- **Prose punctuation matters.** Card bodies are sentences, not run-on fragments.
- Claims must be traceable to `model/facts.md`.

### AI-DESK vocabulary

- **AI-DESK** — the GenAI framework we coined. It hosts the services for Bots, Enterprise Search and
  Unstructured (DocuQA), and adds the in-browser analysis path the Data Analyst uses. On the service
  pages the band is labelled just `AI-DESK`, never `AI-DESK · Bots service`.
- **SEAMS** — the boundary between client and framework: questions and answers cross it, never the data.
- **DataHub** — the system of record: catalogue, connections, query engine, document corpus, job queue.
- **Bring your own key (BYOK)** — always spelled out at least once, never a bare acronym.

## The deck

`out/exec/aidesk/aidesk-pack.pptx` is 13.333 × 7.5 in (16:9): title, `01`, `02`, the Bots sequence, `03`,
its sequence, `04`, its sequence, `06`, thank you. `05 Three lanes` is deliberately not in the deck — the
per-service sequences say it better. Every slide carries speaker notes: a summary of the page, then a
cue for the room.

## Requirements

- **Python 3.10+** with `python-pptx` (`pip install python-pptx`).
- **podman** — exports run draw.io Desktop headlessly in
  `docker.io/rlespinasse/drawio-export:v4.60.0`; `build.sh` pulls it if missing.
- **The Mermaid service** on `127.0.0.1:1122` for the sequence set:

  ```bash
  ./scripts/mermaid-mcp.sh up      # start; nothing starts on its own
  ./scripts/mermaid-mcp.sh status
  ./scripts/mermaid-mcp.sh down
  ```

  A loopback-only container serving the `mcp-mermaid` MCP tools over streamable HTTP. Skip it with
  `./scripts/build.sh --no-mermaid`; the pages and the deck still build.
- **rsvg-convert** (optional) for the `hi/` sequence renders.

## The MCP servers (optional authoring aids)

Two self-hosted MCP servers exist so diagrams never leave this machine. **The build does not need
either** — they are for authoring by prompt.

| Server | Endpoint | Image |
|---|---|---|
| draw.io | `http://127.0.0.1:3001/mcp` | `docker.io/jgraph/drawio-mcp:latest` |
| Mermaid | `http://127.0.0.1:1122/mcp` | `localhost/mcp-mermaid:0.4.1` (built from source) |

Both are Quadlet-managed (`~/.config/containers/systemd/`), published on loopback only, and have no
`[Install]` section — **nothing starts at boot or login**. Start and stop them explicitly:
`./scripts/<name>.sh up|down|status|logs|restart`. `boot-on` opts into autostart; `boot-off` is the
default state. Pi reaches them through `~/.pi/agent/mcp.json` (`exposure: direct`, tools appear as
`mcp__drawio__*` and `mcp__mermaid__*`).

`create_diagram` only returns an `app.diagrams.net` link — Pi has no inline viewer — so verify drawings
by exporting to PNG and looking at it, which is exactly what `build.sh` does.

The Mermaid image is built locally because Docker Hub `susuperli/mcp-mermaid:latest` is 0.2.3 and lacks
`outputType: base64|svg|file`; upstream is 0.4.1. Rebuild with `./scripts/mermaid-mcp.sh build`.
(Upstream hardcodes `serverInfo.version = 0.1.3`, so the handshake always reports that.)

## build.sh options

```bash
./scripts/build.sh                 # all three packs, AI-DESK pages at -s 2 (3202×1802, ~240 dpi)
./scripts/build.sh exec            # one pack: exec | tech | aidesk
./scripts/build.sh aidesk -s 4     # print master for the AI-DESK set (6402×3602, ~480 dpi)
./scripts/build.sh --no-mermaid    # skip the Mermaid set
./scripts/build.sh --no-deck       # skip the pptx
```

The two hand-authored packs have fixed export scales baked into `build.sh` (exec `-s 3`, tech `-s 2`)
because their page sizes differ. Ad-hoc export of one file, without the build:

```bash
./scripts/drawio-export.sh -f png -s 2 some.drawio     # → some/export/some-*.png
./scripts/drawio-export.sh -f svg some.drawio
```

## Things that will bite you

Recorded because each cost real time once:

- **`-s 6` silently clips.** Past roughly 4515 px vertically draw.io drops content — the footer and the
  bottom of a band vanish with no error. `-s 4` is the safe ceiling; always look at a render after
  raising the scale.
- **Never export pages in parallel.** Several containers mounting the same directory with `:Z` deadlock.
  `build.sh` renders one page per container, sequentially: seconds each.
- **Mermaid flowcharts lose their text if you rasterise the SVG** — they use `foreignObject` HTML labels
  that `rsvg-convert` cannot read. `render.sh` renders those through the service and only vector-rasterises
  the sequence diagrams into `hi/`.
- **`scripts/drawio-export.sh` can hang** if a previous container still holds the mount. Clear leftovers
  with `podman ps -a --filter ancestor=docker.io/rlespinasse/drawio-export:v4.60.0` + `podman rm -f`;
  `build.sh` does not depend on it.
- **A literal `<br>` inside a `.drawio` value is invalid XML** in the attribute. In hand-authored packs,
  store `&lt;br&gt;`; the generator escapes for you.
- **Patience with string patches**: an anchored `str.replace` that does not match fails silently. Assert
  the count, re-validate with `xml.dom.minidom`, re-export, then look.

## Sending a pack to someone else

| If they want to… | Send |
|---|---|
| present | `out/exec/aidesk/aidesk-pack.pptx` |
| put a page in a document or wiki | `out/<pack>/export/*.svg` (vector, zoomable) |
| drop a page into slides themselves | `out/<pack>/export/*.png` |
| edit the diagrams | `out/<pack>/*.drawio`, or the `src/` file it came from |
| re-do the sequences | `src/exec/aidesk/mermaid/*.mmd` (plain Mermaid text) |

`model/facts.md` is worth sending too: it is the evidence trail behind every claim on the pages.
