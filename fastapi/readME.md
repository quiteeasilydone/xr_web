# 디렉토리 구조

- db
    - init.sql : 데이터베이스 초기 실행시 적용할 DDL


- fastapi/app
    - api/routes : 엔드포인트별로 파일 구분
        - endpoints:
            - infras.py
            - login.py
            - reports.py
            - posted_reports.py
            - users.py
            - whiteboard.py
    - core: 공통 파일 config.py, security.py, celery_app.py : 현재 사용하지 않음
    - db: 데이터베이스 관련 파일
        - init.sql : 데이터베이스 초기 실행시 적용할 DDL
        - minio_connection.py : MinIO storage와 연결을 맺는 객체 생성
        - postgres_connection.py : postgresDB와 연결을 맺는 객체 생성
    - models: 데이터베이스 테이블과 매칭되는 모델 ex.. item.py, user.py : 현재 사용하지 않음
    - schemas: 데이터 전송 객체 스키마, 스프링의 DTO와 비슷
        - request_body.py : api request에 담아서 받을 데이터 형식
        - response_body.py : api response에 담아서 보낼 데이터 형식

- Dockerfile : 컨테이너 빌드 세부사항을 정의. requirements.txt에 기입된 install list를 참고하여 pip library들을 컨테이너에 설치