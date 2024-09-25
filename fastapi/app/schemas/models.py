from sqlalchemy import Column, Integer, String, BigInteger, ForeignKey, Boolean, ARRAY, Enum, VARCHAR
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import ENUM

Base = declarative_base()

# Enum type 정의
instruction_type_enum = ENUM('check', 'multiple_choice', 'single_choice', 'multiple_select', 'numeric_input', name='instruction_type', create_type=False)

class User(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False)
    company_name = Column(String(255), nullable=False, unique=True)
    wearable_identification = Column(ARRAY(VARCHAR(100)), nullable=True)
    employee_identification_number = Column(BigInteger, nullable=False, unique=True)

class Infra(Base):
    __tablename__ = 'infras'

    infra_id = Column(Integer, primary_key=True, index=True)
    infra_name = Column(String(255), nullable=False)
    company_name = Column(String(255), nullable=False)
    company_name_fk = ForeignKey('users.company_name', ondelete='CASCADE')

class ReportForm(Base):
    __tablename__ = 'report_forms'

    report_form_id = Column(Integer, primary_key=True, index=True)
    infra_id = Column(Integer, ForeignKey('infras.infra_id', ondelete='CASCADE'), nullable=False)
    company_name = Column(String(255), ForeignKey('users.company_name', ondelete='CASCADE'), nullable=False)
    last_modified_time = Column(BigInteger, nullable=True)

class TopicForm(Base):
    __tablename__ = 'topic_forms'

    topic_form_id = Column(Integer, primary_key=True, index=True)
    report_form_id = Column(Integer, ForeignKey('report_forms.report_form_id', ondelete='CASCADE'), nullable=False)
    topic_form_name = Column(String(255), nullable=False)
    image_required = Column(Boolean, nullable=False)

class InstructionForm(Base):
    __tablename__ = 'instruction_forms'

    instruction_form_id = Column(Integer, primary_key=True, index=True)
    topic_form_id = Column(Integer, ForeignKey('topic_forms.topic_form_id', ondelete='CASCADE'), nullable=False)
    instruction = Column(String, nullable=False)
    instruction_type = Column(instruction_type_enum, nullable=False)
    options = Column(ARRAY(VARCHAR(100)), nullable=True)
    answer = Column(ARRAY(VARCHAR(100)), nullable=True)

class PostedReport(Base):
    __tablename__ = 'posted_reports'

    posted_report_id = Column(Integer, primary_key=True, index=True)
    posted_report_path = Column(String(255), nullable=False)
    report_form_id = Column(Integer, ForeignKey('report_forms.report_form_id', ondelete='CASCADE'), nullable=False)
    start_time = Column(BigInteger, nullable=True)
    end_time = Column(BigInteger, nullable=True)
    company_name = Column(String(255), ForeignKey('users.company_name', ondelete='CASCADE'), nullable=False)
    user_name = Column(String(255), nullable=False)

class MediaFile(Base):
    __tablename__ = 'media_files'

    media_id = Column(Integer, primary_key=True, index=True)
    report_form_id = Column(Integer, ForeignKey('report_forms.report_form_id', ondelete='CASCADE'), nullable=True)
    # topic_form_id = Column(Integer, ForeignKey('topic_forms.topic_form_id', ondelete='CASCADE'), nullable=True)
    instruction_form_id = Column(Integer, ForeignKey('instruction_forms.instruction_form_id', ondelete='CASCADE'), nullable = True)
    file_type = Column(String(50), nullable=False)
    file_path = Column(String(255), nullable=False)
