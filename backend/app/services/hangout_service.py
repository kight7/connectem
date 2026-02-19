from uuid import UUID
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from backend.app.models.user import User
from backend.app.models.hangout import HangoutPost, HangoutRequest, HangoutParticipant
from backend.app.schemas.hangout import CreatePostRequest

class HangoutService:

    async def create_post(self, db: AsyncSession, user: User, data: CreatePostRequest) -> HangoutPost:
        # Create the post
        new_post = HangoutPost(
            creator_id=user.id,
            **data.model_dump()
        )
        db.add(new_post)
        await db.flush() # Flush to get the new_post.id

        # Automatically add the creator as the first participant (host)
        host_participant = HangoutParticipant(
            post_id=new_post.id,
            user_id=user.id,
            role='host'
        )
        db.add(host_participant)
        
        await db.commit()
        await db.refresh(new_post)
        return new_post

    async def get_feed(self, db: AsyncSession, city: str, filters: dict, page: int = 1, limit: int = 20) -> list[HangoutPost]:
        query = select(HangoutPost).where(
            HangoutPost.city == city,
            HangoutPost.status == 'open',
            HangoutPost.scheduled_at >= datetime.now(timezone.utc)
        )

        if "activity_type" in filters and filters["activity_type"]:
            query = query.where(HangoutPost.activity_type == filters["activity_type"])

        query = query.order_by(HangoutPost.scheduled_at.asc())
        query = query.offset((page - 1) * limit).limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_post_by_id(self, db: AsyncSession, post_id: UUID) -> HangoutPost | None:
        query = select(HangoutPost).options(
            joinedload(HangoutPost.creator),
            joinedload(HangoutPost.participants)
        ).where(HangoutPost.id == post_id)
        
        result = await db.execute(query)
        return result.scalars().first()

    async def send_request(self, db: AsyncSession, user: User, post_id: UUID, message: str | None) -> HangoutRequest:
        post = await self.get_post_by_id(db, post_id)
        if not post or post.status != 'open':
            raise HTTPException(status_code=400, detail="Post is not available")
        
        if post.creator_id == user.id:
            raise HTTPException(status_code=400, detail="Cannot request your own post")

        # Check if already requested
        existing_req = await db.execute(
            select(HangoutRequest).where(HangoutRequest.post_id == post_id, HangoutRequest.requester_id == user.id)
        )
        if existing_req.scalars().first():
            raise HTTPException(status_code=409, detail="Already requested")

        # Check if full
        count_result = await db.execute(select(func.count()).select_from(HangoutParticipant).where(HangoutParticipant.post_id == post_id))
        current_count = count_result.scalar()
        if current_count >= post.max_participants:
            raise HTTPException(status_code=400, detail="Post is full")

        new_request = HangoutRequest(post_id=post_id, requester_id=user.id, message=message, status='pending')
        db.add(new_request)
        await db.commit()
        await db.refresh(new_request)
        return new_request

    async def respond_to_request(self, db: AsyncSession, owner: User, request_id: UUID, action: str) -> HangoutRequest:
        result = await db.execute(select(HangoutRequest).options(joinedload(HangoutRequest.post)).where(HangoutRequest.id == request_id))
        req = result.scalars().first()
        
        if not req:
            raise HTTPException(status_code=404, detail="Request not found")
            
        post = req.post
        if post.creator_id != owner.id:
            raise HTTPException(status_code=403, detail="Not authorized")
            
        if req.status != 'pending':
            raise HTTPException(status_code=400, detail="Request already processed")

        if action == 'accept':
            # Check capacity again before accepting
            count_result = await db.execute(select(func.count()).select_from(HangoutParticipant).where(HangoutParticipant.post_id == post.id))
            current_count = count_result.scalar()
            
            if current_count >= post.max_participants:
                raise HTTPException(status_code=400, detail="Post is full")

            req.status = 'accepted'
            req.responded_at = datetime.now(timezone.utc)
            
            new_participant = HangoutParticipant(post_id=post.id, user_id=req.requester_id, role='participant')
            db.add(new_participant)
            
            # If accepting this person fills the post, close it
            if current_count + 1 >= post.max_participants:
                post.status = 'closed'
                
        elif action == 'decline':
            req.status = 'declined'
            req.responded_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(req)
        return req

    async def get_my_posts(self, db: AsyncSession, user: User) -> list[HangoutPost]:
        query = select(HangoutPost).where(HangoutPost.creator_id == user.id).order_by(HangoutPost.created_at.desc())
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_my_requests(self, db: AsyncSession, user: User) -> list[HangoutRequest]:
        query = select(HangoutRequest).where(HangoutRequest.requester_id == user.id).order_by(HangoutRequest.created_at.desc())
        result = await db.execute(query)
        return list(result.scalars().all())

    async def cancel_post(self, db: AsyncSession, user: User, post_id: UUID) -> HangoutPost:
        post = await self.get_post_by_id(db, post_id)
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        if post.creator_id != user.id:
            raise HTTPException(status_code=403, detail="Not authorized")
            
        post.status = 'cancelled'
        await db.commit()
        await db.refresh(post)
        return post