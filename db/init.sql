CREATE TYPE instruction_type AS ENUM ('check', 'multiple_choice', 'single_choice', 'multiple_select', 'numeric_input');

CREATE TABLE reports (
    report_id SERIAL PRIMARY KEY,
    infra VARCHAR(255) NOT NULL,
    start_time BIGINT, -- 유닉스 타임스탬프로 작성 시작 시간 
    end_time BIGINT, -- 유닉스 타임스탬프로 작성 완료 시간 
    client_id VARCHAR(255) NOT NULL -- 작성자의 이름 또는 아이디(아이디를 만드는것이 좋을것 같음)
);

CREATE TABLE topics (
    topic_id SERIAL PRIMARY KEY,
    report_id INT NOT NULL,
    topic_name VARCHAR(255) NOT NULL,
    image_required BOOLEAN NOT NULL,
    -- postgres 배열 타입: 원소가 instruction_id - 추가 나중에 쿼리 날려서 instruction 찾을 때 이거 사용,
    -- 위의 거가 과연 필요한가? 어차피 topic을 찾는다 해도 infra_id로 찾기 시작할거라 필요 없을 듯
    FOREIGN KEY (report_id) REFERENCES reports(report_id) ON DELETE CASCADE
);

CREATE TABLE instructions (
    instruction_id SERIAL PRIMARY KEY,
    topic_id INT NOT NULL,
    instruction TEXT NOT NULL,
    instruction_type instruction_type NOT NULL,
    options VARCHAR(100)[], -- 문자열로 옵션 저장 ('multiple_choice', 'single_choice', 'multiple_select' 의 경우)
    answer VARCHAR(100)[], -- 응답 정보 저장 - 바차배열쓰기
    FOREIGN KEY (topic_id) REFERENCES topics(topic_id) ON DELETE CASCADE
);

CREATE TABLE media_files (
    media_id SERIAL PRIMARY KEY,
    report_id INT,
    topic_id INT,
    file_type VARCHAR(50) NOT NULL CHECK (file_type IN ('audio', 'image')),
    file_path VARCHAR(255) NOT NULL,
    FOREIGN KEY (report_id) REFERENCES reports(report_id) ON DELETE CASCADE,
    FOREIGN KEY (topic_id) REFERENCES topics(topic_id) ON DELETE CASCADE
);