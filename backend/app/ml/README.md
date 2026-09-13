# BharatLens — Machine Learning Subsystem

> **Tagline:** “News with a wider perspective”  
> **Mission:** “BharatLens — See India. See the World.”

---

## 1. Overview & Architecture

The BharatLens ML subsystem provides lightweight, transparent, and explainable Machine Learning capabilities using Python and `scikit-learn`.

### Subsystem Structure
```
backend/app/ml/
    ├── __init__.py               # Package public interfaces
    ├── text_processing.py        # Text combination & normalization
    ├── category_classifier.py    # TF-IDF + Logistic Regression classification
    ├── similarity.py             # TF-IDF + Cosine similarity & near-duplicate logic
    ├── train.py                  # Reproducible training & evaluation script
    ├── data/
    │   └── sample_dataset.json   # Seed bootstrap dataset (DEMO / BOOTSTRAP DATA)
    ├── models/
    │   └── category_model.joblib # Serialized model pipeline artifact
    └── README.md                 # Subsystem documentation
```

---

## 2. Category Classification

The classifier predicts one of the **11 standard BharatLens categories**:
- `politics`
- `sports`
- `technology`
- `business`
- `movies-entertainment`
- `education`
- `science`
- `health`
- `lifestyle`
- `crime`
- `environment`

### ML Pipeline Architecture
```
Raw Article Title + Description
              ↓
  Text Preprocessing & Normalization (whitespace, lowercase)
              ↓
  TF-IDF Vectorizer (1-2 ngrams, sublinear TF, stop_words='english')
              ↓
  Logistic Regression (Multinomial lbfgs, C=1.0, random_state=42)
              ↓
  Category Prediction + Calibrated Probability Confidence
```

---

## 3. Training Dataset & Reproducibility

- **Dataset Location:** `backend/app/ml/data/sample_dataset.json`
- **Dataset Nature:** Marked explicitly as **DEMO / BOOTSTRAP TRAINING DATA**. Contains synthetic, balanced news headlines and descriptions across all 11 categories (8 samples per category = 88 samples).
- **Reproducibility:** A fixed `random_state=42` is used across all train/test splits and estimators.

### Training Command
To train the model and save the artifact:
```bash
python -m app.ml.train
```

### Evaluation Output
The training script executes a stratified 75/25 train/test split and calculates:
- Overall Accuracy
- Precision (Macro & Weighted)
- Recall (Macro & Weighted)
- F1-Score (Macro & Weighted)

The trained pipeline is persisted via `joblib` to `backend/app/ml/models/category_model.joblib`.

---

## 4. Ingestion Decision Flow & Fallback Safety

The ingestion pipeline respects a strict priority order where **Reliability > Forcing ML**:

```
Article Ingested
       ↓
1. Direct Provider Category Check:
   If the upstream news provider supplies a valid category (e.g. 'sports', 'business'),
   respect and return it directly.
       ↓ (if unprovided / unmapped)
2. ML Category Classification (Conservative Gate):
   Query ML model. Only accept if predicted probability >= 0.18 (~2x uniform 1/11 random baseline).
       ↓ (if missing, error, or confidence < 0.18)
3. Deterministic Keyword Fallback:
   Score text against curated domain keyword heuristics.
       ↓ (if no keyword matches)
4. Default Safety Category:
   Return 'politics'.
```

### Confidence Threshold Selection Rationale:
- In an 11-class problem, the uniform random baseline is `1/11 ≈ 9.09% (0.0909)`.
- On high-confidence domain news, winning class probabilities reach `0.18 – 0.25+`.
- A conservative threshold of `0.18` (approx. 2× baseline) ensures the ML classifier only accepts predictions with strong discriminative signals, safely delegating ambiguous cases to deterministic rules.

---

## 5. Similarity & Near-Duplicate Detection

The `similarity.py` module computes explainable term-frequency cosine similarity:
- `calculate_similarity(text_a, text_b)`: Computes pairwise cosine similarity strictly bounded in `[0.0, 1.0]`.
- `is_near_duplicate(text_a, text_b, threshold=0.85)`: Configurable threshold test for near-duplicate identification.
- `group_similar_articles(articles, threshold=0.40)`: Foundational helper for clustering multi-source coverage of the same event without modifying database schema.

### Example Similarity Profile:
- **Identical Texts:** `1.000`
- **Strong Near-Duplicates:** `0.85 – 0.95`
- **Thematically Related Articles:** `0.40 – 0.60`
- **Completely Unrelated Articles:** `0.000`

> **Note:** Primary article deduplication during ingestion continues to use the deterministic SHA-256 `url_hash` mechanism. Cosine similarity acts as an analytical foundation for future story grouping.

---

## 6. Limitations & Project Scope

> [!NOTE]
> The Phase 7 ML system is a lightweight demonstration model intended for academic and project purposes. It operates on a synthetic bootstrap dataset and does not claim production-grade real-world generalization. No deep learning, large language models, vector databases, or user-tracking recommendation algorithms are used.
