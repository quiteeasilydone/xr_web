from fastapi import APIRouter
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from db import minio_connection
from db import postgres_connection
from schemas import reponse_body
import pytz
import os
import json
import io

router = APIRouter()



# 설비에 해당하는 보고서 제출 목록 가져오기(날짜 기준 오름차순)
@router.get("/api/posted-reports")
async def get_posted_reports(request: Request, infra: str = None):
    try:
        # 인프라 이름 파라미터 확인
        if not infra:
            raise HTTPException(status_code=400, detail="Infra name is missing in query parameters")
        infra_name = infra

        # 데이터베이스 연결
        conn = await postgres_connection.connect_db()

        # 보고서 제출 목록 조회
        reports = await conn.fetch('''
            SELECT * FROM posted_reports
            WHERE report_form_id IN (
                SELECT report_form_id FROM report_forms
                WHERE infra_id = (
                    SELECT infra_id FROM infras WHERE infra_name = $1
                )
            )
            ORDER BY start_time ASC;
        ''', infra_name)

        # 데이터베이스 연결 종료
        await conn.close()

        # 보고서 목록을 JSON 응답으로 반환
        reports_list = [{
            'posted_report_id': report['posted_report_id'],
            'posted_report_path': report['posted_report_path'],
            'start_time': report['start_time'],
            'end_time': report['end_time'],
            'user_name': report['user_name']
        } for report in reports]

        return JSONResponse(content={"posted_reports": reports_list}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# 설비의 특정 날짜 보고서 가져오기
@router.get("/api/posted-reports")
async def get_posted_reports(request: Request, infra: str = None, Unixtime: int = None):
    # 인프라 이름 파라미터 확인
    if not infra:
        raise HTTPException(status_code=400, detail="Infra name is missing in query parameters")
    
    # Unixtime 파라미터 확인
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
        infra_id = await conn.fetchval('SELECT infra_id FROM infras WHERE infra_name = $1', infra)
        
        if not infra_id:
            raise HTTPException(status_code=404, detail=f'Infra "{infra}" not found')
        
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

# 점검 완료 결과를 DB 및 minIO에 저장
@router.post("/api/report")
async def submit_inspected_report(request: Request, data: reponse_body.InspectedReport):
    try:
        # Extract data from JSON
        start_time = int(data.start_time)
        end_time = int(data.end_time)
        report_form_id = int(data.report_form_id)
        infra_name = data.infra
        inspection_list = data.inspection_list
        
        # Connect to the database
        conn = await postgres_connection.connect_db()

        last_posted_report_id = await conn.fetchval('''
            SELECT count(*) FROM posted_reports;
        ''')

        # 1, 2 무결성 보장해야 함
        # 1
        posted_report_path = "/" + str(os.environ['MINIO_BUCKET']) + "/" + str(last_posted_report_id)

        # Insert data into posted_reports table
        posted_report_id = await conn.fetchval('''
            INSERT INTO posted_reports (posted_report_path, report_form_id, start_time, end_time, user_name)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING posted_report_id
        ''', posted_report_path, report_form_id, start_time, end_time, "0000")
        await conn.close()

        # 2
        # Save original JSON data to MinIO bucket
        # 파일명: {posted_report_id}.json
        data_json = json.dumps(data.dict())
        file_name = f"{posted_report_id}.json"
        with io.BytesIO(data_json.encode('utf-8')) as data_file:
            minio_connection.minio_client.put_object(os.environ['MINIO_BUCKET'], file_name, data_file, length=-1, part_size=10*1024*1024, content_type="application/json")

        return JSONResponse(content={"message": "Report submitted successfully", "posted_report_id": posted_report_id}, status_code=200)
    except Exception as e:
        await conn.close()
        raise HTTPException(status_code=500, detail=f"Error submitting report: {str(e)}")
