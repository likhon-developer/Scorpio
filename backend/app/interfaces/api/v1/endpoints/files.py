"""
File operation endpoints
"""

import os
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Request, UploadFile, File
from pydantic import BaseModel

from app.domain.services.agent_service import AgentService


router = APIRouter()


class FileReadRequest(BaseModel):
    """File read request model"""
    file: str
    start_line: Optional[int] = 0
    end_line: Optional[int] = None


class FileWriteRequest(BaseModel):
    """File write request model"""
    file: str
    content: str
    append: bool = False


class FileSearchRequest(BaseModel):
    """File search request model"""
    file: str
    regex: str


def get_agent_service(request: Request) -> AgentService:
    """Dependency to get agent service from app state"""
    return request.app.agent_service


@router.post("/read")
async def read_file(
    request: FileReadRequest,
    session_id: str = None,
    agent_service: AgentService = Depends(get_agent_service)
) -> dict:
    """Read file content"""

    if not session_id:
        raise HTTPException(
            status_code=400,
            detail={
                "code": 400,
                "msg": "session_id header is required",
                "data": None
            }
        )

    try:
        # For now, we'll simulate file reading
        # In a real implementation, this would call the sandbox service
        if not os.path.exists(request.file):
            raise HTTPException(
                status_code=404,
                detail={
                    "code": 404,
                    "msg": "File not found",
                    "data": None
                }
            )

        with open(request.file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Apply line range filtering
        start_line = max(0, request.start_line or 0)
        end_line = min(len(lines), request.end_line or len(lines))

        selected_lines = lines[start_line:end_line]
        content = ''.join(selected_lines)

        return {
            "code": 0,
            "msg": "success",
            "data": {
                "content": content,
                "line_count": len(selected_lines),
                "file": request.file
            }
        }

    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail={
                "code": 404,
                "msg": "File not found",
                "data": None
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": 500,
                "msg": f"Failed to read file: {str(e)}",
                "data": None
            }
        )


@router.post("/write")
async def write_file(
    request: FileWriteRequest,
    session_id: str = None,
    agent_service: AgentService = Depends(get_agent_service)
) -> dict:
    """Write content to file"""

    if not session_id:
        raise HTTPException(
            status_code=400,
            detail={
                "code": 400,
                "msg": "session_id header is required",
                "data": None
            }
        )

    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(request.file), exist_ok=True)

        # Write file
        mode = 'a' if request.append else 'w'
        with open(request.file, mode, encoding='utf-8') as f:
            f.write(request.content)

        return {
            "code": 0,
            "msg": "success",
            "data": {
                "file": request.file,
                "bytes_written": len(request.content.encode('utf-8'))
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": 500,
                "msg": f"Failed to write file: {str(e)}",
                "data": None
            }
        )


@router.post("/search")
async def search_file(
    request: FileSearchRequest,
    session_id: str = None,
    agent_service: AgentService = Depends(get_agent_service)
) -> dict:
    """Search file content using regex"""

    if not session_id:
        raise HTTPException(
            status_code=400,
            detail={
                "code": 400,
                "msg": "session_id header is required",
                "data": None
            }
        )

    try:
        import re

        if not os.path.exists(request.file):
            raise HTTPException(
                status_code=404,
                detail={
                    "code": 404,
                    "msg": "File not found",
                    "data": None
                }
            )

        with open(request.file, 'r', encoding='utf-8') as f:
            content = f.read()

        lines = content.split('\n')
        matches = []

        for line_num, line in enumerate(lines, 1):
            if re.search(request.regex, line):
                matches.append({
                    "line_number": line_num,
                    "line": line,
                    "match": re.search(request.regex, line).group(0)
                })

        return {
            "code": 0,
            "msg": "success",
            "data": {
                "file": request.file,
                "matches": matches
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": 500,
                "msg": f"Failed to search file: {str(e)}",
                "data": None
            }
        )


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    session_id: str = None,
    agent_service: AgentService = Depends(get_agent_service)
) -> dict:
    """Upload a file"""

    if not session_id:
        raise HTTPException(
            status_code=400,
            detail={
                "code": 400,
                "msg": "session_id header is required",
                "data": None
            }
        )

    try:
        # Read file content
        content = await file.read()

        # For now, save to a temporary location
        # In production, you'd want to handle this more securely
        upload_dir = f"/tmp/scorpio_uploads/{session_id}"
        os.makedirs(upload_dir, exist_ok=True)

        file_path = os.path.join(upload_dir, file.filename)

        with open(file_path, 'wb') as f:
            f.write(content)

        return {
            "code": 0,
            "msg": "success",
            "data": {
                "file": file_path,
                "filename": file.filename,
                "size": len(content)
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": 500,
                "msg": f"Failed to upload file: {str(e)}",
                "data": None
            }
        )
