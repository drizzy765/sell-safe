"""Drive URL parsing + list/download with mocked API."""

from __future__ import annotations

import httpx
import pytest

from app.onboarding.drive_import import (
    DriveImportError,
    extract_drive_id,
    list_drive_media,
)


def test_extract_folder_id() -> None:
    kind, drive_id = extract_drive_id(
        "https://drive.google.com/drive/folders/abc123XYZ?usp=sharing"
    )
    assert kind == "folder"
    assert drive_id == "abc123XYZ"


def test_extract_file_id() -> None:
    kind, drive_id = extract_drive_id(
        "https://drive.google.com/file/d/file99/view?usp=sharing"
    )
    assert kind == "file"
    assert drive_id == "file99"


@pytest.mark.asyncio
async def test_list_drive_media_parses_files() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "key=test-key" in str(request.url)
        return httpx.Response(
            200,
            json={
                "files": [
                    {
                        "id": "f1",
                        "name": "Honey beans - NGN 6000.jpg",
                        "mimeType": "image/jpeg",
                        "webContentLink": "https://drive.google.com/uc?id=f1",
                    },
                    {
                        "id": "f2",
                        "name": "notes.txt",
                        "mimeType": "text/plain",
                    },
                ]
            },
        )

    files = await list_drive_media(
        "https://drive.google.com/drive/folders/folder1",
        api_key="test-key",
        transport=httpx.MockTransport(handler),
    )
    assert len(files) == 1
    assert files[0].name.startswith("Honey beans")


@pytest.mark.asyncio
async def test_list_requires_api_key() -> None:
    with pytest.raises(DriveImportError, match="GOOGLE_DRIVE_API_KEY"):
        await list_drive_media("https://drive.google.com/drive/folders/x", api_key="")
