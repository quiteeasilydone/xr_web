from fastapi import APIRouter
from fastapi import HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse

from schemas.request_body import MediaFileRequest

import os
import io
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from schemas.models import MediaFile as MediaFileModel
from db.postgres_connection import connect_db
from db.minio_connection import minio_client
from sqlalchemy import func
from sqlalchemy.future import select
from sqlalchemy import delete
from schemas.models import User as UserModel
from schemas.models import UserLocation as UserLocationModel
from schemas.request_body import UserLoactionRequest
from schemas.response_body import UserLocationResponse

router = APIRouter()

# 안드로이드에서 위치 정보 받기
@router.post("/api/user/location", summary="유저 위치 정보 업로드(AND)", description="안드로이드에서 사용자의 위치정보 업로드 후, DB에 저장"
             ,responses={
                200: {
                    "description": "사용자 위치 정보 입력/수정 성공.",
                    "content": {
                        "application/json": {
                            "example":{
                                "message": "User Location update successfully"
                            }                          
                        }
                    }
                }
            })
async def submit_user_location(
    body : UserLoactionRequest, db: AsyncSession = Depends(connect_db)
):  
    try:
        print('0000')
        user_result = await db.execute(
            select(UserModel.wearable_identification)
            .where(UserModel.wearable_identification.any(body.android_uuid))
        )


        uuid_result =user_result.scalars().first()

        if not uuid_result:
            raise HTTPException(status_code = 404, detail = "Android uuid not found")
        
        ## 기존 유저 위치 정보 삭제
        print("11111")
        await db.execute(delete(UserLocationModel).where(UserLocationModel.android_uuid == body.android_uuid))

        await db.flush()

        print("222222")
        ## 새로운 위치 정보 업데이트
        new_location = UserLocationModel(
            android_uuid = body.android_uuid,
            company_name = body.company_name,
            latitude = body.latitude,
            longitude = body.longitude
        )

        db.add(new_location)
        await db.commit()

        return {"message" : "User Location update successfully"}
 

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving media: {str(e)}")
    

@router.get("/api/user/location", summary="유저 위치 정보 조회", description="안드로이드에서 전송한 위치정보를 WEB에서 조회"
            ,response_model = UserLocationResponse)
async def get_user_location(
    android_uuid: str,
    company_name: str,
    db: AsyncSession = Depends(connect_db)
):
    try:
        user_location_result = await db.execute(
            select(UserLocationModel).where(
                UserLocationModel.android_uuid == android_uuid,
                UserLocationModel.company_name == company_name
            )
        )

        user_location = user_location_result.scalars().first()

        if not user_location:
            raise HTTPException(status_code = 404, detail = "User Info not found")
        

        response_data = {
                "android_uuid": user_location.android_uuid,
                "company_name": user_location.company_name,
                "latitude": user_location.latitude,
                "longitude": user_location.longitude
        }

        return JSONResponse(content = response_data, status_code = 200)
    
    except Exception as e:
        raise HTTPException(status_code = 500, detail = f"Error retrieving report form: {str(e)}")