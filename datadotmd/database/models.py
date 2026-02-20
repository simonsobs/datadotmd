"""Database models for DataDotMD using SQLModel."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlmodel import Field, SQLModel, Relationship


class DataMdFile(SQLModel, table=True):
    """Represents a DATA.md file and its location."""

    __tablename__ = "datamd_files"

    id: Optional[int] = Field(default=None, primary_key=True)
    path: str = Field(index=True, unique=True)  # Relative path to the DATA.md file
    current_content: str  # Current content of the DATA.md file
    content_hash: str  # Hash of the current content
    created_at: datetime 
    updated_at: datetime
    data_last_modified: datetime



class DataMdHistory(SQLModel, table=True):
    """Historical versions of DATA.md files."""

    __tablename__ = "datamd_history"

    id: Optional[int] = Field(default=None, primary_key=True)
    datamd_file_id: int = Field(foreign_key="datamd_files.id", index=True)
    content: str  # Historical content
    content_hash: str  # Hash of the historical content
    created_at: datetime


class Directory(SQLModel, table=True):
    """Represents a directory in the filesystem."""

    __tablename__ = "directories"

    id: Optional[int] = Field(default=None, primary_key=True)
    path: str = Field(index=True, unique=True) 
    parent_id: Optional[int] = Field(default=None, foreign_key="directories.id", index=True)
    
    # Self-referential relationships for parent-child hierarchy
    children: list["Directory"] = Relationship(back_populates="parent")
    parent: Optional["Directory"] = Relationship(
        back_populates="children",
        sa_relationship_kwargs={"remote_side": "[Directory.id]"}
    )
    
    datamd_file_id: Optional[int] = Field(default=None, foreign_key="datamd_files.id")
    datamd_file: Optional["DataMdFile"] = Relationship()
    
    last_scanned: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    data_last_modified: datetime
