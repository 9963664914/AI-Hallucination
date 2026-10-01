# 🧠 HalluciBench

**HalluciBench** is an open-source Django-based platform for benchmarking AI language models against hallucination detection. It provides a structured pipeline to run benchmark evaluations, score model responses across multiple dimensions, and analyze failure patterns — all through a REST API.

---

## ✨ Features

- 📂 **Dataset Management** — Organize benchmark questions by category, difficulty, and version. Supports unanswerable question testing.
- 🤖 **Model Registry** — Register and manage AI model providers (OpenAI, Anthropic, Google Gemini, Ollama, or a built-in Mock provider).
- 🏃 **Benchmark Runs** — Execute benchmarks against one or more models with async task processing via Celery.
- 🔍 **Multi-Dimensional Evaluation** — Score responses using a suite of pluggable evaluators:
  - **Exact Match** — Token-level exact answer comparison
  - **Semantic Similarity** — Embedding-based semantic alignment
  - **Factuality** — Numerical/entity overlap + abstention detection
  - **Citation** — Source and reference verification
  - **Composite** — Weighted aggregate score
- 📊 **Dashboard** — View aggregated metrics, hallucination rates, and per-model performance
- 🐳 **Docker Support** — Full Docker Compose setup with PostgreSQL and Redis
- 🧪 **Test Suite** — pytest-based test coverage

---

## 🏗️ Project Structure

```
HalluciBench/
├── apps/
│   ├── accounts/           # User authentication
│   ├── api/                # API routing & entry points
│   ├── benchmarks/         # BenchmarkRun, ModelResponse models & Celery tasks
│   ├── dashboard/          # Aggregated metrics & reporting views
│   ├── datasets/           # Dataset, DatasetVersion, BenchmarkQuestion models
│   ├── evaluations/        # EvaluationResult, EvaluationEvidence models
│   │   └── evaluators/     # Pluggable evaluator modules
│   │       ├── base.py
│   │       ├── factuality.py
│   │       ├── exact_match.py
│   │       ├── semantic_similarity.py
│   │       ├── citation.py
│   │       ├── composite.py
│   │       └── registry.py
│   └── models_registry/    # ModelProvider & AIModel management
├── config/                 # Django settings, Celery config, URLs
├── templates/              # HTML templates
├── static/                 # Static assets
├── tests/                  # Test suite
├── docker-compose.yml
├── Dockerfile
├── manage.py
├── pytest.ini
└── requirements.txt
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Redis (for Celery task queue)
- PostgreSQL (optional; SQLite used by default locally)

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/hallucibench.git
cd hallucibench
```

### 2. Create a Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your values:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True

# Database (leave DB_HOST empty to use SQLite locally)
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3

# Redis / Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CELERY_ALWAYS_EAGER=True   # Set True to run tasks synchronously (no Redis needed)

# External AI Provider Keys (optional — falls back to Mock Provider)
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GEMINI_API_KEY=
```

### 5. Run Migrations & Seed Data

```bash
python manage.py migrate
python manage.py seed_data
```

### 6. Start the Development Server

```bash
python manage.py runserver
```

The API will be available at `http://127.0.0.1:8000/`.

---

## 🐳 Docker Setup

Run the full stack (Django + Celery + PostgreSQL + Redis) with a single command:

```bash
docker-compose up --build
```

| Service        | URL / Port              |
|----------------|-------------------------|
| Django API     | `http://localhost:8000` |
| PostgreSQL     | `localhost:5432`        |
| Redis          | `localhost:6379`        |

---

## 🔌 API Overview

The REST API is built with Django REST Framework and documented via `drf-spectacular`.

| Endpoint                      | Description                      |
|-------------------------------|----------------------------------|
| `GET /api/datasets/`          | List all datasets                |
| `POST /api/datasets/`         | Create a new dataset             |
| `GET /api/benchmarks/`        | List benchmark runs              |
| `POST /api/benchmarks/`       | Start a new benchmark run        |
| `GET /api/evaluations/`       | List evaluation results          |
| `GET /api/models/`            | List registered AI models        |
| `GET /api/schema/`            | OpenAPI schema (JSON)            |
| `GET /api/schema/swagger-ui/` | Interactive Swagger docs         |

---

## 🔍 Evaluators

Evaluators live in `apps/evaluations/evaluators/` and all extend `BaseEvaluator`.

### Factuality Evaluator

Detects hallucinations by:

1. **Abstention Check** — For unanswerable questions, verifies the model correctly refuses to answer using known abstention phrases (e.g. *"insufficient information"*, *"cannot answer"*).
2. **Numeric/Entity Overlap** — Extracts numbers from both the expected answer and model response and flags mismatches.
3. **Overconfidence Detection** — Flags responses containing phrases like *"definitively"*, *"without a doubt"*, *"100%"*.
4. **Word Overlap Score** — Computes word-level Jaccard similarity against the ground truth reference.

**Scoring:**

| Overlap   | Score | Label                       |
|-----------|-------|-----------------------------|
| ≥ 0.70    | ~1.0  | ✅ High factual consistency  |
| 0.30–0.69 | 0.5   | ⚠️ Partial alignment         |
| < 0.30    | 0.1   | ❌ High hallucination risk   |

### Error Codes

| Code                  | Meaning                                      |
|-----------------------|----------------------------------------------|
| `failure_to_abstain`  | Model answered an unanswerable question      |
| `fabricated_fact`     | Response contains invented details           |
| `incorrect_fact`      | Numeric or factual mismatch                  |
| `wrong_calculation`   | Mathematical error detected                  |
| `partially_correct`   | Mixed accurate and unsupported claims        |
| `unsupported_claim`   | Assertion lacking evidence                   |
| `contradiction`       | Directly contradicts ground truth            |
| `overconfident_answer`| Hallucination expressed with high certainty  |

---

## 🤖 Supported Model Providers

| Provider  | Type                         |
|-----------|------------------------------|
| Mock      | Built-in offline/testing     |
| OpenAI    | GPT-3.5, GPT-4, GPT-4o, …   |
| Anthropic | Claude 3 family              |
| Google    | Gemini 1.5 / 2.0 family      |
| Custom    | Any HTTP endpoint / Ollama   |

> **Note:** API keys are stored as environment variable references — never as plaintext in the database.

---

## 🧪 Running Tests

```bash
pytest
```

To run with verbose output:

```bash
pytest -v
```

Configuration is in `pytest.ini`.

---

## ⚙️ Async Task Processing

Benchmark runs are executed asynchronously via **Celery**. For local development without Redis, set `CELERY_ALWAYS_EAGER=True` in your `.env` to run tasks synchronously in-process.

For production, start the Celery worker separately:

```bash
celery -A config worker --loglevel=info
```

---

## 🛡️ Security Notes

- Change `SECRET_KEY` before deploying to production.
- Set `DEBUG=False` in production.
- Never commit your `.env` file — it is already listed in `.gitignore`.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

## 🤝 Contributing

Contributions are welcome! Please open an issue or submit a pull request.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -m "feat: add my feature"`
4. Push and open a Pull Request
