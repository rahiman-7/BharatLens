from typing import List
from fastapi import APIRouter, HTTPException
from app.core.state_languages import (
    StateLanguageMetadata,
    get_all_states_metadata,
    get_state_by_slug,
)

router = APIRouter(prefix="/states", tags=["States"])


@router.get("", response_model=List[StateLanguageMetadata], summary="Get All Indian States and Language Metadata")
def list_states() -> List[StateLanguageMetadata]:
    """Retrieve metadata for all 28 Indian States and 8 Union Territories.
    
    Includes default regional languages, supported language options, native script names,
    and major urban centers for regional news filtering.
    """
    return get_all_states_metadata()


@router.get("/{slug}", response_model=StateLanguageMetadata, summary="Get Specific State Metadata")
def get_state(slug: str) -> StateLanguageMetadata:
    """Retrieve language and geographic metadata for a specific state or UT by slug."""
    state_meta = get_state_by_slug(slug)
    if not state_meta:
        raise HTTPException(status_code=404, detail=f"State with slug '{slug}' not found")
    return state_meta
