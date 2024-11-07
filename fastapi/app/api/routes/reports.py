from fastapi import APIRouter
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from schemas.request_body import ReportForm, SubmittedReportForm

from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from schemas.models import Infra as InfraModel
from schemas.models import ReportForm as ReportFormModel
from schemas.models import TopicForm as TopicFormModel
from schemas.models import InstructionForm as InstructionFormModel
from db.postgres_connection import connect_db
from sqlalchemy import func
from sqlalchemy.future import select
from sqlalchemy import delete
from schemas.response_body import DBReportResponseModel,DBReportsResponseModel

router = APIRouter()

# 설비에 대한 보고서(양식) 정보 입력 또는 수정
@router.post("/api/report", summary="점검절차 입력/수정", description="설비에 대한 점검절차를 입력하거나 수정합니다. 기존 데이터가 있으면 삭제하고 새로운 데이터를 저장합니다."
             ,responses={
                200: {
                    "description": "점검절차을 정보 입력/수정 성공.",
                    "content": {
                        "application/json": {
                            "example":{
                                "message": "Data saved successfully"
                            }                          
                        }
                    }
                }
            })
async def submit_report_form(
    data: ReportForm, db: AsyncSession = Depends(connect_db)
):
    try:
        infra_name = data.infra
        last_modified_time = int(data.last_modified_time)
        company_name = data.company_name

        if not infra_name:
            raise HTTPException(status_code=400, detail="Infra field is required")

        infra_id_result = await db.execute(
            select(InfraModel.infra_id).where(
                InfraModel.infra_name == infra_name,
                InfraModel.company_name == company_name)
        )
        infra_id = infra_id_result.scalars().first()


        if not infra_id:
            raise HTTPException(status_code=404, detail="Infra not found")

        existing_report_form_result = await db.execute(
            select(ReportFormModel).where(
                ReportFormModel.infra_id == infra_id,
                ReportFormModel.company_name == company_name,
            )
        )

        existing_report_form = existing_report_form_result.scalars().first()
        

        # 기존 정보 삭제
        if existing_report_form is not None:
            await db.execute(
                delete(ReportFormModel).where(
                    ReportFormModel.report_form_id == existing_report_form.report_form_id
                )
            )
            await db.flush()

        new_report = ReportFormModel(
            infra_id=infra_id,
            company_name=company_name,
            last_modified_time=last_modified_time,
        )

        db.add(new_report)
        await db.flush()
        
        for inspection in data.inspection_list:
            topic_name = inspection.topic
            new_topic = TopicFormModel(
                report_form_id=new_report.report_form_id,
                topic_form_name=topic_name,
            )
            db.add(new_topic)
            await db.flush()
            await db.refresh(new_topic)

            for instruction in inspection.instruction_list:
                new_instruction = InstructionFormModel(
                    topic_form_id=new_topic.topic_form_id,
                    instruction=instruction.instruction,
                    instruction_type=instruction.instruction_type,
                    img_url=instruction.img_url,
                    options=instruction.options,
                    answer=instruction.answer,
                )
                db.add(new_instruction)
                await db.flush()

        await db.commit()
        return {"message": "Data saved successfully"}

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error saving data: {str(e)}")


# 설비에 대해 가장 최근에 작성된 점검절차을 가져오기
@router.get("/api/report-form", summary="최근 점검절차 조회(AND)", description="설비와 회사 이름을 기준으로 가장 최근에 작성된 점검절차를 가져옵니다."
             , response_model=DBReportResponseModel)
async def get_report_form(
    infra: str,
    company_name: str,
    db: AsyncSession = Depends(connect_db)
):
    if not infra:
        raise HTTPException(
            status_code=400, detail="Infra name is missing in query parameters"
        )
    
    try:
        infra_id_result = await db.execute(
            select(InfraModel.infra_id).where(
                InfraModel.infra_name == infra,
                InfraModel.company_name == company_name)
        )
        infra_id = infra_id_result.scalars().first()


        if not infra_id:
            raise HTTPException(status_code=404, detail="Infra not found")

        stmt = select(ReportFormModel.report_form_id, ReportFormModel.last_modified_time).where(ReportFormModel.infra_id == infra_id)

        if company_name:
            stmt = stmt.where(ReportFormModel.company_name == company_name)

        stmt = stmt.order_by(ReportFormModel.report_form_id.desc()).limit(1)
        result = await db.execute(stmt)
        

        report_form = result.fetchone()
        

        if not report_form:
            raise HTTPException(
                status_code=404, detail=f"No report form found for infra '{infra}'"
            )

        report_form_id = report_form.report_form_id
        last_modified_time = report_form.last_modified_time

        stmt = (
            select(
                TopicFormModel.topic_form_name,
                func.array_agg(
                    func.json_build_object(
                        'instruction', InstructionFormModel.instruction,
                        'instruction_type', InstructionFormModel.instruction_type,
                        'img_url', InstructionFormModel.img_url,
                        'options', InstructionFormModel.options,
                        'answer', InstructionFormModel.answer
                    )
                ).label("instruction_list")
            )
            .join(InstructionFormModel, TopicFormModel.topic_form_id == InstructionFormModel.topic_form_id)
            .where(TopicFormModel.report_form_id == report_form_id)
            .group_by(TopicFormModel.topic_form_name)
        )
        result = await db.execute(stmt)
        report_form_data = result.fetchall()

        if not report_form_data:
            raise HTTPException(
                status_code=404,
                detail=f"No report form data found for report form id '{report_form_id}'",
            )

        response_data = {
            "infra_name": infra,
            "last_modified_time": last_modified_time,
            "report_form_id": report_form_id,
            "inspection_list": [],
        }

        for record in report_form_data:
            inspection = {
                "topic": record.topic_form_name,
                "instruction_list": [],
            }
            for instruction_json in record.instruction_list:
                instruction_data = {
                    "instruction": instruction_json["instruction"],
                    "instruction_type": instruction_json["instruction_type"],
                    "options": instruction_json["options"],
                    "answer": instruction_json["answer"],
                    "img_url": instruction_json["img_url"]
                }
                inspection["instruction_list"].append(instruction_data)
            response_data["inspection_list"].append(inspection)

        return JSONResponse(content=response_data, status_code=200)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving report form: {str(e)}"
        )

# 설비에 대한 모든 점검절차을 가져오기
@router.post("/api/report-forms", summary="모든 점검절차 조회(AND)", description="설비와 회사 이름을 기준으로 작성된 모든 점검절차 ID를 반환합니다."
             ,response_model = DBReportsResponseModel)
async def get_report_forms(body: SubmittedReportForm, db: AsyncSession = Depends(connect_db)):
    infra_name = body.infra
    company_name = body.company_name

    if not infra_name:
        raise HTTPException(
            status_code=400, detail="Infra name is missing in request body"
        )

    try:
        infra_id_result = await db.execute(
            select(InfraModel.infra_id).where(InfraModel.infra_name == infra_name)
        )
        infra_id = infra_id_result.scalars().first()

        if not infra_id:
            raise HTTPException(status_code=404, detail="Infra not found")

        stmt = select(ReportFormModel.report_form_id).where(ReportFormModel.infra_id == infra_id)

        if company_name:
            stmt = stmt.where(ReportFormModel.company_name == company_name)

        result = await db.execute(stmt)
        report_form_ids = result.scalars().all()

        response_data = {
            "infra_name": infra_name,
            "report_form_ids": report_form_ids,
        }

        return JSONResponse(content=response_data, status_code=200)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving report form data: {str(e)}"
        )


# 보고서 ID로 보고서 정보 가져오기
@router.get("/api/report-form/", summary="점검절차 ID로 점검절차 정보 조회(AND)", description="특정 점검젗라 ID를 사용하여 해당 점검절차을 조회합니다."
            ,response_model = DBReportResponseModel)
async def get_report_form_id(report_form_id: int, db: AsyncSession = Depends(connect_db)):
    try:
        result = await db.execute(select(ReportFormModel).where(ReportFormModel.report_form_id == report_form_id))
        report_form = result.scalar()

        if not report_form:
            raise HTTPException(
                status_code=404, detail=f"Report form with ID '{report_form_id}' not found"
            )

        stmt = (
            select(
                TopicFormModel.topic_form_name,
                func.array_agg(
                    func.json_build_object(
                        'instruction', InstructionFormModel.instruction,
                        'instruction_type', InstructionFormModel.instruction_type,
                        'img_url', InstructionFormModel.img_url,
                        'options', InstructionFormModel.options,
                        'answer', InstructionFormModel.answer
                    )
                ).label("instruction_list")
            )
            .join(InstructionFormModel, TopicFormModel.topic_form_id == InstructionFormModel.topic_form_id)
            .where(TopicFormModel.report_form_id == report_form_id)
            .group_by(TopicFormModel.topic_form_name)
        )
        
        result = await db.execute(stmt)
        report_form_data = result.fetchall()

        if not report_form_data:
            raise HTTPException(
                status_code=404, detail=f"No topic forms found for report form ID '{report_form_id}'"
            )

        response_data = {
            "report_form_id": report_form_id,
            "infra_id": report_form.infra_id,
            "company_name": report_form.company_name,
            "last_modified_time": report_form.last_modified_time,
            "inspection_list": [],
        }

        for record in report_form_data:
            inspection = {
                "topic": record.topic_form_name,
                "instruction_list": [],
            }
            for instruction_json in record.instruction_list:
                instruction_data = {
                    "instruction": instruction_json["instruction"],
                    "instruction_type": instruction_json["instruction_type"],
                    "options": instruction_json["options"],
                    "answer": instruction_json["answer"],
                    "img_url": instruction_json["img_url"]
                }
                inspection["instruction_list"].append(instruction_data)
            response_data["inspection_list"].append(inspection)

        return JSONResponse(content=response_data, status_code=200)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving report form data: {str(e)}"
        )
