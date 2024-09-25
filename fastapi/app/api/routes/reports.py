from fastapi import APIRouter
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
# from db import postgres_connection
from schemas.request_body import (
    ReportForm,
    # InstructionForm,
    # InspectionForm,
    SubmittedReportForm,
)
# from schemas import request_body

# from datetime import datetime
# import json

# 추가 
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

router = APIRouter()

# 설비에 대한 보고서(양식) 정보 입력 또는 수정 (sqlalchemy 적용)
@router.post("/api/report")
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
            select(InfraModel.infra_id).where(InfraModel.infra_name == infra_name)
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
            image_required = inspection.image_required

            new_topic = TopicFormModel(
                report_form_id=new_report.report_form_id,
                topic_form_name=topic_name,
                image_required=image_required,
            )
            db.add(new_topic)
            await db.flush()
            await db.refresh(new_topic)

            for instruction in inspection.instruction_list:
                new_instruction = InstructionFormModel(
                    topic_form_id=new_topic.topic_form_id,
                    instruction=instruction.instruction,
                    instruction_type=instruction.instruction_type,
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



# 설비에 대해 가장 최근에 작성된 보고서 양식을 가져오기 (sqlalchemy 적용)
@router.post("/api/report-form")
async def get_report_form(body: SubmittedReportForm, db: AsyncSession = Depends(connect_db)):
    infra_name = body.infra
    company_name = body.company_name

    if not infra_name:
        raise HTTPException(
            status_code=400, detail="Infra name is missing in request body"
        )
    
    try:
        # Check if the infra_name exists 
        infra_id_result = await db.execute(
            select(InfraModel.infra_id).where(InfraModel.infra_name == infra_name)
        )
        infra_id = infra_id_result.scalars().first()

        if not infra_id:
            raise HTTPException(status_code=404, detail="Infra not found")

        
        
        # Build the query to get the most recent report_form_id for the given infra_id
        stmt = select(ReportFormModel.report_form_id, ReportFormModel.last_modified_time).where(ReportFormModel.infra_id == infra_id)

        if company_name:
            stmt = stmt.where(ReportFormModel.company_name == company_name)
        stmt = stmt.order_by(ReportFormModel.report_form_id.desc()).limit(1)
        result = await db.execute(stmt)
        
        report_form = result.fetchone()
        
        
        if not report_form:
            raise HTTPException(
                status_code=404, detail=f"No report form found for infra '{infra_name}'"
            )

        report_form_id = report_form.report_form_id
        last_modified_time = report_form.last_modified_time

        # Retrieve report form data
        stmt = (
            select(
                TopicFormModel.topic_form_name,
                TopicFormModel.image_required,
                func.array_agg(
                    func.json_build_object(
                        'instruction', InstructionFormModel.instruction,
                        'instruction_type', InstructionFormModel.instruction_type,
                        'options', InstructionFormModel.options,
                        'answer', InstructionFormModel.answer
                    )
                ).label("instruction_list")
            )
            .join(InstructionFormModel, TopicFormModel.topic_form_id == InstructionFormModel.topic_form_id)
            .where(TopicFormModel.report_form_id == report_form_id)
            .group_by(TopicFormModel.topic_form_name, TopicFormModel.image_required)
        )
        result = await db.execute(stmt)
        report_form_data = result.fetchall()

        if not report_form_data:
            raise HTTPException(
                status_code=404,
                detail=f"No report form data found for report form id '{report_form_id}'",
            )

        # Format the response data
        response_data = {
            "infra_name": infra_name,
            "last_modified_time": last_modified_time,
            "report_form_id": report_form_id,
            "inspection_list": [],
        }

        for record in report_form_data:
            inspection = {
                "topic": record.topic_form_name,
                "instruction_list": [],
                "image_required": record.image_required,
            }
            for instruction_json in record.instruction_list:
                instruction_data = {
                    "instruction": instruction_json["instruction"],
                    "instruction_type": instruction_json["instruction_type"],
                    "options": instruction_json["options"],
                    "answer": instruction_json["answer"],
                }
                inspection["instruction_list"].append(instruction_data)
            response_data["inspection_list"].append(inspection)

        return JSONResponse(content=response_data, status_code=200)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving report form: {str(e)}"
        )


# 설비에 대한 모든 보고서 양식을 가져오기
@router.post("/api/report-forms")
async def get_report_forms(body: SubmittedReportForm,  db: AsyncSession = Depends(connect_db)):
    infra_name = body.infra
    company_name = body.company_name

    if not infra_name:
        raise HTTPException(
            status_code=400, detail="Infra name is missing in request body"
        )

    try:
        # Check if the infra_name exists 
        infra_id_result = await db.execute(
            select(InfraModel.infra_id).where(InfraModel.infra_name == infra_name)
        )
        infra_id = infra_id_result.scalars().first()

        if not infra_id:
            raise HTTPException(status_code=404, detail="Infra not found")


        # Build the query to get the report_form_ids for the given infra_id
        stmt = select(ReportFormModel.report_form_id).where(ReportFormModel.infra_id == infra_id)

        if company_name:
            stmt = stmt.where(ReportFormModel.company_name == company_name)

        result = await db.execute(stmt)
        report_form_ids = result.scalars().all()  # Retrieves all report_form_ids

        # Format the response data
        response_data = {
            "infra_name": infra_name,
            "report_form_ids": report_form_ids,
        }

        return JSONResponse(content=response_data, status_code=200)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving report form data: {str(e)}"
        )
    
# 보고서 id로 보고서 정보 가져오기
@router.get("/api/report-form/")
async def get_report_form_id(report_form_id: int, db: AsyncSession = Depends(connect_db)):
    print(report_form_id)
    try:
        # Check if the report form exists
        result = await db.execute(select(ReportFormModel).where(ReportFormModel.report_form_id == report_form_id))
        report_form = result.scalar()

        if not report_form:
            raise HTTPException(
                status_code=404, detail=f"Report form with ID '{report_form_id}' not found"
            )
        # Query to get the related topic forms and instruction forms
        stmt = (
            select(
                TopicFormModel.topic_form_name,
                TopicFormModel.image_required,
                func.array_agg(
                    func.json_build_object(
                        'instruction', InstructionFormModel.instruction,
                        'instruction_type', InstructionFormModel.instruction_type,
                        'options', InstructionFormModel.options,
                        'answer', InstructionFormModel.answer
                    )
                ).label("instruction_list")
            )
            .join(InstructionFormModel, TopicFormModel.topic_form_id == InstructionFormModel.topic_form_id)
            .where(TopicFormModel.report_form_id == report_form_id)
            .group_by(TopicFormModel.topic_form_name, TopicFormModel.image_required)
        )
        
        result = await db.execute(stmt)
        report_form_data = result.fetchall()

        if not report_form_data:
            raise HTTPException(
                status_code=404, detail=f"No topic forms found for report form ID '{report_form_id}'"
            )

        # Format the response data
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
                "image_required": record.image_required,
            }
            for instruction_json in record.instruction_list:
                instruction_data = {
                    "instruction": instruction_json["instruction"],
                    "instruction_type": instruction_json["instruction_type"],
                    "options": instruction_json["options"],
                    "answer": instruction_json["answer"],
                }
                inspection["instruction_list"].append(instruction_data)
            response_data["inspection_list"].append(inspection)

        return JSONResponse(content=response_data, status_code=200)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving report form data: {str(e)}"
        )