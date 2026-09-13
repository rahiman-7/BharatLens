import math
from datetime import datetime
from typing import Optional, Dict
from app.core.datetime_utils import utc_now
from app.models.article import Article


def calculate_freshness_score(
    published_at: datetime,
    now: Optional[datetime] = None,
    half_life_hours: float = 72.0,
) -> float:
    """Calculate exponential freshness score bounded in [0.0, 1.0]."""
    current_time = now or utc_now()
    delta_hours = max(0.0, (current_time - published_at).total_seconds() / 3600.0)
    return round(math.exp(-delta_hours / half_life_hours), 4)


def calculate_article_score(
    article: Article,
    user_profile: Dict[str, float],
    category_weight: float = 0.70,
    freshness_weight: float = 0.30,
    now: Optional[datetime] = None,
) -> float:
    """Calculate combined recommendation score for a candidate article based on user affinity and freshness.
    
    Formula:
        Score = (Category Affinity * 0.70) + (Freshness * 0.30)
    
    Returns:
        Floating-point score bounded in [0.0, 1.0].
    """
    if not article.category:
        cat_slug = "politics"
    else:
        cat_slug = article.category.slug

    # 1. Category affinity from user interest profile
    cat_affinity = user_profile.get(cat_slug, 0.0)

    # 2. Article freshness score
    freshness = calculate_freshness_score(article.published_at, now=now)

    # 3. Weighted combination
    total_score = (cat_affinity * category_weight) + (freshness * freshness_weight)
    return round(total_score, 4)
