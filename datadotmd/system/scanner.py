"""Filesystem scanner for finding and tracking DATA.md files."""

import os
from datetime import datetime
from pathlib import Path
from typing import Generator

from datadotmd.app.config import settings


class FileSystemScanner:
    """Scanner for finding DATA.md files and tracking directory contents."""

    def __init__(self, root_path: Path | None = None):
        """
        Initialize the filesystem scanner.

        Parameters
        ----------
        root_path : Path | None
            Root directory to scan. If None, uses settings.data_root
        """
        self.root_path = root_path or settings.data_root

    def find_all_datamd_files(self) -> Generator[tuple[Path, Path], None, None]:
        """
        Find all DATA.md files in the root path.

        Yields
        ------
        tuple[Path, Path]
            Tuple of (datamd_file_path, directory_it_describes)
        """
        if not self.root_path.exists():
            return

        for root, dirs, files in os.walk(self.root_path):
            root_path = Path(root)

            # Check if DATA.md exists in this directory
            if "DATA.md" in files:
                datamd_path = root_path / "DATA.md"
                # DATA.md describes its parent directory
                yield (datamd_path, root_path)

    def get_directory_last_modified(self, directory: Path) -> datetime:
        """
        Get the most recent modification time of any file in a directory.

        Parameters
        ----------
        directory : Path
            Directory to check

        Returns
        -------
        datetime
            Most recent modification time
        """
        if not directory.exists():
            return datetime.utcnow()

        latest_time = datetime.fromtimestamp(directory.stat().st_mtime)

        try:
            for item in directory.rglob("*"):
                if item.is_file() and item.name != "DATA.md":
                    mtime = datetime.fromtimestamp(item.stat().st_mtime)
                    if mtime > latest_time:
                        latest_time = mtime
        except (PermissionError, OSError):
            # If we can't access some files, just use what we have
            pass

        return latest_time

    def read_datamd_content(self, datamd_path: Path) -> str:
        """
        Read the content of a DATA.md file.

        Parameters
        ----------
        datamd_path : Path
            Path to the DATA.md file

        Returns
        -------
        str
            Content of the file
        """
        try:
            return datamd_path.read_text(encoding="utf-8")
        except Exception:
            return ""

    def get_relative_path(self, absolute_path: Path) -> str:
        """
        Get a path relative to the root.

        Parameters
        ----------
        absolute_path : Path
            Absolute path

        Returns
        -------
        str
            Relative path as string
        """
        try:
            return str(absolute_path.relative_to(self.root_path))
        except ValueError:
            return str(absolute_path)

    def find_all_directories(self) -> Generator[Path, None, None]:
        """
        Find all directories under the root path that don't contain a DATA.md file.

        Yields
        ------
        Path
            Directory path
        """
        if not self.root_path.exists():
            return

        for root, dirs, files in os.walk(self.root_path, topdown=True):
            root_path = Path(root)
            for dir in dirs:
                dir_path = root_path / dir
                if not (dir_path / "DATA.md").exists():
                    print("Found directory without DATA.md:", dir_path)
                    yield dir_path
                else:
                    # If this directory has DATA.md, don't recurse into it
                    print("Directory has DATA.md, skipping children:", dir_path)
                    dirs.remove(dir)

    def get_directory_tree(
        self, directory: Path, parent_has_datamd: bool = False
    ) -> dict:
        """
        Get a tree structure of a directory.

        Parameters
        ----------
        directory : Path
            Directory to analyze
        parent_has_datamd : bool
            Whether any parent directory has a DATA.md file

        Returns
        -------
        dict
            Dictionary with 'name', 'path', 'is_dir', 'has_datamd', 'has_files', 'needs_warning', 'children'
        """
        if not directory.exists():
            return {}

        has_datamd = (directory / "DATA.md").exists()
        # If this directory or any parent has DATA.md, children are "covered"
        is_covered = parent_has_datamd or has_datamd

        tree = {
            "name": directory.name,
            "path": self.get_relative_path(directory),
            "is_dir": True,
            "has_datamd": has_datamd,
            "has_files": False,
            "needs_warning": False,
            "children": [],
        }

        try:
            items = sorted(directory.iterdir(), key=lambda x: (not x.is_dir(), x.name))
            for item in items:
                if item.is_dir():
                    tree["children"].append(self.get_directory_tree(item, is_covered))
                else:
                    # Check if this directory has files (excluding DATA.md)
                    if item.name != "DATA.md":
                        tree["has_files"] = True
        except (PermissionError, OSError):
            pass

        # Show warning only if: has files, no DATA.md, and not covered by parent
        tree["needs_warning"] = (
            tree["has_files"] and not has_datamd and not parent_has_datamd
        )

        return tree

    def get_clean_directory_tree(
        self, directory: Path, parent_has_datamd: bool = False
    ) -> dict:
        """
        Get a clean tree structure of a directory, removing trailing directories at the
        bottom level.
        """

        tree = self.get_directory_tree(directory, parent_has_datamd)

        def node_has_datamd_below(node):
            if node["has_datamd"]:
                return True
            else:
                has_below = any(node_has_datamd_below(x) for x in node["children"])
            return has_below

        def clean_node(node):
            if not node_has_datamd_below(node) and node["has_datamd"]:
                node["children"] = []
            else:
                node["children"] = [clean_node(x) for x in node["children"]]

        return tree
