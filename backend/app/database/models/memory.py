from typing import Optional
from sqlmodel import Field, SQLModel, Column
from sqlalchemy import Index
from pgvector.sqlalchemy import Vector


class Memory(SQLModel, table=True):
	id: Optional[int] = Field(default=None, primary_key=True)
	npc_id: int = Field(foreign_key="npc.id", index=True)
	content: str

	# Vetor de embedding semântico (pgvector)
	embedding = Field(sa_column=Column(Vector(128)))


# Índice para buscas vetoriais eficientes (cosine)
Index("ix_memory_embedding", Memory.__table__.c.embedding, postgresql_using="ivfflat")
