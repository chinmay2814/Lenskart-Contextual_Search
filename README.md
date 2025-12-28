# Lenskart AI-Powered Contextual Search Platform

An intelligent product search platform that understands natural language queries, learns from user behavior, and provides explainable AI-powered results.

## Features

- **Semantic Search**: Understands natural language queries like "stylish sunglasses for men under 5000"
- **Query Expansion**: AI automatically expands queries with related terms
- **Behavioral Learning**: Rankings improve based on clicks, carts, and purchases
- **Explainable Results**: AI explains why each product was shown
- **Real-time Event Tracking**: Asynchronous event processing for non-blocking operations

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FastAPI Server                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  Products   │  │   Search    │  │   Events    │              │
│  │    API      │  │    API      │  │    API      │              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
│         │                │                │                      │
│  ┌──────┴──────┐  ┌──────┴──────┐  ┌──────┴──────┐              │
│  │  Ingestion  │  │   Search    │  │   Event     │              │
│  │  Service    │  │   Service   │  │  Processor  │              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
│         │                │                │                      │
│  ┌──────┴────────────────┴────────────────┴──────┐              │
│  │              Service Layer                     │              │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐       │              │
│  │  │Embedding │ │ Ranking  │ │ Learning │       │              │
│  │  │ Service  │ │ Service  │ │ Service  │       │              │
│  │  └──────────┘ └──────────┘ └──────────┘       │              │
│  │  ┌──────────────────────────────────┐         │              │
│  │  │        AI Service (Groq)         │         │              │
│  │  │  - Query Expansion               │         │              │
│  │  │  - Result Explanations           │         │              │
│  │  └──────────────────────────────────┘         │              │
│  └───────────────────────────────────────────────┘              │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │     SQLite      │  │    ChromaDB     │  │  Asyncio Queue  │  │
│  │   (Products,    │  │   (Vectors,     │  │    (Events)     │  │
│  │    Events)      │  │   Embeddings)   │  │                 │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI (Python) |
| Structured Database | SQLite |
| Vector Database | ChromaDB (embedded) |
| Embeddings | Sentence Transformers (all-MiniLM-L6-v2) |
| LLM | Groq (Llama 3.1 70B) |
| Event Queue | Asyncio Queue |

## Quick Start

### Prerequisites

- Python 3.10+
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/lenskart-contextual-search.git
   cd lenskart-contextual-search
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   .\venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   # Copy example env file
   cp .env.example .env
   
   # Edit .env and add your Groq API key
   # Get free API key at: https://console.groq.com/
   ```

5. **Seed sample data**
   ```bash
   python scripts/seed_data.py
   ```

6. **Run the server**
   ```bash
   python -m uvicorn app.main:app --reload
   ```

7. **Open API docs**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## API Endpoints

### Products

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/products/` | Create a single product |
| POST | `/products/batch` | Create multiple products |
| POST | `/products/upload/json` | Upload products from JSON file |
| POST | `/products/upload/csv` | Upload products from CSV file |
| GET | `/products/` | List all products |
| GET | `/products/{id}` | Get product by ID |
| DELETE | `/products/{id}` | Delete product |

### Search

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/search/` | Full contextual search with AI features |
| GET | `/search/quick` | Quick search without AI |
| GET | `/search/similar/{id}` | Find similar products |
| POST | `/search/with-filters` | Search with query parameters |

### Events

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/events/` | Track any event |
| POST | `/events/batch` | Track multiple events |
| POST | `/events/click` | Track click event |
| POST | `/events/cart` | Track add-to-cart |
| POST | `/events/purchase` | Track purchase |
| POST | `/events/dwell` | Track dwell time |
| GET | `/events/recent` | Get recent events |
| GET | `/events/stats` | Get event processor stats |

### Analytics

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/analytics/summary` | Get analytics summary |
| GET | `/analytics/top-products` | Get top products by behavior |
| POST | `/analytics/recalculate-scores` | Recalculate all behavior scores |
| GET | `/analytics/product/{id}/behavior` | Get product behavior metrics |

## Data Flow

### Search Flow

1. User submits natural language query
2. AI expands query with related terms (optional)
3. Query is converted to embedding vector
4. ChromaDB performs semantic similarity search
5. Results are fetched from SQLite
6. Ranking service combines semantic + behavioral scores
7. AI generates explanations for each result
8. Ranked results returned to user

### Learning Flow

1. User interactions (clicks, carts, purchases) are tracked
2. Events are pushed to async queue
3. Background worker processes events
4. Behavior scores are updated in real-time
5. Future searches incorporate learned signals

## Behavioral Scoring Formula

```python
final_score = (semantic_score * 0.6) + (behavior_score * 0.4)

behavior_score = (
    click_rate * 0.3 +
    cart_rate * 0.3 +
    conversion_rate * 0.3 +
    normalized_dwell_time * 0.1
) - (bounce_rate * 0.2)
```

## AI Features

### Query Expansion

Expands user queries with related terms:
- Input: "sunglasses"
- Output: "sunglasses shades UV protection eyewear polarized glasses sun glasses"

### Result Explanations

Generates human-readable explanations:
- "Shown because: matches 'aviator style', high customer rating (4.5/5), frequently purchased with similar searches"

## Sample Queries

Try these searches to test the system:

- "stylish sunglasses for men under 5000"
- "blue light blocking glasses for computer"
- "polarized aviator sunglasses gold"
- "lightweight titanium frames"
- "kids eyeglasses flexible"
- "progressive reading glasses"

## Project Structure

```
lenskart-search/
├── app/
│   ├── api/
│   │   └── routes/          # API endpoints
│   ├── db/                   # Database layer
│   ├── models/               # SQLAlchemy models & Pydantic schemas
│   ├── services/             # Business logic
│   ├── workers/              # Background processors
│   ├── config.py             # Configuration
│   └── main.py               # FastAPI app
├── data/
│   └── sample_eyewear.json   # Sample dataset
├── scripts/
│   ├── seed_data.py          # Data seeding
│   └── generate_sample_events.py
├── tests/                    # Unit tests
├── requirements.txt
├── .env.example
└── README.md
```

## Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_search.py -v

# Generate sample events for testing learning
python scripts/generate_sample_events.py 100
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| GROQ_API_KEY | Groq API key for LLM features | Required |
| SQLITE_DB_PATH | Path to SQLite database | ./data/lenskart.db |
| CHROMA_DB_PATH | Path to ChromaDB storage | ./data/chroma_db |
| EMBEDDING_MODEL | Sentence transformer model | all-MiniLM-L6-v2 |
| LLM_MODEL | Groq LLM model | llama-3.1-70b-versatile |
| SEMANTIC_WEIGHT | Weight for semantic score | 0.6 |
| BEHAVIOR_WEIGHT | Weight for behavior score | 0.4 |

## Evaluation Criteria Coverage

| Criteria | Weight | Implementation |
|----------|--------|----------------|
| Search relevance & quality | 25% | Semantic search with ChromaDB, query expansion |
| Data pipeline design | 20% | Reusable ingestion pipeline, batch processing |
| Learning from behavior | 20% | Event tracking, behavior scoring, ranking adjustments |
| Code quality & modularity | 20% | Clean architecture, separation of concerns |
| AI integration quality | 15% | Query expansion, result explanations via Groq |

## License

MIT License

## Author

Built for Lenskart SDE Assignment

