from pydantic import BaseModel, ConfigDict, Field
from typing import Literal, List, Optional
from datetime import datetime
from uuid import UUID

# We import UserResponse from your auth schemas for the detailed post view
from backend.app.schemas.auth import UserResponse

# ----------------- REQUEST SCHEMAS -----------------

class CreatePostRequest(BaseModel):
    """Schema for creating a new hangout post."""
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    # Updated to match our new categories
    activity_type: Literal['movies', 'dining_nightlife', 'adventure_trips', 'sports', 'casual_hangout', 'dating']
    city: str = Field(..., max_length=100)
    venue_name: Optional[str] = Field(None, max_length=200)
    venue_address: Optional[str] = None
    scheduled_at: datetime
    max_participants: int = Field(..., ge=2, le=50)
    is_public: bool = True
    # New field for dating
    dating_preferences: Optional[str] = None

class UpdatePostRequest(BaseModel):
    """Schema for updating an existing hangout post (all fields optional)."""
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    activity_type: Optional[Literal['movies', 'dining_nightlife', 'adventure_trips', 'sports', 'casual_hangout', 'dating']] = None
    city: Optional[str] = Field(None, max_length=100)
    venue_name: Optional[str] = Field(None, max_length=200)
    venue_address: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    max_participants: Optional[int] = Field(None, ge=2, le=50)
    is_public: Optional[bool] = None
    dating_preferences: Optional[str] = None

class SendRequestRequest(BaseModel):
    """Schema for sending a request to join a hangout."""
    message: Optional[str] = Field(None, max_length=500)

class RespondRequestRequest(BaseModel):
    """Schema for the host to accept or decline a request."""
    action: Literal['accept', 'decline']

class CreateReviewRequest(BaseModel):
    """Schema for reviewing another user after a hangout."""
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=500)


# ----------------- RESPONSE SCHEMAS -----------------

class PostResponse(BaseModel):
    """Basic response schema for a hangout post."""
    id: UUID
    creator_id: UUID
    title: str
    description: Optional[str]
    activity_type: str
    city: str
    venue_name: Optional[str]
    venue_address: Optional[str]
    scheduled_at: datetime
    max_participants: int
    status: str
    is_public: bool
    dating_preferences: Optional[str] = None  # Added here to send back to the user
    created_at: datetime
    
    current_participant_count: Optional[int] = None 

    model_config = ConfigDict(from_attributes=True)

class RequestResponse(BaseModel):
    """Response schema for a hangout join request."""
    id: UUID
    post_id: UUID
    requester_id: UUID
    message: Optional[str]
    status: str
    responded_at: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ParticipantResponse(BaseModel):
    """Response schema for a confirmed hangout participant."""
    id: UUID
    post_id: UUID
    user_id: UUID
    role: str
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ReviewResponse(BaseModel):
    """Response schema for a user review."""
    id: UUID
    hangout_id: UUID
    reviewer_id: UUID
    reviewee_id: UUID
    rating: int
    comment: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PostDetailResponse(PostResponse):
    """Detailed post response that includes the creator and participant list."""
    creator: UserResponse
    participants: List[ParticipantResponse]