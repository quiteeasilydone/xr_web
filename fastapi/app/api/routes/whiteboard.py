from fastapi import APIRouter, HTTPException, UploadFile, File
import asyncio
from datetime import datetime
from schemas.request_body import WhiteboardRequest

router = APIRouter()

# 전역 딕셔너리로 temp_file 선언
temp_file = {}
removal_tasks = {}

# 일정 시간이 지난 후 파일을 메모리에서 제거하는 비동기 함수
async def remove_file_after_timeout(file_id: str, timeout: int):
    await asyncio.sleep(timeout)
    if file_id in temp_file:
        del temp_file[file_id]
        print(f"File {file_id} has been removed from memory after {timeout} seconds")
        del removal_tasks[file_id]

# 화이트보드 파일 제출 API
@router.post("/api/whiteboard", summary="화이트보드 파일 제출", description="화이트보드 파일을 제출하고, 해당 파일은 서버 메모리에 5분 동안 유지됩니다.")
async def submit_whiteboard(wb: WhiteboardRequest):
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
    
    # 새로운 삭제 타이머를 설정 (300초 = 5분)
    removal_task = asyncio.create_task(remove_file_after_timeout(file_id, 300))
    removal_tasks[file_id] = removal_task

    return {"message": "File received and will be kept for 5 minutes"}

# 화이트보드 파일 조회 API
@router.get("/api/get-whiteboard/{android_UUID}", summary="화이트보드 파일 조회", description="안드로이드 UUID를 사용하여 서버에 저장된 화이트보드 파일의 내용을 조회합니다.")
async def get_whiteboard(android_UUID: str):
    
    if android_UUID not in temp_file:
        raise HTTPException(status_code=404, detail="File not found")
    
    result = str(temp_file[android_UUID]['content'])
    return {"result": result}
