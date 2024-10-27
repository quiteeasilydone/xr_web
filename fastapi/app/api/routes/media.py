from fastapi import APIRouter
from fastapi import HTTPException, Depends, UploadFile, File, Form

from schemas.request_body import MediaFileRequest

import os
import io
from fastapi.responses import JSONResponse
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from schemas.models import ReportForm as ReportFormModel
from schemas.models import TopicForm as TopicFormModel
from schemas.models import MediaFile as MediaFileModel
from db.postgres_connection import connect_db
from db.minio_connection import minio_client
from sqlalchemy import func
from sqlalchemy.future import select
from sqlalchemy import delete
from schemas.models import Infra as InfraModel
from schemas.response_body import MediaFileResponse, MediaFilesResponse
import urllib.parse


router = APIRouter()

def get_bucket_type_by_extension(file_extension: str):
    # 파일 확장자에 따라 적절한 버킷 이름과 파일 타입 반환
    file_extension = file_extension.lower()

    if file_extension in {'.jpeg', '.jpg', '.png', '.gif', '.bmp', '.tiff', '.webp'}:
        bucket_name = os.environ["MINIO_BUCKET_IMG"]
        file_type = 'image'
    elif file_extension in {'.pdf'}:
        bucket_name = os.environ["MINIO_BUCKET_PDF"]
        file_type = 'pdf'
    elif file_extension in {'.mp3', '.wav', '.m4a', '.ogg', '.flac', '.aac'}:
        bucket_name = os.environ["MINIO_BUCKET_AUDIO"]
        file_type = 'audio'
    elif file_extension in {'.mp4', '.mov', '.avi', '.mkv', '.webm'}:
        bucket_name = os.environ["MINIO_BUCKET_VIDEO"]
        file_type = 'video'
    else:
        raise HTTPException(status_code=400, detail="Invalid file extension.")

    return bucket_name, file_type


# 점검 절차에 따른 메뉴얼 등록 
@router.post("/api/manual", summary="메뉴얼 파일 업로드", description="점검 절차에 따른 메뉴얼 파일을 업로드하고, 파일 유형에 따라 MinIO에 저장합니다."
             ,responses={
                200: {
                    "description": "메뉴얼 파일 업로드 성공",
                    "content": {
                        "application/json": {
                            "example":{
                                "message": "Manual file saved successfully"
                            }                          
                        }
                    }
                }
            })
async def submit_manual(
    infra: str = Form(...),
    company_name: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(connect_db)
):
    try:
        if not infra:
            raise HTTPException(status_code=400, detail="Infra field is required")

        infra_id_result = await db.execute(
            select(InfraModel.infra_id).where(InfraModel.infra_name == infra)
        )
       
        infra_id = infra_id_result.scalars().first()

        if not infra_id:
            raise HTTPException(status_code=404, detail="Infra not found")
        

        # 파일 이름 처리
        file_name = file.filename
        file_extension = os.path.splitext(file_name)[1].lower()
        file_name = os.path.splitext(file_name)[0]

        # 파일 유형 및 버킷 결정
        bucket_name, file_type = get_bucket_type_by_extension(file_extension)

        # 파일 이름에 보고서 ID와 주제 ID 추가
        file_name = file_name + "_" + infra + "_" + company_name

        # 새 미디어 파일 등록
        new_media = MediaFileModel(
            infra_id = infra_id,
            infra_name = infra,
            company_name = company_name,
            file_type = file_type,
            file_name = file_name
        )

        db.add(new_media)
        await db.flush()

        try:
            # 파일 읽기 및 MinIO에 저장
            file_data = file.file.read()
            minio_client.put_object(
                bucket_name = bucket_name,
                object_name = file_name,
                data=io.BytesIO(file_data),
                length=len(file_data),
                content_type = file.content_type
            )
        except Exception as e:
            raise HTTPException(status_code = 500, detail=f"Error saving file from MinIO: {str(e)}")
        
        await db.commit()
        return {"message": "Manual file saved successfully"}

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code = 500, detail = f"Error saving data: {str(e)}")


@router.get("/api/manual/", summary="메뉴얼 파일 상세조회(AND)", description="media_id로 메뉴얼을 상세조회합니다.(파일 반환)")
async def get_manual_file(
    media_id: int,
    db: AsyncSession = Depends(connect_db)
):
    try:
        media_file = await db.execute(
            select(MediaFileModel).where(MediaFileModel.media_id == media_id)
        )
        media = media_file.scalars().first()

        if not media:
            raise HTTPException(status_code=404, detail="Media file not found")

        media_type = 'temp'
        if media.file_type == "image":
            bucket_name = os.environ["MINIO_BUCKET_IMG"]
            media_type = "image/jpeg"
        elif media.file_type == "pdf":
            bucket_name = os.environ["MINIO_BUCKET_PDF"]
            media_type = "application/pdf"
        elif media.file_type == "audio":
            bucket_name = os.environ["MINIO_BUCKET_AUDIO"]
            media_type = "audio/wav"
        elif media.file_type == "video":
            bucket_name = os.environ["MINIO_BUCKET_VIDEO"]
            media_type = "video/mp4"
        else:
            raise HTTPException(status_code=400, detail="Invalid file type")

        try:
            file_data = minio_client.get_object(bucket_name, media.file_name)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error retrieving file from MinIO: {str(e)}")

        encoded_filename = urllib.parse.quote(media.file_name)

        return StreamingResponse(
            io.BytesIO(file_data.read()), 
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving media: {str(e)}")
    


@router.get("/api/manuals/", summary="메뉴얼 파일 전체조회(AND)", description="infra, company에 해당하는 모든 메뉴얼을 조회합니다.(파일 반환X)"
            ,response_model = MediaFilesResponse)
async def get_manual_files(
    infra: str,
    company_name: str,
    db: AsyncSession = Depends(connect_db)
):
    try:
        # # 보고서 및 주제 확인
        # existing_report_form = await db.execute(
        #     select(ReportFormModel.report_form_id).where(ReportFormModel.report_form_id == report_form_id)
        # )
        # existing_report_form_id = existing_report_form.scalars().first()

        # if not existing_report_form_id:
        #     raise HTTPException(status_code=404, detail="Report not found")

        # existing_topic_form = await db.execute(
        #     select(TopicFormModel.topic_form_id).where(TopicFormModel.topic_form_id == topic_form_id)
        # )
        # existing_topic_form_id = existing_topic_form.scalars().first()

        # if not existing_topic_form_id:
        #     raise HTTPException(status_code=404, detail="Topic not found")

        # 미디어 파일 확인
        media_files = await db.execute(
            select(MediaFileModel)
            .where(MediaFileModel.infra_name == infra)
            .where(MediaFileModel.company_name == company_name)
        )
        
        medias = media_files.scalars().all()

        return {"media_files": medias}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving media: {str(e)}")

