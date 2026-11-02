"""Google Drive folder listing + download for catalog import.

Uses Drive API v3 with an optional API key (public "anyone with the link" folders).
File convention: ``Honey beans - NGN 6000.jpg``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

import httpx

from app.onboarding.price_parse import is_catalog_image_filename, parse_filename_product

_FOLDER_ID_RE = re.compile(r"/folders/([a-zA-Z0-9_-]+)")
_FILE_ID_RE = re.compile(r"/file/d/([a-zA-Z0-9_-]+)")
_DRIVE_API = "https://www.googleapis.com/drive/v3"


@dataclass(frozen=True)
class DriveFile:
    id: str
    name: str
    mime_type: str
    web_content_link: str = ""
    thumbnail_link: str = ""

    @property
    def is_image(self) -> bool:
        return self.mime_type.startswith("image/") or is_catalog_image_filename(self.name)

    @property
    def is_video(self) -> bool:
        return self.mime_type.startswith("video/")

    def download_url(self, api_key: str = "") -> str:
        if self.web_content_link:
            return self.web_content_link
        base = f"{_DRIVE_API}/files/{self.id}?alt=media"
        if api_key:
            return f"{base}&key={api_key}"
        return f"https://drive.google.com/uc?export=download&id={self.id}"


class DriveImportError(ValueError):
    """Raised when a Drive URL cannot be listed or downloaded."""


def extract_drive_id(url: str) -> tuple[str, str]:
    """Return (kind, id) where kind is ``folder`` or ``file``."""
    text = (url or "").strip()
    folder = _FOLDER_ID_RE.search(text)
    if folder:
        return "folder", folder.group(1)
    file_match = _FILE_ID_RE.search(text)
    if file_match:
        return "file", file_match.group(1)
    parsed = urlparse(text)
    qs = parse_qs(parsed.query)
    if "id" in qs and qs["id"]:
        # Ambiguous open?id= — treat as file unless path says folders.
        if "/folders/" in text:
            return "folder", qs["id"][0]
        return "file", qs["id"][0]
    raise DriveImportError("Could not find a Drive folder or file id in that link.")


async def list_drive_media(
    folder_url: str,
    *,
    api_key: str = "",
    transport: httpx.AsyncBaseTransport | None = None,
) -> list[DriveFile]:
    """List image/video files in a public Drive folder (or a single file URL)."""
    kind, drive_id = extract_drive_id(folder_url)
    if not api_key:
        raise DriveImportError(
            "GOOGLE_DRIVE_API_KEY is not set. Add a Drive API key in .env to import "
            "public folders, or upload the photos directly."
        )

    if kind == "file":
        meta = await _get_file_meta(drive_id, api_key=api_key, transport=transport)
        return [meta] if (meta.is_image or meta.is_video) else []

    files: list[DriveFile] = []
    page_token = ""
    async with httpx.AsyncClient(
        transport=transport, timeout=45.0, follow_redirects=True
    ) as client:
        while True:
            params: dict[str, str] = {
                "q": f"'{drive_id}' in parents and trashed=false",
                "fields": ("nextPageToken,files(id,name,mimeType,webContentLink,thumbnailLink)"),
                "pageSize": "100",
                "key": api_key,
                "supportsAllDrives": "true",
                "includeItemsFromAllDrives": "true",
            }
            if page_token:
                params["pageToken"] = page_token
            response = await client.get(f"{_DRIVE_API}/files", params=params)
            if response.status_code >= 400:
                detail = _drive_error_detail(response)
                raise DriveImportError(detail)
            payload = response.json()
            for row in payload.get("files") or []:
                mime = str(row.get("mimeType") or "")
                name = str(row.get("name") or "")
                if mime.startswith("application/vnd.google-apps.folder"):
                    continue
                item = DriveFile(
                    id=str(row.get("id") or ""),
                    name=name,
                    mime_type=mime,
                    web_content_link=str(row.get("webContentLink") or ""),
                    thumbnail_link=str(row.get("thumbnailLink") or ""),
                )
                if item.id and (item.is_image or item.is_video):
                    files.append(item)
            page_token = str(payload.get("nextPageToken") or "")
            if not page_token:
                break
    return files


async def download_drive_file(
    file: DriveFile,
    *,
    api_key: str = "",
    transport: httpx.AsyncBaseTransport | None = None,
) -> bytes:
    url = file.download_url(api_key)
    async with httpx.AsyncClient(
        transport=transport, timeout=60.0, follow_redirects=True
    ) as client:
        headers = {}
        response = await client.get(url, headers=headers)
        if response.status_code >= 400:
            # Retry via alt=media with key.
            media_url = f"{_DRIVE_API}/files/{file.id}?alt=media&key={api_key}"
            response = await client.get(media_url)
        if response.status_code >= 400:
            raise DriveImportError(f"Could not download {file.name}: HTTP {response.status_code}")
        return response.content


def product_from_filename(filename: str) -> dict | None:
    name, price = parse_filename_product(filename)
    if not name or price is None:
        return None
    return {"name": name, "price_ngn": price}


async def _get_file_meta(
    file_id: str,
    *,
    api_key: str,
    transport: httpx.AsyncBaseTransport | None = None,
) -> DriveFile:
    async with httpx.AsyncClient(
        transport=transport, timeout=30.0, follow_redirects=True
    ) as client:
        response = await client.get(
            f"{_DRIVE_API}/files/{file_id}",
            params={
                "fields": "id,name,mimeType,webContentLink,thumbnailLink",
                "key": api_key,
                "supportsAllDrives": "true",
            },
        )
    if response.status_code >= 400:
        raise DriveImportError(_drive_error_detail(response))
    row = response.json()
    return DriveFile(
        id=str(row.get("id") or file_id),
        name=str(row.get("name") or ""),
        mime_type=str(row.get("mimeType") or ""),
        web_content_link=str(row.get("webContentLink") or ""),
        thumbnail_link=str(row.get("thumbnailLink") or ""),
    )


def _drive_error_detail(response: httpx.Response) -> str:
    try:
        err = response.json().get("error") or {}
        message = str(err.get("message") or response.text)[:240]
    except Exception:
        message = response.text[:240]
    if response.status_code in (403, 401):
        return (
            "Drive refused access. Make the folder public "
            f"('Anyone with the link') and check GOOGLE_DRIVE_API_KEY. {message}"
        )
    if response.status_code == 404:
        return f"Drive folder/file not found. {message}"
    return f"Drive API error ({response.status_code}): {message}"
