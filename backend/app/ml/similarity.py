import logging
from typing import Optional, List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.ml.text_processing import preprocess_text

logger = logging.getLogger("bharatlens.ml.similarity")


def calculate_similarity(
    text_a: Optional[str],
    text_b: Optional[str],
    description_a: Optional[str] = None,
    description_b: Optional[str] = None,
) -> float:
    """Calculate TF-IDF cosine similarity between two text snippets.
    
    Returns:
        Float value strictly bounded between 0.0 and 1.0.
    """
    clean_a = preprocess_text(text_a, description_a)
    clean_b = preprocess_text(text_b, description_b)

    if not clean_a or not clean_b:
        return 0.0

    if clean_a == clean_b:
        return 1.0

    try:
        vectorizer = TfidfVectorizer(
            ngram_range=(1, 1),
            stop_words="english",
            use_idf=False,
            norm="l2",
        )
        tfidf_matrix = vectorizer.fit_transform([clean_a, clean_b])
        cos_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        score = float(max(0.0, min(1.0, cos_sim)))
        return round(score, 4)
    except Exception as e:
        logger.warning(f"Error calculating text similarity: {e}")
        return 0.0


def is_near_duplicate(
    text_a: Optional[str],
    text_b: Optional[str],
    threshold: float = 0.85,
    description_a: Optional[str] = None,
    description_b: Optional[str] = None,
) -> bool:
    """Determine whether two articles are near-duplicates using a configurable similarity threshold.
    
    Args:
        text_a: Primary text or title for article A.
        text_b: Primary text or title for article B.
        threshold: Floating-point threshold in (0.0, 1.0]. Defaults to 0.85.
        description_a: Optional description for article A.
        description_b: Optional description for article B.
    
    Returns:
        True if cosine similarity is greater than or equal to the threshold.
    """
    score = calculate_similarity(text_a, text_b, description_a, description_b)
    return score >= threshold


def group_similar_articles(
    articles: List[Dict[str, Any]],
    threshold: float = 0.75,
) -> List[List[Dict[str, Any]]]:
    """Foundational helper to cluster a list of articles into story groups based on pairwise similarity.
    
    This provides the building block for future multi-source story clustering without modifying the DB.
    """
    if not articles:
        return []

    groups: List[List[Dict[str, Any]]] = []

    for article in articles:
        title = article.get("title", "")
        desc = article.get("description", "")
        placed = False

        for group in groups:
            # Check similarity against the representative (first) article in the group
            rep_title = group[0].get("title", "")
            rep_desc = group[0].get("description", "")
            
            sim = calculate_similarity(title, rep_title, desc, rep_desc)
            if sim >= threshold:
                group.append(article)
                placed = True
                break

        if not placed:
            groups.append([article])

    return groups
