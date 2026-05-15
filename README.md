# Resume Parser API

A production-grade FastAPI service that parses resume files (PDF / DOCX / DOC) and returns structured JSON — powered by a **pluggable extraction strategy** (OpenAI, Anthropic, or a local HuggingFace model).

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      FastAPI Server                     │
│                                                         │
│  POST /api/v1/parse                                     │
│       │                                                 │
│       ▼                                                 │
│  ┌────────────┐     ┌──────────────────────────────┐    │
│  │ Auth Layer │──── │       Parser Factory         │    │
│  │ (X-API-Key)│     │  .pdf  → PDFParser (PyMuPDF) │    │
│  └────────────┘     │  .docx → DOCXParser (docx)   │    │
│                     │  .doc  → DOCXParser          │    │
│                     └──────────────┬───────────────┘    │
│                                    │ raw text           │
│                                    ▼                    │
│                     ┌──────────────────────────────┐    │
│                     │    Strategy Factory          │    │
│                     │  (env: EXTRACTION_STRATEGY)  │    │
│                     └──────┬───────────────────────┘    │
│                            │                            │
│          ┌─────────────────┼─────────────────┐          │
│          ▼                 ▼                 ▼          │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐ │
│  │   OpenAI     │ │  Anthropic   │ │  LocalModel      │ │
│  │  Strategy    │ │  Strategy    │ │  Strategy        │ │
│  │  (GPT-4o)    │ │  (Claude)    │ │  NER + GenModel  │ │
│  └──────────────┘ └──────────────┘ └──────────────────┘ │
│          │                 │                 │          │
│          └─────────────────┴─────────────────┘          │
│                            │                            │
│                            ▼                            │
│                     ParsedResume (JSON)                 │
└─────────────────────────────────────────────────────────┘
```

### Design Patterns Used

| Pattern                  | Where                                                 | Why                                                                     |
| ------------------------ | ----------------------------------------------------- | ----------------------------------------------------------------------- |
| **Strategy**             | `app/strategies/`                                     | Swap extraction backends without touching routing logic                 |
| **Factory**              | `app/parsers/factory.py`, `app/strategies/factory.py` | Decouple instantiation from usage; extend by adding to registry         |
| **Dependency Injection** | FastAPI `Depends()`                                   | Strategy and auth injected per-request; easy to mock in tests           |
| **Port / Adapter**       | `BaseParser`, `BaseExtractionStrategy`                | Concrete implementations are interchangeable behind abstract interfaces |

---

## Project Structure

```
resume_parser/
├── app/
│   ├── core/
│   │   ├── config.py          # Pydantic settings (env-driven)
│   │   └── auth.py            # API key dependency
│   ├── models/
│   │   └── resume.py          # ParsedResume output schema
│   ├── parsers/
│   │   ├── base.py            # BaseParser ABC
│   │   ├── pdf_parser.py      # PDFParser  (PyMuPDF)
│   │   ├── docx_parser.py     # DOCXParser (python-docx)
│   │   └── factory.py         # Extension → parser mapping
│   ├── strategies/
│   │   ├── base.py            # BaseExtractionStrategy ABC + shared prompt
│   │   ├── openai_strategy.py
│   │   ├── anthropic_strategy.py
│   │   ├── local_strategy.py  # HuggingFace NER + generative
│   │   └── factory.py         # Env-driven strategy selection
│   ├── routes/
│   │   └── resume.py          # POST /api/v1/parse
│   └── main.py                # FastAPI app + lifespan
├── .env.example
├── requirements.txt
└── README.md
```

---

## Setup

```bash
# 1. Clone / unpack and enter the project
cd resume_parser

# 2. Create virtualenv
python -m venv .venv && source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env — set APP_API_KEY, EXTRACTION_STRATEGY, and the relevant API key

# 5. Run
uvicorn app.main:app --reload --port 8000
```

---

## Environment Variables

| Variable              | Default                              | Description                                        |
| --------------------- | ------------------------------------ | -------------------------------------------------- |
| `APP_API_KEY`         | `changeme`                           | Secret key clients must send in `X-API-Key` header |
| `EXTRACTION_STRATEGY` | `openai` \| `anthropic` \| `local`   |
| `OPENAI_API_KEY`      | —                                    | Required when strategy = `openai`                  |
| `OPENAI_MODEL`        | `gpt-4o`                             | OpenAI model ID                                    |
| `ANTHROPIC_API_KEY`   | —                                    | Required when strategy = `anthropic`               |
| `ANTHROPIC_MODEL`     | `claude-sonnet-4-20250514`           | Anthropic model ID                                 |
| `LOCAL_NER_MODEL`     | `dslim/bert-base-NER`                | HuggingFace NER model                              |
| `LOCAL_GEN_MODEL`     | `mistralai/Mistral-7B-Instruct-v0.2` | HuggingFace generative model                       |
| `LOCAL_DEVICE`        | `cpu`                                | `cpu` or `cuda`                                    |

---

## Usage

### Parse a resume

```bash
curl -X POST http://localhost:8000/api/v1/parse \
  -H "X-API-Key: your-secret-api-key-here" \
  -F "file=@/path/to/resume.pdf"
```
