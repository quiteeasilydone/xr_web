# 디렉토리 구조

fastapi/app

- api : 엔드포인트별로 파일 구분
    - endpoints: items.py, login.py, users.py, utils.py
- core: 공통 파일 config.py, security.py, celery_app.py
- crud: 기본 get, create, update, remove base.py, crud_item.py, crud_user.py
- db: 데이터베이스 관련 파일 base.py, base_class.py, init_db.py, session.py
- models: 데이터베이스 테이블과 매칭되는 모델 item.py, user.py
- schemas: 스프링의 DTO와 비슷 item.py, user.py, msg.py, token.py
- tests: 테스트 파일