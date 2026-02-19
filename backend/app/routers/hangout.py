from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from typing import Optional

from backend.app.database import get_db
from backend.app.dependencies import get_current_user
from backend.app.models.user import User
from backend.app.models.hangout import HangoutPost, HangoutRequest
from backend.app.schemas.hangout import (
    CreatePostRequest, UpdatePostRequest, SendRequestRequest,
    RespondRequestRequest, PostResponse, PostDetailResponse,
    RequestResponse
)
from backend.app.services.hangout_service import HangoutService

hangout_router = APIRouter(prefix="/hangout", tags=["HangOut"])
hangout_service = HangoutService()

@hangout_router.get("/posts", response_model=dict)
async def get_feed(
    city: str,
    activity_type: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    filters = {"activity_type": activity_type} if activity_type else {}
    posts = await hangout_service.get_feed(db, city, filters, page, limit)
    # Convert ORM models to Pydantic schemas for the response
    post_responses = [PostResponse.model_validate(p) for p in posts]
    return {"success": True, "data": post_responses, "message": "Feed retrieved successfully"}

@hangout_router.post("/posts", response_model=dict, status_code=201)
async def create_post(
    data: CreatePostRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    post = await hangout_service.create_post(db, current_user, data)
    return {"success": True, "data": PostResponse.model_validate(post), "message": "Post created successfully"}

@hangout_router.get("/posts/{post_id}", response_model=dict)
async def get_post_detail(
    post_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    post = await hangout_service.get_post_by_id(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return {"success": True, "data": PostDetailResponse.model_validate(post), "message": "Post retrieved"}

@hangout_router.patch("/posts/{post_id}", response_model=dict)
async def update_post(
    post_id: UUID,
    data: UpdatePostRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    post = await hangout_service.get_post_by_id(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this post")
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(post, key, value)
        
    await db.commit()
    await db.refresh(post)
    return {"success": True, "data": PostResponse.model_validate(post), "message": "Post updated"}

@hangout_router.delete("/posts/{post_id}", response_model=dict)
async def cancel_post(
    post_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    await hangout_service.cancel_post(db, current_user, post_id)
    return {"success": True, "data": None, "message": "Post cancelled successfully"}

@hangout_router.post("/posts/{post_id}/request", response_model=dict, status_code=201)
async def send_request(
    post_id: UUID,
    data: SendRequestRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    req = await hangout_service.send_request(db, current_user, post_id, data.message)
    return {"success": True, "data": RequestResponse.model_validate(req), "message": "Request sent"}

@hangout_router.get("/posts/{post_id}/requests", response_model=dict)
async def get_post_requests(
    post_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    post = await hangout_service.get_post_by_id(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    result = await db.execute(select(HangoutRequest).where(HangoutRequest.post_id == post_id))
    requests = result.scalars().all()
    req_responses = [RequestResponse.model_validate(r) for r in requests]
    return {"success": True, "data": req_responses, "message": "Requests retrieved"}

@hangout_router.patch("/requests/{request_id}", response_model=dict)
async def respond_to_request(
    request_id: UUID,
    data: RespondRequestRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    req = await hangout_service.respond_to_request(db, current_user, request_id, data.action)
    return {"success": True, "data": RequestResponse.model_validate(req), "message": f"Request {data.action}ed"}

@hangout_router.delete("/requests/{request_id}", response_model=dict)
async def cancel_request(
    request_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(HangoutRequest).where(HangoutRequest.id == request_id))
    req = result.scalars().first()
    if not req or req.requester_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized or not found")
        
    req.status = 'cancelled'
    await db.commit()
    return {"success": True, "data": None, "message": "Request cancelled"}

@hangout_router.get("/my-posts", response_model=dict)
async def get_my_posts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    posts = await hangout_service.get_my_posts(db, current_user)
    post_responses = [PostResponse.model_validate(p) for p in posts]
    return {"success": True, "data": post_responses, "message": "My posts retrieved"}

@hangout_router.get("/my-requests", response_model=dict)
async def get_my_requests(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    requests = await hangout_service.get_my_requests(db, current_user)
    req_responses = [RequestResponse.model_validate(r) for r in requests]
    return {"success": True, "data": req_responses, "message": "My requests retrieved"}