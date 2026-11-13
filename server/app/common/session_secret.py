import os
import secrets
import tempfile
from pathlib import Path


def load_session_secret(path: Path | None = None) -> str:
    """Persist one private signing key per data volume, across worker restarts.

    Publish a fully written file atomically: a second process must never read
    an empty key between creation and write. Explicit SESSION_SECRET settings
    bypass this default factory entirely.
    """
    if path is None:
        path = Path(__file__).resolve().parents[2] / "data/system/session-secret"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=".session-")
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as output:
                output.write(secrets.token_urlsafe(32))
                output.flush()
                os.fsync(output.fileno())
            try:
                os.link(temporary, path)
            except FileExistsError:
                pass  # Another worker published the volume's key first.
        finally:
            Path(temporary).unlink(missing_ok=True)
    secret = path.read_text(encoding="utf-8").strip()
    if len(secret) < 32:
        raise ValueError("A mentett munkamenet-aláíró kulcs sérült vagy túl rövid.")
    return secret
