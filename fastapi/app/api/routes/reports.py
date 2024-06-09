from fastapi import APIRouter
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from db import postgres_connection
from schemas.request_body import ReportForm, InstructionForm, InspectionForm, SubmittedReportForm
from schemas import request_body

from datetime import datetime
import json

router = APIRouter()

# 설비에 대한 보고서(양식) 정보 입력 또는 수정
@router.post("/api/reports")
async def submit_report_form(request: Request, data: ReportForm):
    # json data parsing
    infra_name = data.infra
    last_modified_time_str = data.last_modified_time

    # company_name
    company_name = data.company_name

    # Check if infra_name is provided
    if not infra_name:
        raise HTTPException(status_code=400, detail="Infra field is required")

    # 데이터베이스에 데이터를 저장 또는 수정
    conn = await postgres_connection.connect_db()

    try:
        # Convert last_modified_time from string to datetime
        last_modified_time = datetime.strptime(last_modified_time_str, "%Y-%m-%dT%H:%M:%S")

        # Check if infra_name already exists in the infras table
        infra_id = await conn.fetchval('''
            SELECT infra_id FROM infras WHERE infra_name = $1
        ''', infra_name)

        # If infra_name does not exist, raise an error
        if not infra_id:
            raise HTTPException(status_code=404, detail="Infra not found")

        # Check if there is already a report form for the given infra_id and company_name
        existing_report_id = await conn.fetchval('''
            SELECT report_form_id FROM report_forms
            WHERE infra_id = $1 AND company_name = $2
        ''', infra_id, company_name)

        # Convert last_modified_time from string to datetime
        last_modified_time = datetime.strptime(last_modified_time_str, "%Y-%m-%dT%H:%M:%S")

        # If a report form already exists, update it and related tables
        if existing_report_id:
            # Update last_modified_time in report_forms table
            await conn.execute('''
                UPDATE report_forms
                SET last_modified_time = $1
                WHERE report_form_id = $2
            ''', last_modified_time, existing_report_id)

            # Update topic_forms and instruction_forms tables
            for inspection in data.inspection_list:
                topic_name = inspection.topic
                image_required = inspection.image_required

                # Check if the topic already exists
                existing_topic_id = await conn.fetchval('''
                    SELECT topic_form_id FROM topic_forms
                    WHERE report_form_id = $1 AND topic_form_name = $2
                ''', existing_report_id, topic_name)

                # If the topic exists, update it
                if existing_topic_id:
                    await conn.execute('''
                        UPDATE topic_forms
                        SET image_required = $1
                        WHERE topic_form_id = $2
                    ''', image_required, existing_topic_id)
                else:
                    # If the topic does not exist, insert it
                    topic_id = await conn.fetchval('''
                        INSERT INTO topic_forms ("report_form_id", "topic_form_name", "image_required")
                        VALUES ($1, $2, $3)
                        RETURNING topic_form_id
                    ''', existing_report_id, topic_name, image_required)

                # Update or insert instructions
                for instruction in inspection.instruction_list:
                    instruction_text = instruction.instruction
                    instruction_type = instruction.instruction_type
                    options = instruction.options
                    answer = instruction.answer

                    # Check if the instruction already exists
                    existing_instruction_id = await conn.fetchval('''
                        SELECT instruction_form_id FROM instruction_forms
                        WHERE topic_form_id = $1 AND instruction = $2
                    ''', topic_id, instruction_text)

                    # If the instruction exists, update it
                    if existing_instruction_id:
                        await conn.execute('''
                            UPDATE instruction_forms
                            SET instruction_type = $1, options = $2, answer = $3
                            WHERE instruction_form_id = $4
                        ''', instruction_type, options, answer, existing_instruction_id)
                    else:
                        # If the instruction does not exist, insert it
                        await conn.execute('''
                            INSERT INTO instruction_forms ("topic_form_id", "instruction", "instruction_type", "options", "answer")
                            VALUES ($1, $2, $3, $4, $5)
                        ''', topic_id, instruction_text, instruction_type, options, answer)
        else:
            # If a report form does not exist, insert new data
            report_id = await conn.fetchval('''
                INSERT INTO report_forms ("infra_id", "company_name", "last_modified_time")
                VALUES ($1, $2, $3)
                RETURNING report_form_id
            ''', infra_id, company_name, last_modified_time)

            # Insert into topic_forms and instruction_forms tables
            for inspection in data.inspection_list:
                topic_name = inspection.topic
                image_required = inspection.image_required

                # Insert into topic_forms
                topic_id = await conn.fetchval('''
                    INSERT INTO topic_forms ("report_form_id", "topic_form_name", "image_required")
                    VALUES ($1, $2, $3)
                    RETURNING topic_form_id
                ''', report_id, topic_name, image_required)

                for instruction in inspection.instruction_list:
                    instruction_text = instruction.instruction
                    instruction_type = instruction.instruction_type
                    options = instruction.options
                    answer = instruction.answer

                    # Insert into instruction_forms
                    await conn.execute('''
                        INSERT INTO instruction_forms ("topic_form_id", "instruction", "instruction_type", "options", "answer")
                        VALUES ($1, $2, $3, $4, $5)
                    ''', topic_id, instruction_text, instruction_type, options, answer)

        await conn.close()
        return JSONResponse(content={"message": "Data saved successfully"}, status_code=200)
    except Exception as e:
        # 예외 발생시 데이터베이스 연결 종료 후 예외 발생
        await conn.close()
        raise HTTPException(status_code=500, detail=f"Error saving data: {str(e)}")

# # 설비에 대한 보고서(양식) 정보 입력
# @router.post("/api/reports")
# async def submit_report_form(request: Request, data: ReportForm):
#     # json data parsing
#     infra_name = data.infra
#     last_modified_time_str = data.last_modified_time

#     # company_name
#     company_name = data.company_name

#     if not infra_name:
#         raise HTTPException(status_code=400, detail="Infra field is required")

#     # 데이터베이스에 데이터를 저장
#     conn = await postgres_connection.connect_db()

#     try:
#         # Convert last_modified_time from string to datetime
#         last_modified_time = datetime.strptime(last_modified_time_str, "%Y-%m-%dT%H:%M:%S")

#         # Check if infra_name already exists in the infras table
#         infra_id = await conn.fetchval('''
#             SELECT infra_id FROM infras WHERE infra_name = $1
#         ''', infra_name)

#         # If infra_name does not exist, insert into infras table
#         if not infra_id:
#             infra_id = await conn.fetchval('''
#                 INSERT INTO infras ("infra_name")
#                 VALUES ($1)
#                 RETURNING infra_id
#             ''', infra_name)

#         # Insert into report_forms with last_modified_time
#         report_id = await conn.fetchval('''
#             INSERT INTO report_forms ("infra_id", "company_name", "last_modified_time")
#             VALUES ($1, $2, $3)
#             RETURNING report_form_id
#         ''', infra_id, company_name, last_modified_time)

#         # inspectionList의 각 topic에 대해 처리
#         for inspection in data.inspection_list:
#             topic_name = inspection.topic
#             image_required = inspection.image_required
            
#             # topic_forms 테이블에 삽입
#             topic_id = await conn.fetchval('''
#                 INSERT INTO topic_forms ("report_form_id", "topic_form_name", "image_required")
#                 VALUES ($1, $2, $3)
#                 RETURNING topic_form_id
#             ''', report_id, topic_name, image_required)

#             # instructionList의 각 instruction에 대해 처리
#             for instruction in inspection.instruction_list:
#                 instruction_text = instruction.instruction
#                 instruction_type = instruction.instruction_type
#                 options = instruction.options  # options를 직접 사용합니다.
#                 answer = instruction.answer    # answer를 직접 사용합니다.
                
#                 # instruction_forms 테이블에 삽입
#                 await conn.execute('''
#                     INSERT INTO instruction_forms ("topic_form_id", "instruction", "instruction_type", "options", "answer")
#                     VALUES ($1, $2, $3, $4, $5)
#                 ''', topic_id, instruction_text, instruction_type, options, answer)

#         await conn.close()
#         return JSONResponse(content={"message": "Data saved successfully"}, status_code=200)
#     except Exception as e:
#         # 예외 발생시 데이터베이스 연결 종료 후 예외 발생
#         await conn.close()
#         raise HTTPException(status_code=500, detail=f"Error saving data: {str(e)}")

# 설비에 대해 가장 최근에 작성된 보고서 양식을 가져오기
@router.post("/api/report-form")
async def get_report_form(request: Request, body: SubmittedReportForm):
    infra_name = body.infra
    company_name = body.company_name

    if not infra_name:
        raise HTTPException(status_code=400, detail="Infra name is missing in request body")

    try:
        conn = await postgres_connection.connect_db()

        # Check if the infra_name exists
        infra_id = await conn.fetchval('''
            SELECT infra_id FROM infras WHERE infra_name = $1
        ''', infra_name)
        if not infra_id:
            raise HTTPException(status_code=404, detail=f"Infra with name '{infra_name}' not found")

        # Build the query to get the most recent report_form_id for the given infra_id
        query = '''
            SELECT report_form_id 
            FROM report_forms 
            WHERE infra_id = $1
        '''
        params = [infra_id]

        if company_name:
            query += ' AND company_name = $2'
            params.append(company_name)

        query += ' ORDER BY report_form_id DESC LIMIT 1'

        report_form_id = await conn.fetchval(query, *params)
        if not report_form_id:
            raise HTTPException(status_code=404, detail=f"No report form found for infra '{infra_name}'")

        # Retrieve report form data
        report_form_data = await conn.fetch('''
            SELECT 
                t.topic_form_name, 
                t.image_required, 
                array_agg(
                    json_build_object(
                        'instruction', i.instruction,
                        'instruction_type', i.instruction_type,
                        'options', i.options,
                        'answer', i.answer
                    )
                ) AS instruction_list
            FROM 
                topic_forms t
            JOIN 
                instruction_forms i ON t.topic_form_id = i.topic_form_id
            WHERE 
                t.report_form_id = $1
            GROUP BY 
                t.topic_form_name, t.image_required
        ''', report_form_id)

        if not report_form_data:
            raise HTTPException(status_code=404, detail=f"No report form data found for report form id '{report_form_id}'")

        # Format the response data
        response_data = {
            "infra_name": infra_name,
            "report_form_id": report_form_id,
            "inspection_list": []
        }

        for record in report_form_data:
            inspection = {
                "topic": record["topic_form_name"],
                "instruction_list": [],
                "image_required": record["image_required"]
            }
            for instruction_json in record["instruction_list"]:
                instruction = json.loads(instruction_json)
                instruction_data = {
                    "instruction": instruction["instruction"],
                    "instruction_type": instruction["instruction_type"],
                    "options": instruction["options"],
                    "answer": instruction["answer"]
                }
                inspection["instruction_list"].append(instruction_data)
            response_data["inspection_list"].append(inspection)

        await conn.close()
        return JSONResponse(content=response_data, status_code=200)
    except Exception as e:
        if conn:
            await conn.close()
        raise HTTPException(status_code=500, detail=f"Error retrieving report form: {str(e)}")
    infra_name = body.infra
    company_name = body.company_name

    if not infra_name:
        raise HTTPException(status_code=400, detail="Infra name is missing in request body")

    try:
        conn = await postgres_connection.connect_db()

        # Check if the infra_name exists
        infra_id = await conn.fetchval('''
            SELECT infra_id FROM infras WHERE infra_name = $1
        ''', infra_name)
        if not infra_id:
            raise HTTPException(status_code=404, detail=f"Infra with name '{infra_name}' not found")

        # Build the query to get the most recent report_form_id for the given infra_id
        query = '''
            SELECT report_form_id 
            FROM report_forms 
            WHERE infra_id = $1
        '''
        params = [infra_id]

        if company_name:
            query += ' AND company_name = $2'
            params.append(company_name)

        query += ' ORDER BY report_form_id DESC LIMIT 1'

        report_form_id = await conn.fetchval(query, *params)
        if not report_form_id:
            raise HTTPException(status_code=404, detail=f"No report form found for infra '{infra_name}'")

        # Retrieve report form data
        report_form_data = await conn.fetch('''
            SELECT 
                t.topic_form_name, 
                t.image_required, 
                array_agg(
                    json_build_object(
                        'instruction', i.instruction,
                        'instruction_type', i.instruction_type,
                        'options', i.options,
                        'answer', i.answer
                    )
                ) AS instruction_list
            FROM 
                topic_forms t
            JOIN 
                instruction_forms i ON t.topic_form_id = i.topic_form_id
            WHERE 
                t.report_form_id = $1
            GROUP BY 
                t.topic_form_name, t.image_required
        ''', report_form_id)

        if not report_form_data:
            raise HTTPException(status_code=404, detail=f"No report form data found for report form id '{report_form_id}'")

        # Format the response data
        response_data = {
            "infra_name": infra_name,
            "report_form_id": report_form_id,
            "inspection_list": []
        }
        print(response_data)
        print(report_form_data)
        for record in report_form_data:
            inspection = {
                "topic": record["topic_form_name"],
                "instruction_list": [],
                "image_required": record["image_required"]
            }
            for instruction in record["instruction_list"]:
                instruction_data = {
                    "instruction": instruction["instruction"],
                    "instruction_type": instruction["instruction_type"],
                    "options": instruction["options"],
                    "answer": instruction["answer"]
                }
                inspection["instruction_list"].append(instruction_data)
            response_data["inspection_list"].append(inspection)

        await conn.close()
        return JSONResponse(content=response_data, status_code=200)
    except Exception as e:
        if conn:
            await conn.close()
        raise HTTPException(status_code=500, detail=f"Error retrieving report form: {str(e)}")

# 설비에 대한 모든 보고서 양식을 가져오기
@router.post("/api/report-forms")
async def get_report_forms(request: Request, body: SubmittedReportForm):
    infra_name = body.infra
    company_name = body.company_name

    if not infra_name:
        raise HTTPException(status_code=400, detail="Infra name is missing in request body")

    try:
        conn = await postgres_connection.connect_db()

        # Check if the infra_name exists
        infra_id = await conn.fetchval('''
            SELECT infra_id FROM infras WHERE infra_name = $1
        ''', infra_name)
        if not infra_id:
            raise HTTPException(status_code=404, detail=f"Infra with name '{infra_name}' not found")

        # Build the query to get the report_form_ids for the given infra_id
        query = '''
            SELECT report_form_id FROM report_forms WHERE infra_id = $1
        '''
        params = [infra_id]

        if company_name:
            query += ' AND company_name = $2'
            params.append(company_name)

        report_form_ids = await conn.fetch(query, *params)

        # Format the response data
        response_data = {
            "infra_name": infra_name,
            "report_form_ids": [row['report_form_id'] for row in report_form_ids]
        }

        await conn.close()
        return JSONResponse(content=response_data, status_code=200)
    except Exception as e:
        if conn:
            await conn.close()
        raise HTTPException(status_code=500, detail=f"Error retrieving report form data: {str(e)}")


# 설비에 대한 특정 보고서 양식을 가져오기 - 특정 보고서 번호 기입 - 더 이상 안쓸 듯
@router.post("/api/report-form/deprecated")
async def get_report_form_deprecated(request: Request, infra: str = None, report_form_id: int = None):
    infra_name = infra

    if not infra_name:
        raise HTTPException(status_code=400, detail="Infra name is missing in query parameters")
    try:
        conn = await postgres_connection.connect_db()

        # Check if the infra_name exists
        infra_id = await conn.fetchval('''
            SELECT infra_id FROM infras WHERE infra_name = $1
        ''', infra_name)
        if not infra_id:
            raise HTTPException(status_code=404, detail=f"Infra with name '{infra_name}' not found")

        # Check if the report_form_id exists for the given infra_name
        report_exists = await conn.fetchval('''
            SELECT 1 FROM report_forms WHERE infra_id = $1 AND report_form_id = $2
        ''', infra_id, report_form_id)
        if not report_exists:
            raise HTTPException(status_code=404, detail=f"Report form with id '{report_form_id}' not found for infra '{infra_name}'")

        # Retrieve report form data
        report_form_data = await conn.fetch('''
            SELECT 
                t.topic_form_name, 
                t.image_required, 
                array_agg(
                    json_build_object(
                        'instruction', i.instruction,
                        'instruction_type', i.instruction_type,
                        'options', i.options,
                        'answer', i.answer
                    )
                ) AS instruction_list
            FROM 
                topic_forms t
            JOIN 
                instruction_forms i ON t.topic_form_id = i.topic_form_id
            WHERE 
                t.report_form_id = $1
            GROUP BY 
                t.topic_form_name, t.image_required
        ''', report_form_id)
        print(report_form_data)

        if not report_form_data:
            raise HTTPException(status_code=404, detail=f"No report form data found for report form id '{report_form_id}'")

        # Format the response data
        response_data = {
            "infra_name": infra_name,
            "report_form_id": report_form_id,
            "inspection_list": []
        }
        for record in report_form_data:
            inspection = {
                "topic": record['topic_form_name'],
                "instruction_list": [],
                "image_required": record['image_required']
            }
            for instruction_json in record['instruction_list']:
                instruction = json.loads(instruction_json)
                instruction_data = {
                    "instruction": instruction['instruction'],
                    "instruction_type": instruction['instruction_type'],
                    "options": instruction['options'],
                    "answer": None
                }
                inspection["instruction_list"].append(instruction_data)
            response_data["inspection_list"].append(inspection)



        await conn.close()
        return JSONResponse(content=response_data, status_code=200)
    except Exception as e:
        await conn.close()
        raise HTTPException(status_code=500, detail=f"Error retrieving report form data: {str(e)}")


# 설비에 대한 모든 보고서 양식을 가져오기
@router.post("/api/report-forms/deprecated")
async def get_report_forms_deprecated(request: Request, infra: str):
    infra_name = infra

    if not infra_name:
        raise HTTPException(status_code=400, detail="Infra name is missing in query parameters")

    try:
        conn = await postgres_connection.connect_db()

        # Check if the infra_name exists
        infra_id = await conn.fetchval('''
            SELECT infra_id FROM infras WHERE infra_name = $1
        ''', infra_name)
        if not infra_id:
            raise HTTPException(status_code=404, detail=f"Infra with name '{infra_name}' not found")

        # Retrieve report form ids for the given infra_name
        report_form_ids = await conn.fetch('''
            SELECT report_form_id FROM report_forms WHERE infra_id = $1
        ''', infra_id)

        # Format the response data
        response_data = {
            "infra_name": infra_name,
            "report_form_ids": [row['report_form_id'] for row in report_form_ids]
        }

        await conn.close()
        return JSONResponse(content=response_data, status_code=200)
    except Exception as e:
        await conn.close()
        raise HTTPException(status_code=500, detail=f"Error retrieving report form data: {str(e)}")
