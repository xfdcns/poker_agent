from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase



class Base(DeclarativeBase):
    pass

ASYNC_DATABASE_URL = "mysql+aiomysql://root:123456@localhost:3306/poker_agent?charset=utf8mb4"





async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)




async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
