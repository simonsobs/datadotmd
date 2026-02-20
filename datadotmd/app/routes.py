"""API routes for DataDotMD."""

import markdown

from fastapi import APIRouter, Request
from sqlmodel import select

from datadotmd.app.config import settings
from datadotmd.app.templating import TemplateDependency, templateify
from datadotmd.database.models import DataMdFile, Directory
from datadotmd.database.service import (
    count_datamd_files,
    get_all_datamd_files,
    get_datamd_history,
    get_directory_by_path,
    get_root_directory,
    get_session,
)
from datadotmd.system.scanner import FileSystemScanner
from datadotmd.system.sync import scan_and_update_database
from starlette.authentication import requires

router = APIRouter()


@router.get("/")
@requires(settings.required_grant)
@templateify(template_name="index.html")
async def index(
    request: Request,
    templates: TemplateDependency,
    page: int = 1,
) -> dict:
    """Homepage showing list of all DATA.md files."""
    if page < 1:
        page = 1

    offset = (page - 1) * settings.items_per_page

    with get_session() as session:
        files = get_all_datamd_files(
            session,
            offset=offset,
            limit=settings.items_per_page,
        )
        total_count = count_datamd_files(session)

        # Format the data for the template
        formatted_files = []
        for datamd_file in files:
            # Get the directory that has this DATA.md file
            statement = select(Directory).where(
                Directory.datamd_file_id == datamd_file.id
            )
            directory = session.exec(statement).first()

            formatted_files.append(
                {
                    "id": datamd_file.id,
                    "path": datamd_file.path,
                    "directory_path": directory.path if directory else "",
                    "updated_at": datamd_file.updated_at,
                    "data_last_modified": datamd_file.data_last_modified,
                }
            )

    total_pages = (total_count + settings.items_per_page - 1) // settings.items_per_page

    return {
        "files": formatted_files,
        "page": page,
        "total_pages": total_pages,
        "total_count": total_count,
        "has_prev": page > 1,
        "has_next": page < total_pages,
    }


@router.get("/browse/{path:path}")
@requires(settings.required_grant)
@templateify(template_name="browse.html")
async def browse(
    request: Request,
    templates: TemplateDependency,
    path: str = "",
) -> dict:
    """Browse a specific directory and view its DATA.md file."""
    with get_session() as session:
        # Get the root directory to build the full tree
        root_dir = get_root_directory(session)
        tree = _build_directory_tree_from_db(session, root_dir)

        # Get the directory record for the current path
        current_dir = get_directory_by_path(session, path)

        datamd_file = None
        datamd_content = None
        datamd_html = None
        history = []

        if current_dir and current_dir.datamd_file_id:
            # Get the DATA.md file record
            statement = select(DataMdFile).where(
                DataMdFile.id == current_dir.datamd_file_id
            )
            datamd_file = session.exec(statement).first()

            if datamd_file:
                datamd_content = datamd_file.current_content
                # Convert markdown to HTML
                datamd_html = markdown.markdown(
                    datamd_content, extensions=["extra", "codehilite"]
                )
                history = get_datamd_history(session, datamd_file.id)

    return {
        "path": path,
        "current_path": path,
        "tree": tree,
        "has_datamd": current_dir and current_dir.datamd_file_id is not None,
        "datamd_content": datamd_content,
        "datamd_html": datamd_html,
        "datamd_record": datamd_file,
        "history": history,
    }


@router.get("/history/{file_id}")
@requires(settings.required_grant)
@templateify(template_name="htmx/history.html")
async def get_history(
    request: Request,
    templates: TemplateDependency,
    file_id: int,
) -> dict:
    """Get history for a specific DATA.md file (HTMX partial)."""
    with get_session() as session:
        history = get_datamd_history(session, file_id, limit=20)

    return {
        "history": history,
    }


@router.post("/scan")
@requires(settings.required_grant)
async def scan_filesystem(request: Request) -> dict:
    """Trigger a filesystem scan to update the database."""
    scanner = FileSystemScanner()
    with get_session() as session:
        scan_and_update_database(session, scanner)

    return {"status": "success", "message": "Filesystem scan completed"}


@router.get("/htmx/file-list")
@requires(settings.required_grant)
@templateify(template_name="htmx/file_list.html")
async def htmx_file_list(
    request: Request,
    templates: TemplateDependency,
    page: int = 1,
) -> dict:
    """Get paginated file list (HTMX partial)."""
    if page < 1:
        page = 1

    offset = (page - 1) * settings.items_per_page

    with get_session() as session:
        files = get_all_datamd_files(
            session,
            offset=offset,
            limit=settings.items_per_page,
        )
        total_count = count_datamd_files(session)

        # Format the data for the template
        formatted_files = []
        for datamd_file in files:
            # Get the directory that has this DATA.md file
            statement = select(Directory).where(
                Directory.datamd_file_id == datamd_file.id
            )
            directory = session.exec(statement).first()

            formatted_files.append(
                {
                    "id": datamd_file.id,
                    "path": datamd_file.path,
                    "directory_path": directory.path if directory else "",
                    "updated_at": datamd_file.updated_at,
                    "data_last_modified": datamd_file.data_last_modified,
                }
            )

    total_pages = (total_count + settings.items_per_page - 1) // settings.items_per_page

    return {
        "files": formatted_files,
        "page": page,
        "total_pages": total_pages,
        "has_prev": page > 1,
        "has_next": page < total_pages,
    }


def _build_directory_tree_from_db(
    session, directory_record, parent_has_datamd=False
) -> dict:
    """
    Build a directory tree dictionary from database records.

    Parameters
    ----------
    session : Session
        Database session
    directory_record : Directory
        The directory database record
    parent_has_datamd : bool
        Whether the parent directory (or any ancestor) has a DATA.md file

    Returns
    -------
    dict
        Directory tree structure
    """
    # Get children directories
    statement = select(Directory).where(Directory.parent_id == directory_record.id)
    children_records = list(session.exec(statement).all())

    has_datamd = directory_record.datamd_file_id is not None

    # Warning should show only for leaf directories (no subdirectories) that:
    # 1. Don't have their own DATA.md file
    # 2. Are not covered by a parent's DATA.md file
    is_leaf = len(children_records) == 0
    needs_warning = is_leaf and not has_datamd and not parent_has_datamd

    tree = {
        "name": directory_record.path.split("/")[-1]
        if directory_record.path
        else "root",
        "path": directory_record.path,
        "is_dir": True,
        "has_datamd": has_datamd,
        "has_files": len(children_records) > 0,
        "needs_warning": needs_warning,
        "children": [],
    }

    # Recursively build children, passing coverage state down the tree
    for child_record in children_records:
        tree["children"].append(
            _build_directory_tree_from_db(
                session, child_record, parent_has_datamd=has_datamd
            )
        )

    return tree
