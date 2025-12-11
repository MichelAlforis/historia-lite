"""AI Advisor API routes for Historia Lite"""
import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.game_state import get_world
from ai.ai_advisor import (
    ai_advisor,
    StrategicAdvice,
    DiplomaticDialogue,
    AnnualBriefing,
    MediaComment,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ai-advisor", tags=["AI Advisor"])


# ============================================================================
# Response Models
# ============================================================================

class StrategicAdviceResponse(BaseModel):
    success: bool
    advices: List[StrategicAdvice] = []
    error: Optional[str] = None


class DiplomaticDialogueResponse(BaseModel):
    success: bool
    dialogue: Optional[DiplomaticDialogue] = None
    error: Optional[str] = None


class BriefingResponse(BaseModel):
    success: bool
    briefing: Optional[AnnualBriefing] = None
    error: Optional[str] = None


class MediaCommentResponse(BaseModel):
    success: bool
    comment: Optional[MediaComment] = None
    error: Optional[str] = None


class OpportunityEventResponse(BaseModel):
    success: bool
    event: Optional[dict] = None
    error: Optional[str] = None


class ChatRequest(BaseModel):
    country_id: str
    message: str
    context: Optional[dict] = None
    conversation_history: Optional[List[dict]] = None


class ChatResponse(BaseModel):
    success: bool
    response: Optional[str] = None
    error: Optional[str] = None


# ============================================================================
# Routes
# ============================================================================

@router.get("/advice/{country_id}", response_model=StrategicAdviceResponse)
async def get_strategic_advice(country_id: str, focus: Optional[str] = None):
    """Get AI-generated strategic advice for a country

    Args:
        country_id: Player country code (e.g., FRA)
        focus: Optional focus area (economy, military, diplomacy, etc.)

    Returns:
        List of strategic advices with priorities and reasoning
    """
    world = get_world()
    if not world:
        raise HTTPException(status_code=404, detail="No active game")

    player = world.get_country(country_id)
    if not player:
        raise HTTPException(status_code=404, detail=f"Country {country_id} not found")

    try:
        advices = await ai_advisor.get_strategic_advice(world, player, focus)
        if advices:
            return StrategicAdviceResponse(success=True, advices=advices)
        return StrategicAdviceResponse(
            success=False,
            error="Could not generate advice - AI unavailable"
        )
    except Exception as e:
        logger.error(f"Strategic advice error: {e}")
        return StrategicAdviceResponse(success=False, error=str(e))


@router.get("/dialogue/{country_id}/{target_id}", response_model=DiplomaticDialogueResponse)
async def get_diplomatic_dialogue(
    country_id: str,
    target_id: str,
    action: str = "general",
    accepted: Optional[bool] = None
):
    """Get AI-generated diplomatic dialogue from a country

    Args:
        country_id: Player country code
        target_id: Target country code (the one responding)
        action: Type of diplomatic action (alliance_proposal, sanction, trade_offer, etc.)
        accepted: Whether the action was accepted (None = pending)

    Returns:
        Diplomatic dialogue with speaker info and message
    """
    world = get_world()
    if not world:
        raise HTTPException(status_code=404, detail="No active game")

    player = world.get_country(country_id)
    target = world.get_country(target_id)

    if not player:
        raise HTTPException(status_code=404, detail=f"Country {country_id} not found")
    if not target:
        raise HTTPException(status_code=404, detail=f"Country {target_id} not found")

    try:
        dialogue = await ai_advisor.generate_diplomatic_response(
            world, player, target, action, accepted
        )
        if dialogue:
            return DiplomaticDialogueResponse(success=True, dialogue=dialogue)
        return DiplomaticDialogueResponse(
            success=False,
            error="Could not generate dialogue - AI unavailable"
        )
    except Exception as e:
        logger.error(f"Diplomatic dialogue error: {e}")
        return DiplomaticDialogueResponse(success=False, error=str(e))


@router.get("/briefing/{country_id}", response_model=BriefingResponse)
async def get_annual_briefing(country_id: str):
    """Get AI-generated annual intelligence briefing

    Args:
        country_id: Player country code

    Returns:
        Annual briefing with threats, opportunities, and recommendations
    """
    world = get_world()
    if not world:
        raise HTTPException(status_code=404, detail="No active game")

    player = world.get_country(country_id)
    if not player:
        raise HTTPException(status_code=404, detail=f"Country {country_id} not found")

    try:
        briefing = await ai_advisor.generate_annual_briefing(world, player)
        if briefing:
            return BriefingResponse(success=True, briefing=briefing)
        return BriefingResponse(
            success=False,
            error="Briefing already generated this year or AI unavailable"
        )
    except Exception as e:
        logger.error(f"Briefing error: {e}")
        return BriefingResponse(success=False, error=str(e))


@router.get("/media/{country_id}", response_model=MediaCommentResponse)
async def get_media_comment(country_id: str):
    """Get AI-generated press/media commentary

    Args:
        country_id: Player country code

    Returns:
        Media comment with source, headline, and excerpt
    """
    world = get_world()
    if not world:
        raise HTTPException(status_code=404, detail="No active game")

    player = world.get_country(country_id)
    if not player:
        raise HTTPException(status_code=404, detail=f"Country {country_id} not found")

    try:
        comment = await ai_advisor.generate_media_comment(world, player)
        if comment:
            return MediaCommentResponse(success=True, comment=comment)
        return MediaCommentResponse(
            success=False,
            error="Could not generate media comment - AI unavailable"
        )
    except Exception as e:
        logger.error(f"Media comment error: {e}")
        return MediaCommentResponse(success=False, error=str(e))


@router.get("/opportunity/{country_id}", response_model=OpportunityEventResponse)
async def get_opportunity_event(country_id: str):
    """Get AI-generated positive opportunity event

    Args:
        country_id: Player country code

    Returns:
        Positive event with title, description, and effects
    """
    world = get_world()
    if not world:
        raise HTTPException(status_code=404, detail="No active game")

    player = world.get_country(country_id)
    if not player:
        raise HTTPException(status_code=404, detail=f"Country {country_id} not found")

    try:
        event = await ai_advisor.generate_opportunity_event(world, player)
        if event:
            return OpportunityEventResponse(success=True, event=event)
        return OpportunityEventResponse(
            success=False,
            error="Could not generate opportunity - AI unavailable"
        )
    except Exception as e:
        logger.error(f"Opportunity event error: {e}")
        return OpportunityEventResponse(success=False, error=str(e))


@router.get("/status")
async def get_ai_advisor_status():
    """Check AI advisor availability"""
    try:
        available = await ai_advisor._call_ollama("Test", 10) is not None
        return {
            "available": available,
            "model": ai_advisor.model,
            "url": ai_advisor.base_url
        }
    except Exception:
        return {
            "available": False,
            "model": ai_advisor.model,
            "url": ai_advisor.base_url
        }


@router.post("/chat", response_model=ChatResponse)
async def chat_with_advisor(request: ChatRequest):
    """Have a conversational chat with the AI advisor

    Args:
        request: ChatRequest with country_id, message, optional context and history

    Returns:
        AI response as plain text
    """
    world = get_world()
    if not world:
        raise HTTPException(status_code=404, detail="No active game")

    player = world.get_country(request.country_id)
    if not player:
        raise HTTPException(status_code=404, detail=f"Country {request.country_id} not found")

    try:
        response = await ai_advisor.chat(
            world,
            player,
            request.message,
            request.context,
            request.conversation_history
        )
        if response:
            return ChatResponse(success=True, response=response)
        return ChatResponse(
            success=False,
            error="Could not get response - AI unavailable"
        )
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return ChatResponse(success=False, error=str(e))
