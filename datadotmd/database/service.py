"""Database service layer for DataDotMD."""

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlmodel import Session, SQLModel, create_engine, select

from datadotmd.app.config import settings
from datadotmd.database.models import DataMdFile, DataMdHistory, Directory

from datadotmd.system.notifications import (
    notify_new_data_md_file,
    notify_changed_data_md_file,
    notify_data_updated,
)

# Create the engine
engine = create_engine(settings.database_url, echo=settings.debug)


def init_db():
    """Initialize the database, creating all tables."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    """Get a database session."""
    return Session(engine)


def compute_hash(content: str) -> str:
    """Compute SHA256 hash of content."""
    return hashlib.sha256(content.encode()).hexdigest()


def get_all_datamd_files(
    session: Session,
    offset: int = 0,
    limit: int = 10,
    order_by_data_modified: bool = True,
) -> list[DataMdFile]:
    """
    Get all DATA.md files, ordered by most recently updated data.

    Parameters
    ----------
    session : Session
        Database session
    offset : int
        Number of records to skip
    limit : int
        Maximum number of records to return
    order_by_data_modified : bool
        If True, order by data_last_modified descending

    Returns
    -------
    list[DataMdFile]
        List of DATA.md files
    """
    statement = select(DataMdFile)
    if order_by_data_modified:
        statement = statement.order_by(DataMdFile.data_last_modified.desc())
    statement = statement.offset(offset).limit(limit)
    return list(session.exec(statement).all())


def count_datamd_files(session: Session) -> int:
    """Count total number of DATA.md files."""
    statement = select(DataMdFile)
    return len(list(session.exec(statement).all()))


def get_datamd_file_by_path(session: Session, path: str) -> Optional[DataMdFile]:
    """Get a DATA.md file by its path."""
    statement = select(DataMdFile).where(DataMdFile.path == path)
    return session.exec(statement).first()


def create_or_update_datamd_file(
    session: Session,
    path: str,
    content: str,
    data_last_modified: datetime,
) -> DataMdFile:
    """
    Create or update a DATA.md file record.

    If the content has changed, adds a history record.

    Parameters
    ----------
    session : Session
        Database session
    path : str
        Path to the DATA.md file
    directory_path : str
        Path to the directory it describes
    content : str
        Content of the DATA.md file
    data_last_modified : datetime
        Last modification time of the underlying data

    Returns
    -------
    DataMdFile
        The created or updated file record
    """
    content_hash = compute_hash(content)
    existing = get_datamd_file_by_path(session, path)

    now = datetime.now(timezone.utc)
    notified_already = False

    if existing:
        # Check if content changed
        if existing.content_hash != content_hash:
            # Add history record with old content
            history = DataMdHistory(
                datamd_file_id=existing.id,
                content=existing.current_content,
                content_hash=existing.content_hash,
                created_at=existing.updated_at,
            )
            session.add(history)

            # Update existing record
            existing.current_content = content
            existing.content_hash = content_hash
            existing.updated_at = now

            notified_already = True
            notify_changed_data_md_file(
                update_time=now,
                new_content=content,
                path=existing.path.replace("/DATA.md", ""),
            )

        # Check if the data has been modified, to some diff.
        if abs(existing.data_last_modified - data_last_modified) > timedelta(minutes=5):
            existing.data_last_modified = data_last_modified
            session.add(existing)

            if not notified_already:
                notify_data_updated(
                    update_time=now,
                    path=existing.path.replace("/DATA.md", ""),
                )

        session.commit()
        session.refresh(existing)
        return existing
    else:
        # Create new record
        new_file = DataMdFile(
            path=path,
            current_content=content,
            content_hash=content_hash,
            created_at=now,
            updated_at=now,
            data_last_modified=data_last_modified,
        )
        session.add(new_file)
        session.commit()
        session.refresh(new_file)

        notify_new_data_md_file(
            update_time=now,
            new_content=content,
            path=new_file.path.replace("/DATA.md", ""),
        )

        return new_file


def get_datamd_history(
    session: Session,
    datamd_file_id: int,
    limit: int = 10,
) -> list[DataMdHistory]:
    """
    Get history records for a DATA.md file.

    Parameters
    ----------
    session : Session
        Database session
    datamd_file_id : int
        ID of the DATA.md file
    limit : int
        Maximum number of history records to return

    Returns
    -------
    list[DataMdHistory]
        List of history records, most recent first
    """
    statement = (
        select(DataMdHistory)
        .where(DataMdHistory.datamd_file_id == datamd_file_id)
        .order_by(DataMdHistory.created_at.desc())
        .limit(limit)
    )
    return list(session.exec(statement).all())


def get_or_create_directory(
    session: Session,
    path: str,
    parent_id: Optional[int] = None,
) -> Directory:
    """
    Get or create a directory record.

    Parameters
    ----------
    session : Session
        Database session
    path : str
        Path to the directory
    parent_id : Optional[int]
        ID of the parent directory

    Returns
    -------
    Directory
        The directory record
    """
    statement = select(Directory).where(Directory.path == path)
    existing = session.exec(statement).first()

    if existing:
        return existing

    now = datetime.now(timezone.utc)
    new_dir = Directory(
        path=path,
        parent_id=parent_id,
        last_scanned=now,
        data_last_modified=now,
    )
    session.add(new_dir)
    session.commit()
    session.refresh(new_dir)
    return new_dir


def update_directory(
    session: Session,
    directory_id: int,
    datamd_file_id: Optional[int] = None,
    data_last_modified: Optional[datetime] = None,
) -> Directory:
    """
    Update a directory record.

    Parameters
    ----------
    session : Session
        Database session
    directory_id : int
        ID of the directory
    datamd_file_id : Optional[int]
        ID of the associated DATA.md file
    data_last_modified : Optional[datetime]
        Last modification time of files in directory

    Returns
    -------
    Directory
        The updated directory record
    """
    statement = select(Directory).where(Directory.id == directory_id)
    directory = session.exec(statement).first()

    if not directory:
        raise ValueError(f"Directory with ID {directory_id} not found")

    if datamd_file_id is not None:
        directory.datamd_file_id = datamd_file_id

    if data_last_modified is not None:
        directory.data_last_modified = data_last_modified

    directory.last_scanned = datetime.now(timezone.utc)
    session.add(directory)
    session.commit()
    session.refresh(directory)
    return directory


def get_directory_by_path(session: Session, path: str) -> Optional[Directory]:
    """Get a directory by its path."""
    statement = select(Directory).where(Directory.path == path)
    return session.exec(statement).first()


def get_root_directory(session: Session) -> Directory:
    """Get the root directory."""
    root = get_directory_by_path(session, "")
    if not root:
        now = datetime.now(timezone.utc)
        root = Directory(
            path="",
            parent_id=None,
            last_scanned=now,
            data_last_modified=now,
        )
        session.add(root)
        session.commit()
        session.refresh(root)
    return root
