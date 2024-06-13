from fastapi import APIRouter
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from db import minio_connection
from db import postgres_connection
from schemas import response_body
from schemas import request_body


import pytz
import os
import json
import io

router = APIRouter()

# 설비에 해당하는 보고서 제출 목록 가져오기 (날짜 기준 오름차순)
@router.get("/api/posted-reports")
async def get_posted_reports(infra: str = None, company_name: str = None):
    if not infra:
        raise HTTPException(status_code=400, detail="Infra name is missing in query parameters")
    if not company_name:
        raise HTTPException(status_code=400, detail="Company name is missing in query parameters")

    try:
        # 데이터베이스 연결
        conn = await postgres_connection.connect_db()

        # 보고서 제출 목록 조회
        reports = await conn.fetch('''
            SELECT * FROM posted_reports
            WHERE report_form_id IN (
                SELECT report_form_id FROM report_forms
                WHERE infra_id = (
                    SELECT infra_id FROM infras WHERE infra_name = $1 AND company_name = $2
                )
            )
            ORDER BY start_time ASC;
        ''', infra, company_name)

        # 데이터베이스 연결 종료
        await conn.close()

        # 보고서 목록을 JSON 응답으로 반환
        reports_list = [{
            'posted_report_id': report['posted_report_id'],
            'posted_report_path': report['posted_report_path'],
            'start_time': report['start_time'],
            'end_time': report['end_time'],
            'company_name': report['company_name']
        } for report in reports]

        return JSONResponse(content={"posted_reports": reports_list}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# 설비의 특정 날짜 보고서 가져오기
@router.get("/api/posted-report-by-date")
async def get_posted_report_by_date(infra: str = None, company_name: str = None, Unixtime: int = None):
    if not infra:
        raise HTTPException(status_code=400, detail="Infra name is missing in query parameters")
    if not company_name:
        raise HTTPException(status_code=400, detail="Company name is missing in query parameters")
    if not Unixtime:
        raise HTTPException(status_code=400, detail="Unixtime is missing in query parameters")

    # Unix timestamp를 datetime 객체로 변환
    try:
        report_date = datetime.fromtimestamp(Unixtime, tz=pytz.utc)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid Unixtime: {str(e)}")

    try:
        # DB 연결
        conn = await postgres_connection.connect_db()

        # 인프라 이름에 해당하는 infra_id 가져오기
        infra_id = await conn.fetchval('SELECT infra_id FROM infras WHERE infra_name = $1 AND company_name = $2', infra, company_name)

        if not infra_id:
            raise HTTPException(status_code=404, detail=f'Infra "{infra}" not found for company "{company_name}"')

        # 특정 날짜에 해당하는 보고서 조회
        reports = await conn.fetch('''
            SELECT * FROM posted_reports
            WHERE report_form_id IN (
                SELECT report_form_id FROM report_forms
                WHERE infra_id = $1
            ) AND start_time <= to_timestamp($2) AND end_time >= to_timestamp($2)
        ''', infra_id, Unixtime)

        # 데이터베이스 연결 종료
        await conn.close()

        return JSONResponse(content={"posted_reports": reports}, status_code=200)

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


# infra, company_name에 따른 작성된 보고서를 Minio에서 가져오기
@router.get("/api/posted-report")
async def get_posted_report_from_minio_with_infra_company_name(request: Request, infra: str = None, company_name: str = None):
    if not infra:
        raise HTTPException(status_code=400, detail="Infra name is missing in query parameters")
    if not company_name:
        raise HTTPException(status_code=400, detail="Company name is missing in query parameters")

    try:
        # 데이터베이스 연결
        conn = await postgres_connection.connect_db()

                # 인프라와 회사 이름으로 report path의 마지막 숫자 가져오기
        last_number = await conn.fetchval('''
            SELECT CAST(substring(posted_report_path FROM '/([0-9]+)$') AS INTEGER) AS last_number
            FROM posted_reports
            WHERE report_form_id IN (
                SELECT report_form_id FROM report_forms
                WHERE infra_id = (
                    SELECT infra_id FROM infras WHERE infra_name = $1 AND company_name = $2
                )
            )
            ORDER BY last_number DESC
            LIMIT 1;
        ''', infra, company_name)

        if last_number is None:
            raise HTTPException(status_code=404, detail=f'No report found for infra "{infra}" and company "{company_name}"')

        # 데이터베이스 연결 종료
        await conn.close()

        # Minio에서 파일 가져오기
        file_name = f"{last_number}.json"
        response = minio_connection.minio_client.get_object(os.environ['MINIO_BUCKET'], file_name)

        # 파일 데이터를 읽어서 반환
        data = response.read()
        response.close()
        response.release_conn()

        # 바이트 데이터를 문자열로 디코딩 (JSON 형식 가정)
        data_str = data.decode('utf-8')

        # JSON 문자열을 파이썬 딕셔너리로 변환
        report_data = json.loads(data_str)

        return JSONResponse(content={"message": "Report fetched successfully", "report": report_data}, status_code=200)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)



@router.post("/api/report")
async def submit_inspected_report(request: Request, data: request_body.InspectedReport):
    try:
        # Extract data from JSON
        start_time = int(data.start_time)
        end_time = int(data.end_time)
        infra_name = data.infra
        company_name = data.company_name
        inspection_list = data.inspection_list
        
        # Connect to the database
        conn = await postgres_connection.connect_db()

        # infra_id 가져오기
        infra_id = await conn.fetchval('''
            SELECT infra_id FROM infras WHERE infra_name = $1 AND company_name = $2
        ''', infra_name, company_name)
        
        if not infra_id:
            raise HTTPException(status_code=404, detail=f'Infra "{infra_name}" not found for company "{company_name}"')

        # report_form_id 가져오기
        report_form_id = await conn.fetchval('''
            SELECT report_form_id FROM report_forms WHERE infra_id = $1 AND company_name = $2 ORDER BY last_modified_time DESC LIMIT 1
        ''', infra_id, company_name)
        
        if not report_form_id:
            raise HTTPException(status_code=404, detail=f'Report form not found for infra "{infra_name}" and company "{company_name}"')

        last_posted_report_id = await conn.fetchval('''
            SELECT count(*) FROM posted_reports;
        ''')

        # 무결성 보장: MinIO 경로 생성
        posted_report_path = "/" + str(os.environ['MINIO_BUCKET']) + "/" + str(last_posted_report_id+1)

        # Insert data into posted_reports table
        posted_report_id = await conn.fetchval('''
            INSERT INTO posted_reports (posted_report_path, report_form_id, start_time, end_time, company_name)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING posted_report_id
        ''', posted_report_path, report_form_id, start_time, end_time, company_name)
        await conn.close()

        # Save original JSON data to MinIO bucket
        # 파일명: {posted_report_id}.json
        data_json = json.dumps(data.dict())
        file_name = f"{posted_report_id}.json"
        with io.BytesIO(data_json.encode('utf-8')) as data_file:
            minio_connection.minio_client.put_object(os.environ['MINIO_BUCKET'], file_name, data_file, length=-1, part_size=10*1024*1024, content_type="application/json")

        return JSONResponse(content={"message": "Report submitted successfully", "posted_report_id": posted_report_id}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)