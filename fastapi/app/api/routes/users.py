from fastapi import APIRouter
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from db import postgres_connection
from schemas import response_body
from typing import List
router = APIRouter()


# 더미 사용자 생성
@router.post("/api/user")
async def make_dummy_user(request: Request):

    # 임시 user_name 0000
    user_name = "0000"
    email = "dummy@dummy.com"

    conn = await postgres_connection.connect_db()

    try:
        await conn.fetch('''
            INSERT INTO users ("user_name", "email")
            VALUES ($1, $2)
        ''', user_name, email
        )
        
        await conn.close()
        return JSONResponse(content={"message": "Data saved successfully"}, status_code=200)
        
    except Exception as e:
        await conn.close()
        raise HTTPException(status_code=500, detail=f"Error saving data: {str(e)}")

# DB에 있는 모든 유저 정보 돌려주기
@router.get("/api/users", response_model=List[response_body.User])
async def login(request: Request):
    conn = await postgres_connection.connect_db()

    try:
        # 모든 유저 정보 조회
        users = await conn.fetch("SELECT user_id, employee_identification_number, user_name, email FROM users")
        await conn.close()

        # 조회된 유저 정보를 리스트로 변환
        user_list = [User(**user) for user in users]

        return user_list
    except Exception as e:
        await conn.close()
        raise HTTPException(status_code=500, detail=f"Error fetching users: {str(e)}")