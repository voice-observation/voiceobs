"""Audio file streaming routes."""

from fastapi import APIRouter, HTTPException, Query, Request, Response, status

from voiceobs.server.dependencies import get_audio_storage
from voiceobs.server.models import ErrorResponse

router = APIRouter(prefix="/api/v1/audio", tags=["Audio"])


def _parse_range_header(range_header: str, file_size: int) -> tuple[int, int, int]:
    """Parse HTTP Range header and return start, end, and status code.

    Args:
        range_header: Range header value (e.g., "bytes=0-1023").
        file_size: Total size of the file in bytes.

    Returns:
        Tuple of (start, end, status_code) where status_code is 206 for partial
        content or 200 for full content.
    """
    status_code = 200
    start = 0
    end = file_size - 1

    if not range_header:
        return start, end, status_code

    # Parse Range header: "bytes=start-end"
    try:
        range_match = range_header.replace("bytes=", "")
        if "-" in range_match:
            start_str, end_str = range_match.split("-", 1)
            start = int(start_str) if start_str else 0
            end = int(end_str) if end_str else file_size - 1
            # Ensure valid range
            if start < 0:
                start = 0
            if end >= file_size:
                end = file_size - 1
            if start > end:
                # Invalid range, will be handled by caller
                status_code = 200
            else:
                status_code = 206
    except (ValueError, AttributeError):
        # Invalid Range header, serve full file
        start = 0
        end = file_size - 1
        status_code = 200

    return start, end, status_code


@router.get(
    "/{audio_id}",
    summary="Stream audio file",
    description="Stream audio file with Range request support for partial content.",
    responses={
        200: {
            "description": "Audio file stream",
            "content": {"audio/wav": {}},
        },
        206: {
            "description": "Partial content (Range request)",
            "content": {"audio/wav": {}},
        },
        404: {"model": ErrorResponse, "description": "Audio file not found"},
    },
)
async def stream_audio(
    audio_id: str,
    request: Request,
    audio_type: str | None = Query(
        None, description="Audio type (e.g., 'asr', 'tts', 'user', 'agent')"
    ),
) -> Response:
    """Stream audio file with Range request support.

    Supports HTTP Range requests for partial content delivery,
    which is useful for audio players that support seeking.

    Args:
        audio_id: Audio file identifier (typically conversation_id).
        request: FastAPI request object for Range header parsing.
        audio_type: Optional audio type identifier (e.g., "asr", "tts", "user", "agent").
            Used to distinguish between multiple audio files per conversation.
            Provided as query parameter: ?audio_type=asr

    Returns:
        StreamingResponse with audio data and appropriate headers.
    """
    storage = get_audio_storage()

    # Build the storage key based on audio_id and type
    if audio_type:
        storage_key = f"{audio_id}-{audio_type}"
    else:
        storage_key = audio_id

    # Check if file exists
    if not await storage.exists(storage_key):
        type_msg = f" (type: {audio_type})" if audio_type else ""
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audio file with ID {audio_id}{type_msg} not found",
        )

    # Get audio data
    audio_data = await storage.get(storage_key)
    if audio_data is None:
        type_msg = f" (type: {audio_type})" if audio_type else ""
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audio file with ID {audio_id}{type_msg} not found",
        )

    file_size = len(audio_data)
    content_type = "audio/wav"

    # Parse Range header if present
    range_header = request.headers.get("Range", "")
    start, end, parsed_status = _parse_range_header(range_header, file_size)

    # Validate range for 416 response (invalid range)
    if parsed_status == 206 and start > end:
        raise HTTPException(
            status_code=status.HTTP_416_RANGE_NOT_SATISFIABLE,
            detail="Invalid range",
        )

    # Check if range is beyond file size
    if start >= file_size:
        raise HTTPException(
            status_code=status.HTTP_416_RANGE_NOT_SATISFIABLE,
            detail="Range not satisfiable",
        )

    # Convert status code to HTTP status
    if parsed_status == 206:
        http_status = status.HTTP_206_PARTIAL_CONTENT
    else:
        http_status = status.HTTP_200_OK

    # Extract the requested range
    content_length = end - start + 1
    audio_chunk = audio_data[start : end + 1]

    # Create response with appropriate headers
    headers = {
        "Content-Type": content_type,
        "Accept-Ranges": "bytes",
        "Content-Length": str(content_length),
    }

    if http_status == status.HTTP_206_PARTIAL_CONTENT:
        headers["Content-Range"] = f"bytes {start}-{end}/{file_size}"

    return Response(
        content=audio_chunk,
        status_code=http_status,
        headers=headers,
        media_type=content_type,
    )
