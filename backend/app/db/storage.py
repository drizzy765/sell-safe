"""Private media uploads. Objects are not given a public URL."""

from typing import Protocol


class ObjectStorage(Protocol):
    def upload(self, path: str, data: bytes, content_type: str) -> str: ...


class MemoryStorage:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    def upload(self, path: str, data: bytes, content_type: str) -> str:
        self.objects[path] = data
        return path


class SupabaseStorage:
    def __init__(self, client: object, bucket: str) -> None:
        self._client = client
        self._bucket = bucket

    def upload(self, path: str, data: bytes, content_type: str) -> str:
        if not self._bucket:
            raise RuntimeError("SUPABASE_STORAGE_BUCKET is not set")
        self._client.storage.from_(self._bucket).upload(
            path,
            data,
            file_options={"content-type": content_type},
        )
        return path


def build_storage(settings: object) -> SupabaseStorage:
    url = getattr(settings, "supabase_url", "")
    key = getattr(settings, "supabase_service_role_key", "")
    bucket = getattr(settings, "supabase_storage_bucket", "")
    if not url or not key or not bucket:
        raise RuntimeError("Supabase storage is not configured")
    from supabase import create_client

    return SupabaseStorage(create_client(url, key), bucket)
