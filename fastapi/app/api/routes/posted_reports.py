from fastapi import APIRouter
from fastapi import FastAPI, Request, HTTPException, Depends, File, UploadFile

# from db import minio_connection
from db import postgres_connection
from schemas import response_body
from schemas import request_body

from fastapi.responses import FileResponse, JSONResponse
import mimetypes

import pytz
import os
import json
import io

# 추가
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from schemas.models import User as UserModel
from schemas.models import Infra as InfraModel
from schemas.models import ReportForm as ReportFormModel
from schemas.models import TopicForm as TopicFormModel
from schemas.models import InstructionForm as InstructionFormModel
from schemas.models import PostedReport as PostedReportModel
from db.postgres_connection import connect_db
from sqlalchemy import func
from sqlalchemy.future import select
from sqlalchemy import delete
from db.minio_connection import minio_client
from datetime import datetime
from fastapi.responses import StreamingResponse
from sqlalchemy import Integer

router = APIRouter()


# 설비에 해당하는 보고서 제출 목록 가져오기 (날짜 기준 오름차순)
@router.get("/api/posted-reports")
async def get_posted_reports(
    infra: str = None, company_name: str = None, db: AsyncSession = Depends(connect_db)
):
    if not infra:
        raise HTTPException(
            status_code=400, detail="Infra name is missing in query parameters"
        )
    if not company_name:
        raise HTTPException(
            status_code=400, detail="Company name is missing in query parameters"
        )

    try:
        infra_result = await db.execute(
            select(InfraModel.infra_id).where(
                InfraModel.infra_name == infra, InfraModel.company_name == company_name
            )
        )
        infra_id = infra_result.scalars().first()

        if not infra_id:
            raise HTTPException(
                status_code=404,
                detail=f'Infra "{infra}" not found for company "{company_name}"',
            )

        # 보고서 제출 목록 조회
        reports_result = await db.execute(
            select(PostedReportModel)
            .join(
                ReportFormModel,
                PostedReportModel.report_form_id == ReportFormModel.report_form_id,
            )
            .where(ReportFormModel.infra_id == infra_id)
            .order_by(PostedReportModel.start_time.asc())
        )

        reports = reports_result.scalars().all()

        # 보고서 목록을 JSON 응답으로 반환
        reports_list = [
            {
                "posted_report_id": report.posted_report_id,
                "posted_report_path": report.posted_report_path,
                "user_name": report.user_name,
                "start_time": report.start_time,
                "end_time": report.end_time,
                "company_name": report.company_name,
            }
            for report in reports
        ]

        return JSONResponse(content={"posted_reports": reports_list}, status_code=200)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


# 설비의 특정 날짜 보고서 가져오기
@router.get("/api/posted-report-by-date")
async def get_posted_report_by_date(
    infra: str = None,
    company_name: str = None,
    Unixtime: int = None,
    db: AsyncSession = Depends(connect_db),
):
    if not infra:
        raise HTTPException(
            status_code=400, detail="Infra name is missing in query parameters"
        )
    if not company_name:
        raise HTTPException(
            status_code=400, detail="Company name is missing in query parameters"
        )
    if not Unixtime:
        raise HTTPException(
            status_code=400, detail="Unixtime is missing in query parameters"
        )

    # # Unix timestamp를 datetime 객체로 변환
    # try:
    #     report_date = datetime.fromtimestamp(Unixtime, tz=pytz.utc)
    # except Exception as e:
    #     raise HTTPException(status_code=400, detail=f"Invalid Unixtime: {str(e)}")

    try:
        # infra_id 가져오기
        infra_id_result = await db.execute(
            select(InfraModel.infra_id).where(
                InfraModel.infra_name == infra, InfraModel.company_name == company_name
            )
        )
        infra_id = infra_id_result.scalars().first()

        if not infra_id:
            raise HTTPException(
                status_code=404,
                detail=f'Infra "{infra}" not found for company "{company_name}"',
            )

        # 특정 날짜에 해당하는 보고서 조회
        reports_result = await db.execute(
            select(PostedReportModel)
            .join(
                ReportFormModel,
                PostedReportModel.report_form_id == ReportFormModel.report_form_id,
            )
            .where(
                ReportFormModel.infra_id == infra_id,
                PostedReportModel.start_time <= Unixtime,
                PostedReportModel.end_time >= Unixtime,
            )
        )

        reports = reports_result.scalars().all()

        # 보고서 목록을 JSON 응답으로 반환
        reports_list = [
            {
                "posted_report_id": report.posted_report_id,
                "posted_report_path": report.posted_report_path,
                "user_name": report.user_name,
                "start_time": report.start_time,
                "end_time": report.end_time,
                "company_name": report.company_name,
            }
            for report in reports
        ]

        return JSONResponse(content={"posted_reports": reports_list}, status_code=200)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


# # minio에 저장된 특정 보고서 하나 가져오기
# @router.get("/api/posted-report/deprecated")
# async def get_posted_report_from_minio(request: Request, posted_report_id: int = None):

#     # posted_report_id 파라미터 확인
#     if not posted_report_id:
#         raise HTTPException(status_code=400, detail="posted_report_id is missing in query parameters")

#     try:
#         bucket_name = os.environ['MINIO_BUCKET']
#         file_name = f"{posted_report_id}.json"
#         file_path = f"/{bucket_name}/{file_name}"
#         response = minio_connection.minio_client.get_object(bucket_name, file_name)

#          # 파일 데이터를 읽어서 반환
#         data = response.read()
#         response.close()
#         response.release_conn()

#         # 바이트 데이터를 문자열로 디코딩 (JSON 형식 가정)
#         data_str = data.decode('utf-8')

#         # JSON 문자열을 파이썬 딕셔너리로 변환
#         report_data = json.loads(data_str)

#         return JSONResponse(content={"message": "Report fetched successfully", "report": report_data}, status_code=200)

#     except Exception as e:
#         return JSONResponse(content={"error": str(e)}, status_code=500)


# minio에 저장된 특정 보고서 하나 가져오기
@router.get("/api/posted-report/deprecated")
async def get_posted_report_from_minio(posted_report_id: int = None):
    # posted_report_id 파라미터 확인
    if not posted_report_id:
        raise HTTPException(
            status_code=400, detail="posted_report_id is missing in query parameters"
        )

    try:
        # test code
        objects = minio_client.list_objects("ymtest")
        for obj in objects:
            print(obj.object_name)

        bucket_name = os.environ["MINIO_BUCKET"]
        # bucket_name = "ymtest"
        file_name = f"{posted_report_id}.json"  # 확장자는 저장된 실제 파일에 따라 다를 수 있습니다
        response = minio_client.get_object(bucket_name, file_name)
        # 파일 데이터를 읽기
        file_data = response.read()
        response.close()
        response.release_conn()

        # 파일 형식 감지 (MIME 타입 결정)
        file_type, _ = mimetypes.guess_type(file_name)

        file_stream = io.BytesIO(file_data)
        # 파일 형식에 따라 적절한 응답 반환
        # if file_type:
        #     # 파일 응답 반환
        #     return FileResponse(file_data, media_type=file_type, filename=file_name)
        # else:
        #     # MIME 타입을 감지할 수 없는 경우 기본적으로 바이너리 응답 처리
        #     return FileResponse(
        #         file_data, media_type="application/octet-stream", filename=file_name
        #     )
        return StreamingResponse(
            file_stream,
            media_type=file_type if file_type else "application/octet-stream",
        )

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


# infra, company_name에 따른 작성된 보고서를 Minio에서 가져오기
# @router.get("/api/posted-report")
# async def get_posted_report_from_minio_with_infra_company_name(
#     infra: str = None, company_name: str = None
# ):
#     if not infra:
#         raise HTTPException(
#             status_code=400, detail="Infra name is missing in query parameters"
#         )
#     if not company_name:
#         raise HTTPException(
#             status_code=400, detail="Company name is missing in query parameters"
#         )

#     try:
#         # 데이터베이스 연결
#         conn = await postgres_connection.connect_db()

#         # 인프라와 회사 이름으로 report path의 마지막 숫자 가져오기
#         last_number = await conn.fetchval(
#             """
#             SELECT CAST(substring(posted_report_path FROM '/([0-9]+)$') AS INTEGER) AS last_number
#             FROM posted_reports
#             WHERE report_form_id IN (
#                 SELECT report_form_id FROM report_forms
#                 WHERE infra_id = (
#                     SELECT infra_id FROM infras WHERE infra_name = $1 AND company_name = $2
#                 )
#             )
#             ORDER BY last_number DESC
#             LIMIT 1;
#         """,
#             infra,
#             company_name,
#         )

#         if last_number is None:
#             raise HTTPException(
#                 status_code=404,
#                 detail=f'No report found for infra "{infra}" and company "{company_name}"',
#             )

#         # 데이터베이스 연결 종료
#         await conn.close()

#         # Minio에서 파일 가져오기
#         file_name = f"{last_number}.json"
#         response = minio_client.get_object(os.environ["MINIO_BUCKET"], file_name)

#         # 파일 데이터를 읽어서 반환
#         data = response.read()
#         response.close()
#         response.release_conn()

#         # 바이트 데이터를 문자열로 디코딩 (JSON 형식 가정)
#         data_str = data.decode("utf-8")

#         # JSON 문자열을 파이썬 딕셔너리로 변환
#         report_data = json.loads(data_str)

#         return JSONResponse(
#             content={"message": "Report fetched successfully", "report": report_data},
#             status_code=200,
#         )

#     except Exception as e:
#         return JSONResponse(content={"error": str(e)}, status_code=500)


# infra, company_name에 따른 작성된 보고서를 Minio에서 가져오기
@router.get("/api/posted-report")
async def get_posted_report_from_minio_with_infra_company_name(
    infra: str = None, company_name: str = None, db: AsyncSession = Depends(connect_db)
):
    if not infra:
        raise HTTPException(
            status_code=400, detail="Infra name is missing in query parameters"
        )
    if not company_name:
        raise HTTPException(
            status_code=400, detail="Company name is missing in query parameters"
        )

    try:
        # infra_id 가져오기
        infra_id_result = await db.execute(
            select(InfraModel.infra_id).where(
                InfraModel.infra_name == infra, InfraModel.company_name == company_name
            )
        )
        infra_id = infra_id_result.scalars().first()

        if not infra_id:
            raise HTTPException(
                status_code=404,
                detail=f'Infra "{infra}" not found for company "{company_name}"',
            )

        # report_form_id 중 마지막 숫자 가져오기
        last_number_result = await db.execute(
            select(PostedReportModel.posted_report_id)
            .join(
                ReportFormModel,
                ReportFormModel.report_form_id == PostedReportModel.report_form_id,
            )
            .where(ReportFormModel.infra_id == infra_id)
            .order_by(
                PostedReportModel.posted_report_id.desc()
            )  
            .limit(1)  
        )

        last_number = last_number_result.scalar()


        if not last_number:
            raise HTTPException(
                status_code=404,
                detail=f'No report found for infra "{infra}" and company "{company_name}"',
            )

        # Minio에서 파일 가져오기
        file_name = f"{last_number}.json"
        response = minio_client.get_object("ymtest", file_name)

        # 파일 데이터를 읽어서 반환
        data = response.read()
        response.close()
        response.release_conn()

        # 바이트 데이터를 문자열로 디코딩 (JSON 형식 가정)
        data_str = data.decode("utf-8")

        # JSON 문자열을 파이썬 딕셔너리로 변환
        report_data = json.loads(data_str)

        return JSONResponse(
            content={"message": "Report fetched successfully", "report": report_data},
            status_code=200,
        )

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


# minio에 저장된 특정 보고서 하나 가져오기
@router.get("/api/posted-reports-detail")
async def get_posted_reports_detail(
    infra: str, company_name: str, posted_report_id: int
):
    if not infra:
        raise HTTPException(
            status_code=400, detail="Infra name is missing in query parameters"
        )
    if not company_name:
        raise HTTPException(
            status_code=400, detail="company_name is missing in query parameters"
        )
    # posted_report_id 파라미터 확인
    if not posted_report_id:
        raise HTTPException(
            status_code=400, detail="posted_report_id is missing in query parameters"
        )
    try:
        file_name = f"{posted_report_id}.json"
        bucket_name = os.environ["MINIO_BUCKET"]
        # bucket_name = "ymtest"
        response = minio_client.get_object(bucket_name, file_name)

        # 파일 데이터를 읽어서 반환
        data = response.read()
        response.close()
        response.release_conn()

        # 바이트 데이터를 문자열로 디코딩 (JSON 형식 가정)
        data_str = data.decode("utf-8")
        # JSON 문자열을 파이썬 딕셔너리로 변환
        report_data = json.loads(data_str)

        return JSONResponse(
            content={"message": "Report fetched successfully", "report": report_data},
            status_code=200,
        )
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


# 보고서 등록하기
@router.post("/api/posted-report")
async def submit_inspected_report(
    data: request_body.InspectedReport, db: AsyncSession = Depends(connect_db)
):
    try:
        # Extract data from JSON
        start_time = datetime.fromisoformat(data.start_time)
        end_time = datetime.fromisoformat(data.end_time)
        infra_name = data.infra
        company_name = data.company_name
        inspection_list = data.inspection_list
        user_name = data.user_name

        # infra_id 가져오기
        infra_id_result = await db.execute(
            select(InfraModel.infra_id).where(
                InfraModel.infra_name == infra_name,
                InfraModel.company_name == company_name,
            )
        )
        infra_id = infra_id_result.scalars().first()

        if not infra_id:
            raise HTTPException(
                status_code=404,
                detail=f'Infra "{infra_name}" not found for company "{company_name}"',
            )

        # report_form_id 가져오기
        report_form_id_result = await db.execute(
            select(ReportFormModel.report_form_id)
            .where(
                ReportFormModel.infra_id == infra_id,
                ReportFormModel.company_name == company_name,
            )
            .order_by(ReportFormModel.last_modified_time.desc())
            .limit(1)
        )
        report_form_id = report_form_id_result.scalars().first()

        if not report_form_id:
            raise HTTPException(
                status_code=404,
                detail=f'Report form not found for infra "{infra_name}" and company "{company_name}"',
            )

        last_posted_report_count = await db.execute(
            select(func.count(PostedReportModel.posted_report_id))
        )
        last_posted_report_id = last_posted_report_count.scalar()


        bucket_name = os.environ["MINIO_BUCKET"]
        # bucket_name = "ymtest"
        # 무결성 보장: MinIO 경로 생성
        posted_report_path = "/" + bucket_name + "/" + str(last_posted_report_id + 1)

        start_time_unix = int(start_time.timestamp())
        end_time_unix = int(end_time.timestamp())

        new_report = PostedReportModel(
            posted_report_path=posted_report_path,
            report_form_id=report_form_id,
            start_time=start_time_unix,
            end_time=end_time_unix,
            company_name=company_name,
            user_name=user_name,
        )

        db.add(new_report)
        await db.flush()
        await db.refresh(new_report)

        posted_report_id = new_report.posted_report_id
        print(posted_report_id)
        # Insert data into posted_reports table
        # Save original JSON data to MinIO bucket
        # 파일명: {posted_report_id}.json

        # TODO : pdf, png로도 저장되게 해야함
        data_json = json.dumps(data.dict())
        file_name = f"{posted_report_id}.json"

        bucket_name = os.environ["MINIO_BUCKET"]
        # bucket_name = "ymtest"

        with io.BytesIO(data_json.encode("utf-8")) as data_file:
            minio_client.put_object(
                bucket_name,  # bucket_name
                file_name,
                data_file,
                length=-1,
                part_size=10 * 1024 * 1024,
                content_type="application/json",
            )

        # 커밋 후 데이터 저장 완료
        await db.commit()

        return JSONResponse(
            content={
                "message": "Report submitted successfully",
                "posted_report_id": posted_report_id,
            },
            status_code=200,
        )
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@router.post("/api/upload-image")
async def upload_image_to_minio(file: UploadFile = File(...)):
    try:
        # 버킷 이름 (사전에 만들어져 있어야 함)
        bucket_name = os.environ["MINIO_BUCKET"]
        # bucket_name = "ymtest"

        # 파일 이름을 고유하게 설정 (예: 업로드된 파일의 이름 사용)
        file_name = file.filename

        # 파일을 MinIO에 업로드
        file_data = file.file.read()
        minio_client.put_object(
            bucket_name=bucket_name,
            object_name=file_name,
            data=io.BytesIO(file_data),
            length=len(file_data),
            content_type=file.content_type
        )

        # 영구적인 URL 생성
        file_url = f"http://127.0.0.1:9000/{bucket_name}/{file_name}"

        return JSONResponse(content={"url": file_url}, status_code=200)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)