from fastapi import APIRouter
from fastapi.responses import JSONResponse
from fastapi import FastAPI, Request, HTTPException, Depends
from schemas.request_body import Infra
from db import postgres_connection

router = APIRouter()

# 앞으로 모든 API에는 사용자 정보가 있어야 합니다.

# body에 사용자 정보(email)를 담아서 주면 참조하여 해당 사용자가 작성한 것들만 return
# infra name에 해당하는 가장 최신의 report 받기
@router.get("/api/infra/report")
async def get_recent_report_form(company_name: str, infra: str = None):
    if not infra:
        raise HTTPException(status_code=400, detail="Infra name is missing in query parameters")

    conn = await postgres_connection.connect_db()

    try:
        # 사용자와 인프라 이름으로 infra_id 조회
        infra_id = await conn.fetchval('''
            SELECT infra_id FROM infras WHERE infra_name = $1 AND company_name = $2
        ''', infra, company_name)
        if not infra_id:
            raise HTTPException(status_code=404, detail=f'Infra name: {infra} not found for company: {company_name}')

        # 가장 최신의 report 조회
        report = await conn.fetchrow('''
            SELECT * FROM report_forms WHERE infra_id = $1 ORDER BY report_form_id DESC LIMIT 1
        ''', infra_id)
        if not report:
            raise HTTPException(status_code=404, detail=f'No reports found for infra name: {infra}')

        report_form_id = report['report_form_id']

        # 카테고리 및 해당하는 주제와 지시사항 조회
        topic_data = await conn.fetch('SELECT * FROM topic_forms WHERE report_form_id = $1', report_form_id)

        # 보고서 내용을 담을 리스트 생성
        inspection_list = []

        # 각 카테고리에 대해 처리
        for topic in topic_data:
            # 주제와 지시사항 조회
            instruction_data = await conn.fetch('SELECT * FROM instruction_forms WHERE topic_form_id = $1', topic['topic_form_id'])

            # 지시사항을 담을 리스트 생성
            instructions_list = []

            # 각 지시사항에 대해 처리
            for instruction in instruction_data:
                instructions_list.append({
                    'instruction': instruction['instruction'],
                    'instruction_type': instruction['instruction_type'],
                    'options': instruction['options'],
                    'answer': instruction['answer']
                })

            # 각 카테고리에 대한 정보를 추가
            inspection_list.append({
                'topic': topic['topic_form_name'],
                'instruction_list': instructions_list,
                'image_required': topic['image_required']
            })

        # JSON 응답 생성
        response_data = {
            'infra': infra,
            'report_form_id': report_form_id,
            'inspection_list': inspection_list
        }

        return JSONResponse(content=response_data, status_code=200)
    except Exception as e:
        await conn.close()
        raise HTTPException(status_code=500, detail=f"Error retrieving data: {str(e)}")

# 전체 설비 목록 가져오기
# 페이지네이션 필요
@router.get("/api/infra-list")
async def get_infra_list(company_name: str):
    try:
        if not company_name:
            raise HTTPException(status_code=400, detail="Company name is missing in query parameters")

        # DB 연결
        conn = await postgres_connection.connect_db()

        # 해당 회사의 모든 인프라 이름 가져오기
        infra_list = await conn.fetch('SELECT infra_name FROM infras WHERE company_name = $1', company_name)

        # 데이터베이스 연결 종료
        await conn.close()

        # 인프라 목록을 JSON 응답으로 반환
        infra_names = [record['infra_name'] for record in infra_list]
        return JSONResponse(content={"infra_list": infra_names}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


# 설비 추가
@router.post("/api/infra")
async def add_infra(infra: Infra):
    infra_name = infra.infra_name
    company_name = infra.company_name

    if not infra_name:
        raise HTTPException(status_code=400, detail="Infra name is missing in request body")

    # DB 연결
    conn = await postgres_connection.connect_db()

    try:
        # 동일한 infra_name이 존재하는지 확인
        existing_infra = await conn.fetchval('''
            SELECT infra_id FROM infras WHERE infra_name = $1
        ''', infra_name)

        if existing_infra:
            raise HTTPException(status_code=406, detail="Infra name is already exists.")
        # infras에 infra_name과 company_name row 추가
        await conn.execute('''
            INSERT INTO infras (infra_name, company_name) 
            VALUES ($1, $2)
        ''', infra_name, company_name)

        # DB 연결 종료
        await conn.close()

        return JSONResponse(content={"message": "Infra added successfully."}, status_code=201)
    except Exception as e:
        await conn.close()
        raise HTTPException(status_code=500, detail=f"Error adding infra: {str(e)}")