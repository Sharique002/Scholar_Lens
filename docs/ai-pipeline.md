# AI Pipeline — Scholar Lens

## Overview

Scholar Lens uses a modular AI service architecture that abstracts all AI interactions behind a clean service layer. This ensures AI logic is separated from Django views and can be swapped independently.

## Service Architecture

```
┌─────────────────────────────────────────┐
│              AI Orchestrator             │
│                                          │
│  ┌──────────────┐  ┌────────────────┐   │
│  │  AIService    │  │  PaperProcessor│   │
│  │  (API Client) │  │  (PDF → Text)  │   │
│  └──────┬───────┘  └───────┬────────┘   │
│         │                   │            │
│  ┌──────▼──────────────────▼──────────┐ │
│  │         Service Classes             │ │
│  │  PaperSummarizer                    │ │
│  │  ResearchGapDetector                │ │
│  │  ResearchQuestionAnswerer (RAG)     │ │
│  │  SemanticSearchService              │ │
│  │  ResearchEvaluator                  │ │
│  │  SimilarityAnalyzer                 │ │
│  └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

## AIService — Core Abstraction

The `AIService` class wraps all OpenAI API interactions:

- **`is_configured`** — Checks if API key is present
- **`chat_completion(system_prompt, user_prompt)`** — Makes chat completion requests with JSON response format
- **`generate_embedding(text)`** — Generates text embeddings for semantic search

### Error Handling
- `AIServiceNotConfigured` — Raised when API key is missing
- `AIServiceError` — Raised on API failures
- All errors are caught and logged, never exposed to users as stack traces

## PDF Processing Pipeline

```
PDF Upload → Validate (.pdf, size limit, encryption check)
    → Store in media/papers/
    → Extract text page-by-page (PyMuPDF)
    → Detect academic section headers (Abstract, Intro, Method, Experiments, Results, Discussion, Conclusion)
    → Count pages and words
    → Clean text and compute character offsets
    → Split into page-aware chunks (500 words, 100 overlap)
    → Generate embeddings for each chunk
    → Store PaperChunk (with page_number, section, offsets) + PaperEmbedding objects
    → Update paper status: UPLOADED → TEXT_EXTRACTED → INDEXED
```

### Chunking Strategy
- **Chunk size**: ~500 words per page
- **Overlap**: 100 words between consecutive chunks
- **Metadata preserved**: `page_number`, `section`, `start_offset`, `end_offset`
- **Purpose**: Enables exact source-aware RAG citations ([1] Methodology — Page 4)

## Feature Pipelines

### 1. Paper Summarization
```
Paper text → System prompt (structured extraction)
    → GPT-4o-mini → JSON response
    → Parse: summary, research_problem, methodology,
             datasets, key_findings, limitations,
             future_work, keywords
    → Store as AIAnalysis (type=SUMMARY)
    → Cache for future requests
```

### 2. Research Gap Detection
```
Paper text → System prompt (gap analysis)
    → GPT-4o-mini → JSON response
    → Parse: list of gaps with title, description,
             area, severity, suggestions
    → Store as ResearchGap objects
    → Cache analysis
```

### 3. RAG Question Answering
```
User question → Vector similarity against chunk embeddings (or lexical scoring)
    → Retrieve top relevant chunks with section & page metadata
    → Build structured context with numbered citations [1], [2]
    → System prompt + context + question → GPT-4o-mini
    → Grounded answer with verifiable section & page citations
    → If evidence insufficient, returns clear non-hallucinating notice
    → Store as ChatMessage with structured sources
```

### 4. Semantic Search
```
Search query → Query embedding or lexical token overlap
    → Multi-factor formula:
        0.60 × Semantic + 0.25 × Lexical + 0.10 × Area + 0.05 × Recency
    → Apply faceted filters (Area, Year, Author, Min Score Threshold)
    → Return ranked papers with score breakdown
```

### 5. Research Evaluation
```
Paper text → System prompt (canonical 7-dimension evaluation)
    → GPT-4o-mini (or deterministic heuristic fallback) → JSON response
    → Parse scores & structured evidence for canonical 7 dimensions:
        Potential Novelty (20%), Research Gap (15%),
        Methodology (15%), Contribution (15%),
        Evidence Quality (15%), Technical Strength (10%),
        Clarity (10%)
    → Calculate weighted overall score (sum of weights = 100%)
    → Extract supporting evidence (page/section), confidence, limitations
    → Store EvaluationReport + ResearchScore objects with provenance metadata
    → Update paper status to EVALUATED
```

## Caching Strategy

- All AI results are stored in the database after generation
- Subsequent requests check for existing results before calling AI
- This prevents duplicate API calls and unnecessary cost
- Cached results are returned immediately

## Graceful Degradation

When `OPENAI_API_KEY` is not configured:
1. AI service reports `is_configured = False`
2. Views check configuration before attempting AI calls
3. Templates show "AI service not configured" message
4. All non-AI features continue working normally
5. No crashes, no fake results

## Models Used

| Feature | Model | Purpose |
|---------|-------|---------|
| Summarization | gpt-4o-mini | Text analysis and extraction |
| Gap Detection | gpt-4o-mini | Research gap identification |
| Q&A (RAG) | gpt-4o-mini | Contextual question answering |
| Evaluation | gpt-4o-mini | Multi-dimensional scoring |
| Embeddings | text-embedding-3-small | Vector representations |

## Disclaimers

All AI-generated content includes clear disclaimers:
- Results are labeled as "AI-Assessed" or "AI-Generated"
- No claims of academic certainty
- Similarity ≠ plagiarism
- Evaluation scores are analytical aids, not official assessments
