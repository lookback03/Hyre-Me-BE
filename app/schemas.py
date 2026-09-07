from pydantic import BaseModel, EmailStr, Field, constr
from typing import Optional, List
from datetime import datetime, date

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    name: Optional[constr(min_length=1)] = None
    password: Optional[constr(min_length=1)] = None


class UserDeleteRequest(BaseModel):
    password: constr(min_length=1) = Field(
        ...,
        description="회원 탈퇴를 확인하기 위한 현재 비밀번호입니다.",
        examples=["현재 비밀번호"],
    )


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user_id: int
    name: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class PortfolioProfileBase(BaseModel):
    education: Optional[str] = None
    gpa: Optional[str] = None
    core_skills_text: Optional[str] = None
    self_intro_keywords: Optional[str] = None


class PortfolioProfileUpsert(PortfolioProfileBase):
    pass


class PortfolioProfileResponse(PortfolioProfileBase):
    id: int
    user_id: int
    resume_file_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PortfolioExperienceBase(BaseModel):
    category: str
    title: str
    organization: Optional[str] = None
    period_text: Optional[str] = None
    role: Optional[str] = None
    tech_stack: Optional[str] = None
    description: Optional[str] = None
    achievement: Optional[str] = None
    learned: Optional[str] = None
    related_skills: Optional[str] = None
    sort_order: Optional[int] = 0


class PortfolioExperienceCreate(PortfolioExperienceBase):
    pass


class PortfolioExperienceUpdate(BaseModel):
    category: Optional[str] = None
    title: Optional[str] = None
    organization: Optional[str] = None
    period_text: Optional[str] = None
    role: Optional[str] = None
    tech_stack: Optional[str] = None
    description: Optional[str] = None
    achievement: Optional[str] = None
    learned: Optional[str] = None
    related_skills: Optional[str] = None
    sort_order: Optional[int] = None


class PortfolioExperienceResponse(PortfolioExperienceBase):
    id: int
    user_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PortfolioCertificationBase(BaseModel):
    name: str
    issuer: Optional[str] = None
    acquired_date: Optional[date] = None
    description: Optional[str] = None


class PortfolioCertificationCreate(PortfolioCertificationBase):
    pass


class PortfolioCertificationUpdate(BaseModel):
    name: Optional[str] = None
    issuer: Optional[str] = None
    acquired_date: Optional[date] = None
    description: Optional[str] = None


class PortfolioCertificationResponse(PortfolioCertificationBase):
    id: int
    user_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PortfolioLanguageBase(BaseModel):
    test_name: str
    score: Optional[str] = None
    grade: Optional[str] = None
    acquired_date: Optional[date] = None
    description: Optional[str] = None


class PortfolioLanguageCreate(PortfolioLanguageBase):
    pass


class PortfolioLanguageUpdate(BaseModel):
    test_name: Optional[str] = None
    score: Optional[str] = None
    grade: Optional[str] = None
    acquired_date: Optional[date] = None
    description: Optional[str] = None


class PortfolioLanguageResponse(PortfolioLanguageBase):
    id: int
    user_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CompanyBase(BaseModel):
    name: str
    role: str
    deadline_text: Optional[str] = None
    job_posting_url: Optional[str] = None
    requirements: Optional[str] = None
    preferences: Optional[str] = None
    core_values: Optional[str] = None


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    deadline_text: Optional[str] = None
    job_posting_url: Optional[str] = None
    requirements: Optional[str] = None
    preferences: Optional[str] = None
    core_values: Optional[str] = None


class CompanyResponse(CompanyBase):
    id: int
    user_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ResumeCompanyOption(BaseModel):
    id: int
    name: str
    role: str
    deadline_text: Optional[str] = None

    class Config:
        from_attributes = True


class GeneratedResumeResponse(BaseModel):
    id: int
    user_id: int
    company_id: int
    title: str
    additional_prompt: Optional[str] = None
    content_markdown: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class GeneratedResumeStatusResponse(BaseModel):
    id: int
    status: Optional[str] = None


class PortfolioSaveRequest(BaseModel):
    profile: PortfolioProfileUpsert
    experiences: List[PortfolioExperienceCreate]
    certifications: List[PortfolioCertificationCreate]
    languages: List[PortfolioLanguageCreate]


class PortfolioSaveResponse(BaseModel):
    profile: PortfolioProfileResponse
    experiences: List[PortfolioExperienceResponse]
    certifications: List[PortfolioCertificationResponse]
    languages: List[PortfolioLanguageResponse]

class GenerateResumeRequest(BaseModel):
    """자소서 생성 및 SSE 스트리밍 생성에 공통으로 사용하는 요청입니다."""

    company_id: int = Field(
        ...,
        description="지원할 목표 기업 ID. 로그인한 사용자 소유의 기업이어야 합니다.",
        examples=[1],
    )
    additional_prompt: Optional[str] = Field(
        default=None,
        description="자소서에 추가로 반영할 요청사항 또는 강조할 항목입니다.",
        examples=["협업 과정에서의 기술적 의사결정을 강조해 주세요."],
    )
    language: Optional[str] = Field(
        default="한국어",
        description="자소서 제목과 본문에 사용할 언어입니다. 작성 포인트와 면접 질문은 한국어입니다.",
        examples=["한국어", "English"],
    )
