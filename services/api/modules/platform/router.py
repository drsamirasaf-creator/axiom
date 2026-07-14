"""Platform messaging routes (Phase 10, ADR-009). Public by design —
this is the shop window; no tenancy involved. REQ-PLT-001."""
from fastapi import APIRouter
from . import content

router = APIRouter(prefix="/api/v1/platform", tags=["platform"])


@router.get("/about")
def about():
    return {**content.ABOUT,
            "intro_video_url": content.intro_video_url()}


@router.get("/pages")
def pages():
    return content.PAGES
