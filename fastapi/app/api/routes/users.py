from fastapi import APIRouter
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from schemas.response_body import User as response_user
from schemas.request_body import User as request_user
from schemas.request_body import WearableIdentifier, Company, Infra

from typing import List
import qrcode  # QR 코드를 생성하기 위한 라이브러리
import io  # QR 코드를 메모리에 저장하기 위한 라이브러리
import json
import base64  # QR 코드를 인코딩하기 위한 라이브러리
import os

from sqlalchemy.ext.asyncio import AsyncSession
from db.postgres_connection import connect_db
from sqlalchemy import func, select, update
from schemas.models import User as UserModel
from janus_client import JanusSession, JanusVideoRoomPlugin

router = APIRouter()

# 더미 사용자 생성
@router.post("/api/user", summary="더미 사용자 생성", description="데이터베이스에 새로운 더미 사용자(HCI_LAB)를 생성합니다.")
async def make_dummy_company(db: AsyncSession = Depends(connect_db)):
    company_name = "HCI_LAB"
    email = "HCI_LAB@gmail.com"
    employee_identification_number = 123

    new_user = UserModel(
        company_name=company_name,
        email=email,
        employee_identification_number=employee_identification_number
    )

    try:
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return JSONResponse(content={"message": "Data saved successfully"}, status_code=200)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error saving data: {str(e)}")


# DB에 있는 모든 유저 정보 돌려주기
@router.post("/api/users", response_model=List[response_user], summary="모든 사용자 정보 조회", description="데이터베이스에 있는 모든 사용자 정보를 반환합니다.")
async def get_all_users(db: AsyncSession = Depends(connect_db)):
    try:
        result = await db.execute(select(UserModel))
        users = result.scalars().all()
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching users: {str(e)}")


# qr code 생성 함수
def generate_qr_code(data: str) -> io.BytesIO:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill='black', back_color='white')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf


# 웹에서 호출하면 QR코드 화면 호스팅
@router.post("/api/wearable-qr-image", summary="QR 코드 생성(AND)", description="회사 이름을 포함한 QR 코드를 생성하여 이미지를 반환합니다.")
async def get_qr_image_for_registering(body: request_user):
    company_name = body.company_name
    if not company_name:
        raise HTTPException(status_code=400, detail="company name is required")

    try:
        qr_data = {"company_name": company_name}
        qr_image = generate_qr_code(qr_data)

        return StreamingResponse(qr_image, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating QR code: {str(e)}")


# (로그인 한 사용자가) infra를 입력하면 infra에 해당하는 보고서 양식을 가져갈 수 있도록 QR 이미지 호스팅
@router.post("/api/infra-qr-image", summary="설비 QR 코드 생성(AND)", description="설비와 회사 이름을 포함한 QR 코드를 생성하여 이미지를 반환합니다.")
async def get_qr_image_for_registrate_infra(body: Infra):
    company_name = body.company_name
    infra = body.infra_name

    if not infra:
        raise HTTPException(status_code=400, detail="Infra name is missing in request body")
    if not company_name:
        raise HTTPException(status_code=400, detail="Company name is missing in request body")

    try:
        qr_data = {"company_name": company_name, "infra_name": infra}
        qr_image = generate_qr_code(json.dumps(qr_data))

        return StreamingResponse(qr_image, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating QR code: {str(e)}")


# 회사가 가지고 있는 모든 안드로이드 기기의 list 반환
@router.post("/api/wearable-machine-lists", summary="회사 안드로이드 기기 목록 조회(AND)", description="회사 이름을 기준으로 안드로이드 기기 목록을 반환합니다.")
async def get_wearable_machine_lists(body: Company, db: AsyncSession = Depends(connect_db)):
    try:
        query = select(UserModel.wearable_identification).where(UserModel.company_name == body.company_name)
        result = await db.execute(query)
        wearable_identification = result.scalar()

        # 회사가 없을 때, 에러 메세지 확인
        if not wearable_identification:
            raise HTTPException(status_code=404, detail="Wearable identification not found in company")

        return {"wearable_identifications": wearable_identification}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error occurred: {str(e)}")


# 특정 Android UUID가 존재하는지 확인
@router.get("/api/wearable-machine-check/{android_UUID}", summary="안드로이드 기기 확인(AND)", description="특정 Android UUID가 존재하는지 확인하고, 존재할 경우 관련된 회사 이름을 반환합니다.")
async def get_wearable_machine_check(android_UUID: str, db: AsyncSession = Depends(connect_db)):
    try:
        query = select(UserModel.company_name).where(
            func.array_position(UserModel.wearable_identification, android_UUID) != None
        )
        result = await db.execute(query)
        company_name = result.scalar()

        if company_name is None:
            return {"result": False, "company_name": None}
        else:
            return {"result": True, "company_name": company_name}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error occurred: {str(e)}")


# Janus API 연동
async def get_janus():
    base_url = os.environ['JANUS_ENDPOINT']
    session = JanusSession(base_url=base_url)
    plugin_handle = JanusVideoRoomPlugin()
    await plugin_handle.attach(session=session)
    try:
        yield plugin_handle
    finally:
        await plugin_handle.destroy()
        await session.destroy()


# 특정 회사에 기기 등록 및 Janus 방 생성
@router.post("/api/registrate-machine-to-company", summary="기기 등록 및 Janus 방 생성(AND)", description="특정 회사에 기기를 등록하고 Janus 방을 생성합니다.")
async def registrate_machine_to_company(
    wearable_identifier: WearableIdentifier, 
    plugin_handle: JanusVideoRoomPlugin = Depends(get_janus),
    db: AsyncSession = Depends(connect_db)
):
    try:
        wearable_identification = wearable_identifier.wearable_identification
        company_name = wearable_identifier.company_name

        # Update wearable_identification 배열에 새로운 ID 추가
        stmt = (
            update(UserModel)
            .where(UserModel.company_name == company_name)
            .values(wearable_identification= func.array_append(UserModel.wearable_identification, wearable_identification))
        )
        await db.execute(stmt)
        # result = await db.execute(stmt)
        await db.commit()

        
        # Janus 방 생성
        room_config = {
            "description": f"Room for {company_name}",
            "is_private": False,
            "publishers": 6,
            "bitrate": 128000,
            "audiocodec": "opus",
            "videocodec": "vp8"
        }

        room_id = company_name + "_" + wearable_identification      
        print(room_id)  
        create_response = await plugin_handle.create_room(
            room_id=room_id,
            configuration=room_config
        )

        return {"result": True, "create_response": create_response}

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error occurred: {str(e)}")
