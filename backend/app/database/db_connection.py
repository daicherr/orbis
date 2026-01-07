from sqlmodel import create_engine, SQLModel
from app.config import settings

engine = create_engine(settings.DATABASE_URL, echo=True, future=True)

def init_db():
    SQLModel.metadata.create_all(engine)
