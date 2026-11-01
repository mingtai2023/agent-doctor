"""Explicit path validation for cooperative agent file tools."""
from pathlib import Path, PureWindowsPath


class PathBoundaryError(ValueError):
    """A path violates the approved workspace boundary."""


class WorkspaceJail:
    """Resolve paths inside an existing workspace; never changes the process cwd."""

    def __init__(self, workspace: str | Path):
        supplied = Path(workspace).expanduser()
        if supplied.is_symlink():
            raise PathBoundaryError("Workspace must not be a symbolic link")
        self.workspace = supplied.resolve(strict=True)
        if not self.workspace.is_dir():
            raise PathBoundaryError("Workspace must be a directory")
        if self.workspace == Path(self.workspace.anchor):
            raise PathBoundaryError("Filesystem roots cannot be workspaces")
        self._reject_home(self.workspace)

    @staticmethod
    def _reject_home(path: str | Path) -> None:
        parts = str(path).replace("\\", "/").casefold().split("/")
        if "home" in parts:
            raise PathBoundaryError("Paths containing a /home/ component are forbidden")

    def resolve(self, path: str | Path) -> Path:
        """Validate before each operation; relative paths use the workspace."""
        self._reject_home(path)
        candidate = Path(path)
        # Reject foreign drive, UNC and alternate-data-stream syntax too.
        if ":" in str(path) and not candidate.is_absolute():
            raise PathBoundaryError("Drive-relative or stream paths are forbidden")
        if PureWindowsPath(str(path)).drive and not candidate.is_absolute():
            raise PathBoundaryError("Foreign drive or UNC path")
        if not candidate.is_absolute():
            candidate = self.workspace / candidate
        resolved = candidate.resolve()
        self._reject_home(resolved)
        if not resolved.is_relative_to(self.workspace):
            raise PathBoundaryError("Path escapes the approved workspace")
        if ":" in str(resolved)[len(resolved.anchor):]:
            raise PathBoundaryError("Alternate data streams are forbidden")
        return resolved
