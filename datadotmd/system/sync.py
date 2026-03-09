"""Functions for scanning and updating the database."""

from sqlmodel import Session

from structlog import get_logger

from datadotmd.database.models import Directory
from datadotmd.database.service import (
    create_or_update_datamd_file,
    get_or_create_directory,
    get_root_directory,
    update_directory,
)
from datadotmd.system.scanner import FileSystemScanner
from datadotmd.app.config import settings

logger = get_logger()

def scan_and_update_database(
    session: Session, scanner: FileSystemScanner | None = None
):
    """
    Scan the filesystem and update the database with current state.

    Parameters
    ----------
    session : Session
        Database session
    scanner : FileSystemScanner | None
        Scanner to use. If None, creates a new one.
    """
    if scanner is None:
        scanner = FileSystemScanner()

    # Get or create root directory
    root = get_root_directory(session)

    # Recursively scan and update all directories
    _scan_directory_recursive(session, scanner, root)


def _scan_directory_recursive(
    session: Session,
    scanner: FileSystemScanner,
    parent_dir_record: Directory,
) -> None:
    """
    Recursively scan a directory and its children.

    Parameters
    ----------
    session : Session
        Database session
    scanner : FileSystemScanner
        Filesystem scanner
    parent_dir_record : Directory
        The parent directory database record
    """
    # Build the full path from the relative path
    if parent_dir_record.path:
        full_path = scanner.root_path / parent_dir_record.path
    else:
        full_path = scanner.root_path

    if not full_path.exists() or not full_path.is_dir() or full_path in settings.skip_directories_for_notify:
        return

    # Check if this directory has a DATA.md file
    datamd_path = full_path / "DATA.md"
    datamd_file_record = None

    if datamd_path.exists():
        content = scanner.read_datamd_content(datamd_path)
        data_last_modified = scanner.get_directory_last_modified(full_path)
        relative_datamd_path = scanner.get_relative_path(datamd_path)

        # Create or update the DATA.md file record
        datamd_file_record = create_or_update_datamd_file(
            session=session,
            path=relative_datamd_path,
            content=content,
            data_last_modified=data_last_modified,
        )

        # Link the directory to the DATA.md file
        if parent_dir_record.datamd_file_id != datamd_file_record.id:
            update_directory(
                session=session,
                directory_id=parent_dir_record.id,
                datamd_file_id=datamd_file_record.id,
            )

    # Update the data_last_modified timestamp for this directory
    data_last_modified = scanner.get_directory_last_modified(full_path)
    if parent_dir_record.data_last_modified != data_last_modified:
        update_directory(
            session=session,
            directory_id=parent_dir_record.id,
            data_last_modified=data_last_modified,
        )

    # Process subdirectories
    try:
        for item in full_path.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                relative_item_path = scanner.get_relative_path(item)

                # Get or create child directory record
                child_dir_record = get_or_create_directory(
                    session=session,
                    path=relative_item_path,
                    parent_id=parent_dir_record.id,
                )

                # Recursively scan the child directory
                _scan_directory_recursive(session, scanner, child_dir_record)
    except (PermissionError, OSError) as e:
        # If we can't access the directory, just skip it
        logger.info(
            "Skipping directory due to access error",
            directory=str(full_path),
            error=str(e),
        )
        pass
