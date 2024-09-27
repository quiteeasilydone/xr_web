from fastapi import APIRouter
from fastapi.responses import JSONResponse
from fastapi import FastAPI, Request, HTTPException, Depends
from schemas.request_body import Infra
# from db import postgres_connection

# 추가
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from schemas.models import Infra as InfraModel
# from schemas.models import ReportForm as ReportFormModel
# from schemas.models import TopicForm as TopicFormModel
# from schemas.models import InstructionForm as InstructionFormModel
from db.postgres_connection import connect_db
# from sqlalchemy import func
from sqlalchemy.future import select
# from sqlalchemy import delete

router = APIRouter()


# 앞으로 모든 API에는 사용자 정보가 있어야 합니다.

# body에 사용자 정보(email)를 담아서 주면 참조하여 해당 사용자가 작성한 것들만 return

# infra name에 해당하는 가장 최신의 report 받기 => reports.py에 있음
# @router.get("/api/infra/report")
# async def get_recent_report_form(company_name: str, infra: str = None, db: AsyncSession = Depends(connect_db)):
#     if not infra:
#         raise HTTPException(status_code=400, detail="Infra name is missing in query parameters")

#     try:
#         # 사용자와 인프라 이름으로 infra_id 조회
#         infra_result = await db.execute(
#             select(InfraModel.infra_id).where(InfraModel.infra_name == infra, InfraModel.company_name == company_name)
#         )
#         infra_id = infra_result.scalars().first()

#         if not infra_id:
#             raise HTTPException(status_code=404, detail=f'Infra name: {infra} not found for company: {company_name}')

#         # 가장 최신의 report 조회
#         report_result = await db.execute(
#             select(ReportFormModel).where(ReportFormModel.infra_id == infra_id).order_by(ReportFormModel.report_form_id.desc()).limit(1)
#         )
#         report = report_result.scalar()

#         if not report:
#             raise HTTPException(status_code=404, detail=f'No reports found for infra name: {infra}')

#         report_form_id = report.report_form_id

#         # 카테고리 및 해당하는 주제와 지시사항 조회
#         topic_result = await db.execute(
#             select(TopicFormModel, InstructionFormModel).join(
#                 InstructionFormModel, TopicFormModel.topic_form_id == InstructionFormModel.topic_form_id
#             ).where(TopicFormModel.report_form_id == report_form_id)
#         )
#         topics = topic_result.fetchall()

#         inspection_list = []
#         for topic, instruction in topics:
#             inspection_list.append({
#                 'topic': topic.topic_form_name,
#                 'instruction_list': [{
#                     'instruction': instruction.instruction,
#                     'instruction_type': instruction.instruction_type,
#                     'options': instruction.options,
#                     'answer': instruction.answer
#                 }],
#                 'image_required': topic.image_required
#             })

#         response_data = {
#             'infra': infra,
#             'report_form_id': report_form_id,
#             'inspection_list': inspection_list
#         }

#         return JSONResponse(content=response_data, status_code=200)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error retrieving data: {str(e)}")


# 전체 설비 목록 가져오기
@router.get("/api/infras")
async def get_infra_list(company_name: str, db: AsyncSession = Depends(connect_db)):
    try:
        if not company_name:
            raise HTTPException(
                status_code=400, detail="Company name is missing in query parameters"
            )

        # 해당 회사의 모든 인프라 이름 가져오기
        infra_result = await db.execute(
            select(InfraModel.infra_name).where(InfraModel.company_name == company_name)
        )
        infra_list = infra_result.scalars().all()

        return JSONResponse(content={"infra_list": infra_list}, status_code=200)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


# 설비 추가
@router.post("/api/infra")
async def add_infra(infra: Infra, db: AsyncSession = Depends(connect_db)):
    infra_name = infra.infra_name
    company_name = infra.company_name
    if not infra_name:
        raise HTTPException(
            status_code=400, detail="Infra name is missing in request body"
        )

    try:
        # 동일한 infra_name이 존재하는지 확인
        existing_infra_result = await db.execute(
            select(InfraModel.infra_id).where(InfraModel.infra_name == infra_name)
        )
        existing_infra = existing_infra_result.scalars().first()

        if existing_infra:
            raise HTTPException(status_code=406, detail="Infra name already exists.")

        # 새 인프라 추가
        new_infra = InfraModel(infra_name=infra_name, company_name=company_name)
        db.add(new_infra)
        await db.commit()

        return JSONResponse(
            content={"message": "Infra added successfully."}, status_code=201
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error adding infra: {str(e)}")