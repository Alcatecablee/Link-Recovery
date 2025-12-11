from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from urllib.parse import urlparse, parse_qs, urlencode
import os

def get_async_database_url():
    url = os.getenv("DATABASE_URL", "")
    if not url:
        return ""
    
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    query_params.pop('sslmode', None)
    
    new_query = urlencode(query_params, doseq=True)
    
    scheme = "postgresql+asyncpg"
    if new_query:
        new_url = f"{scheme}://{parsed.netloc}{parsed.path}?{new_query}"
    else:
        new_url = f"{scheme}://{parsed.netloc}{parsed.path}"
    
    return new_url

DATABASE_URL = get_async_database_url()

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with async_session() as session:
        yield session

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
