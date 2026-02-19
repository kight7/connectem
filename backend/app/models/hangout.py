import uuid
from sqlalchemy import String, Text, DateTime, ForeignKey, Integer, Boolean, Enum, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.database import Base

# We define these models to match the 4 tables in your prompt

class HangoutPost(Base):
    __tablename__ = "hangout_posts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    creator_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Enums constrain the database to specific allowed values
    activity_type: Mapped[str] = mapped_column(
        Enum('Dining_NightLife', 'Entertainment', 'Sports', 'Arcade_Adventure', 'Casual_WentOut', 'Event', 'Dating', name='activity_type_enum'), 
        nullable=False
    )
    dating_preferences: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    venue_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    venue_address: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    scheduled_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    max_participants: Mapped[int] = mapped_column(Integer, nullable=False)
    
    status: Mapped[str] = mapped_column(
        Enum('open', 'closed', 'cancelled', 'completed', name='post_status_enum'), 
        default='open'
    )
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    creator = relationship("User", back_populates="hangout_posts")
    requests = relationship("HangoutRequest", back_populates="post", cascade="all, delete-orphan")
    participants = relationship("HangoutParticipant", back_populates="post", cascade="all, delete-orphan")


class HangoutRequest(Base):
    __tablename__ = "hangout_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("hangout_posts.id"), nullable=False, index=True)
    requester_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        Enum('pending', 'accepted', 'declined', 'cancelled', name='request_status_enum'), 
        default='pending'
    )
    responded_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    post = relationship("HangoutPost", back_populates="requests")
    requester = relationship("User")


class HangoutParticipant(Base):
    __tablename__ = "hangout_participants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("hangout_posts.id"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    
    role: Mapped[str] = mapped_column(Enum('host', 'participant', name='participant_role_enum'), nullable=False)
    joined_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    post = relationship("HangoutPost", back_populates="participants")
    user = relationship("User")


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hangout_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("hangout_posts.id"), nullable=False, index=True)
    reviewer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    reviewee_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    hangout = relationship("HangoutPost")
    reviewer = relationship("User", foreign_keys=[reviewer_id])
    reviewee = relationship("User", foreign_keys=[reviewee_id])