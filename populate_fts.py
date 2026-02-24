#!/usr/bin/env python3
"""Populate FTS5 index from existing datamd_files table."""

from sqlalchemy import text
from datadotmd.database.service import get_session
from datadotmd.database.models import DataMdFile
from sqlmodel import select

def populate_fts():
    """Populate FTS5 table from datamd_files."""
    with get_session() as session:
        # Get all files
        files = session.exec(select(DataMdFile)).all()
        
        # Clear existing FTS5 index
        session.exec(text("DELETE FROM datamd_files_fts"))
        
        # Insert all files into FTS5
        for file in files:
            session.exec(
                text("""
                    INSERT INTO datamd_files_fts(rowid, path, content) 
                    VALUES (:id, :path, :content)
                """).bindparams(id=file.id, path=file.path, content=file.current_content)
            )
        
        session.commit()
        print(f"✓ Indexed {len(files)} DATA.md files")

if __name__ == "__main__":
    populate_fts()
