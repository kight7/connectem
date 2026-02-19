from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.app.config import settings

# 1. Create the engine (the connection to the DB)
engine = create_async_engine(settings.DATABASE_URL, echo=True)

# 2. Create a session factory
# This creates a new "session" (interaction) for every request
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# 3. Create a Base class
# All your future database tables will inherit from this
Base = declarative_base()

# 4. Dependency to get the database session
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session