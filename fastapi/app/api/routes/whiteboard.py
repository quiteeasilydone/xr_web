from fastapi import APIRouter, Request, HTTPException, UploadFile, File
import asyncio
from datetime import datetime, timedelta
from schemas.request_body import WhiteboardRequest

router = APIRouter()

# 전역 딕셔너리로 temp_file 선언
temp_file = {}
removal_tasks = {}

async def remove_file_after_timeout(file_id: str, timeout: int):
    await asyncio.sleep(timeout)
    if file_id in temp_file:
        del temp_file[file_id]
        print(f"File {file_id} has been removed from memory after {timeout} seconds")
        del removal_tasks[file_id]

@router.post("/api/whiteboard")
async def submit_whiteboard(wb:WhiteboardRequest):
    file_id = wb.filename
    file_content = wb.file_content

    # 파일을 temp_file에 저장
    temp_file[file_id] = {
        "content": file_content,
        "timestamp": datetime.now()
    }
    print({"item": file_id})
    
    # 기존의 삭제 타이머가 있으면 취소
    if file_id in removal_tasks:
        removal_tasks[file_id].cancel()
    
    # 새로운 삭제 타이머를 설정
    removal_task = asyncio.create_task(remove_file_after_timeout(file_id, 300))
    removal_tasks[file_id] = removal_task

    return {"message": "File received and will be kept for 5 minutes"}

@router.get("/api/get-whiteboard/{android_UUID}")
async def get_whiteboard(android_UUID : str):
    # print(temp_file)
    result = str(temp_file[android_UUID]['content'])
    return {"result" : result}

# @router.get("/api/check-temp")
# async def check():
#     print(temp_file)