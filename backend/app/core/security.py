from app.core.config import get_settings


def validate_upload_size(size_bytes: int) -> bool:
    settings = get_settings()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    return size_bytes <= max_bytes
