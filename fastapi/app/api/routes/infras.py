from fastapi import APIRouter
from fastapi.responses import JSONResponse
from fastapi import FastAPI, Request, HTTPException, Depends
from schemas.request_body import Infra
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from schemas.models import Infra as InfraModel
from db.postgres_connection import connect_db
from sqlalchemy.future import select

from schemas.response_body import InfraBase, InfrasResponseModel

router = APIRouter()

# 전체 설비 목록 가져오기
@router.get("/api/infras", summary="설비 목록 조회", description="회사 이름을 입력하여 해당 회사에 등록된 모든 설비 목록을 가져옵니다."
            ,response_model = InfrasResponseModel)
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
@router.post("/api/infra", summary="설비 추가", description="새로운 설비를 추가합니다. 중복된 설비 이름이 존재하면 에러를 반환합니다."
             ,responses={
                200: {
                    "description": "설비 추가 성공.",
                    "content": {
                        "application/json": {
                            "example":{
                                "message": "Infra added successfully"
                            }                          
                        }
                    }
                }
            })
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
            select(InfraModel.infra_id).where(
                InfraModel.infra_name == infra_name, InfraModel.company_name == company_name
                )
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
