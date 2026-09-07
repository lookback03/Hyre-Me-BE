import os
import json
import mimetypes
from datetime import datetime, date
from typing import Iterator
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# 클라이언트 초기화
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# .env에서 모델 이름 추출 (.env에 없을 경우 기본값으로 'gemini-2.5-flash' 사용)
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")

PORTFOLIO_RESPONSE_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    required=["experiences", "certifications", "languages"],
    properties={
        "experiences": types.Schema(
            type=types.Type.ARRAY,
            items=types.Schema(
                type=types.Type.OBJECT,
                required=["category", "title"],
                properties={
                    "category": types.Schema(type=types.Type.STRING),
                    "title": types.Schema(type=types.Type.STRING),
                    "organization": types.Schema(type=types.Type.STRING),
                    "period_text": types.Schema(type=types.Type.STRING),
                    "role": types.Schema(type=types.Type.STRING),
                    "tech_stack": types.Schema(type=types.Type.STRING),
                    "description": types.Schema(type=types.Type.STRING),
                    "achievement": types.Schema(type=types.Type.STRING),
                    "learned": types.Schema(type=types.Type.STRING),
                    "related_skills": types.Schema(type=types.Type.STRING),
                },
            ),
        ),
        "certifications": types.Schema(
            type=types.Type.ARRAY,
            items=types.Schema(
                type=types.Type.OBJECT,
                required=["name"],
                properties={
                    "name": types.Schema(type=types.Type.STRING),
                    "issuer": types.Schema(type=types.Type.STRING),
                    "acquired_date": types.Schema(type=types.Type.STRING),
                    "description": types.Schema(type=types.Type.STRING),
                },
            ),
        ),
        "languages": types.Schema(
            type=types.Type.ARRAY,
            items=types.Schema(
                type=types.Type.OBJECT,
                required=["test_name"],
                properties={
                    "test_name": types.Schema(type=types.Type.STRING),
                    "score": types.Schema(type=types.Type.STRING),
                    "grade": types.Schema(type=types.Type.STRING),
                    "acquired_date": types.Schema(type=types.Type.STRING),
                    "description": types.Schema(type=types.Type.STRING),
                },
            ),
        ),
    },
)

PORTFOLIO_SYSTEM_INSTRUCTION = """
# 지시 사항

- 첨부된 이력서, resume, 포트폴리오 파일에서 경험, 자격증, 어학 성적을 구조화된 JSON으로 추출한다.
- 출력은 반드시 JSON만 반환하고, 설명 문장, 마크다운, 코드 블록은 포함하지 않는다.
- 응답 내용은 한국어 기준으로 작성하되, 시험명, 기술명, 기관명처럼 원문 표기가 자연스러운 값은 원문을 유지할 수 있다.
- 경험, 자격증, 어학 성적을 찾지 못하면 해당 배열은 빈 배열([])로 반환한다.
- 추측으로 채우지 말고 문서에서 확인되는 정보만 사용한다.

## 출력 의미

### experiences
- 한 개의 경험 항목을 하나의 객체로 표현한다.
- category: "프로젝트", "인턴", "경력", "동아리" 중 하나로 분류한다.
- title: 경험 제목으로, 필수 값이다.
- organization: 소속 기관명이나 팀명이다. 문서에 없으면 null로 둔다.
- period_text: 기간을 사람이 읽을 수 있는 문자열로 적는다. 예: 2023.01 ~ 2023.06.
- role: 맡은 역할이나 직책이다.
- tech_stack: 사용한 기술, 도구, 언어, 프레임워크를 적는다.
- description: 수행 내용의 핵심 요약이다.
- achievement: 성과, 수치, 개선 결과를 요약한다.
- learned: 경험을 통해 배운 점을 적는다.
- related_skills: 이 경험으로 드러난 역량 키워드를 적는다.

### certifications
- 한 개의 자격증을 하나의 객체로 표현한다.
- name: 자격증 이름으로, 필수 값이다.
- issuer: 발급 기관명이다.
- acquired_date: 취득일을 YYYY-MM-DD 형식으로 적는다. 정확한 날짜를 모르겠으면 null로 둔다.
- description: 자격증에 대한 보충 설명이다. 없으면 null로 둔다.

### languages
- 한 개의 어학 시험 또는 언어 성적을 하나의 객체로 표현한다.
- test_name: 시험명으로, 필수 값이다. 예: TOEIC, TOEFL, OPIC.
- score: 점수나 정량 결과를 적는다. 예: 850.
- grade: 등급이나 레벨을 적는다. 예: AL, IH.
- acquired_date: 취득일을 YYYY-MM-DD 형식으로 적는다. 정확한 날짜를 모르겠으면 null로 둔다.
- description: 성적에 대한 보충 설명이다. 없으면 null로 둔다.

## 날짜 규칙
- 날짜는 가능한 경우 YYYY-MM-DD 형식 문자열로 반환한다.
- 연도만 알면 YYYY, 월까지 알면 YYYY-MM 형식도 허용한다.
- 아예 알 수 없으면 null로 둔다.

## 추가 규칙
- 각 배열의 객체는 문서에 실제로 존재하는 항목만 넣는다.
- 복수 항목이 있으면 중복 없이 각각 분리해서 반환한다.
""".strip()


def _empty_portfolio_result() -> dict:
    return {"experiences": [], "certifications": [], "languages": []}


def _guess_mime_type(file_path: str) -> str:
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type:
        return mime_type

    extension = os.path.splitext(file_path)[1].lower()
    fallback_mime_types = {
        ".pdf": "application/pdf",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
        ".txt": "text/plain",
    }
    return fallback_mime_types.get(extension, "application/octet-stream")

def extract_portfolio_data_with_ai(file_path: str) -> dict:
    """
    저장된 이력서 파일을 구글 Gemini API에 전송하여 JSON 형태로 포트폴리오 데이터를 추출
    """
    uploaded_file = None
    try:
        # 1. 파일을 Gemini 서버에 업로드
        print(f"Uploading {file_path} to Gemini...")
        mime_type = _guess_mime_type(file_path)
        with open(file_path, "rb") as file_obj:
            uploaded_file = client.files.upload(
                file=file_obj,
                config=types.UploadFileConfig(mime_type=mime_type),
            )

        # 환경변수에서 읽어온 모델 확인용 출력
        print(f"Using AI Model: {GEMINI_MODEL_NAME}")

        # 2. 시스템 지시와 구조화 출력 스키마를 함께 적용
        response = client.models.generate_content(
            model=GEMINI_MODEL_NAME,
            contents=[uploaded_file],
            config=types.GenerateContentConfig(
                temperature=0.2,
                response_mime_type="application/json",
                response_schema=PORTFOLIO_RESPONSE_SCHEMA,
                system_instruction=[
                    types.Part.from_text(text=PORTFOLIO_SYSTEM_INSTRUCTION),
                ],
            ),
        )
        
        # 3. 응답받은 텍스트를 파이썬 딕셔너리로 변환하여 반환
        result_dict = json.loads(response.text)
        return result_dict

    except Exception as e:
        print(f"AI Extraction Error: {e}")
        # 에러 발생 시 빈 데이터 반환
        return _empty_portfolio_result()

    finally:
        if uploaded_file is not None:
            try:
                client.files.delete(name=uploaded_file.name)
            except Exception as delete_error:
                print(f"Failed to delete uploaded file: {delete_error}")

# AI 응답이 반드시 지켜야 할 정확한 JSON 스키마(규격) 정의
RESUME_RESPONSE_SCHEMA = types.Schema(
    type=types.Type.OBJECT,
    required=["title", "content_markdown", "reasoning", "enhanced_keywords", "interview_questions"],
    properties={
        "title": types.Schema(type=types.Type.STRING, description="자기소개서의 간략한 제목 (15자를 넘기지 않게, 회사명 반드시 포함)"),
        "content_markdown": types.Schema(type=types.Type.STRING, description="마크다운 형식으로 작성된 자기소개서 본문"),
        "reasoning": types.Schema(type=types.Type.STRING, description="사용자의 TMI와 스펙을 바탕으로 왜 이렇게 자소서를 작성했는지에 대한 설명"),
        "enhanced_keywords": types.Schema(
            type=types.Type.ARRAY, 
            items=types.Schema(type=types.Type.STRING),
            description="기업의 인재상을 바탕으로 자소서에 의도적으로 강조한 3가지 핵심 키워드"
        ),
        "interview_questions": types.Schema(
            type=types.Type.ARRAY, 
            items=types.Schema(type=types.Type.STRING),
            description="이 자소서를 읽은 면접관이 할 법한 2개의 예상 꼬리 질문"
        ),
    },
)

class _DateTimeEncoder(json.JSONEncoder):
    """경험 데이터에 포함될 수 있는 날짜/시간을 JSON으로 변환합니다."""

    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)


def _normalise_resume_inputs(
    profile_data: dict,
    experiences: list,
    company_data: dict,
) -> tuple[dict, list, dict]:
    """AI 프롬프트에 넣을 입력값의 최소 타입을 보장합니다."""
    if not isinstance(profile_data, dict):
        profile_data = {}
    if not isinstance(company_data, dict):
        company_data = {}
    if not isinstance(experiences, list):
        experiences = []

    return profile_data, experiences, company_data


def _build_resume_prompt(
    profile_data: dict,
    experiences: list,
    company_data: dict,
    additional_prompt: str = "",
    language: str = "한국어",
) -> str:
    """동기식/스트리밍 생성에서 공통으로 사용하는 Gemini 프롬프트를 만듭니다."""
    profile_data, experiences, company_data = _normalise_resume_inputs(
        profile_data, experiences, company_data
    )

    # 경험 데이터는 ORM에서 온 날짜 객체를 포함할 수 있으므로 별도 인코더를 사용합니다.
    try:
        experiences_json = json.dumps(
            experiences,
            ensure_ascii=False,
            cls=_DateTimeEncoder,
        )
    except Exception as e:
        print(f"경험 데이터 JSON 변환 실패: {e}")
        experiences_json = "[]"

    return f"""
    당신은 삼성, 네이버, 카카오 등 국내 대기업과 글로벌 Big Tech 기업 채용을 총괄하는 10년 차 IT 전문 기술 취업 컨설턴트입니다.
    제공된 [사용자 스펙 및 경험]과 [타겟 기업 정보]를 정밀 분석하여, 서류 전형을 무조건 통과할 수 있는 수준의 정제되고 완성도 높은 자기소개서를 마크다운 형식으로 작성해주세요.

    [작성 및 구조화 원칙]
    1. 다음 5가지 항목을 지정된 순서대로 모두 포함하여 하나의 완벽한 에세이 형태로 구성하세요:
       - 지원동기: 타겟 기업의 기술적 방향성/비즈니스 트렌드와 자신의 커리어 로드맵 및 기술적 관심사를 유기적으로 결합하여 서술
       - 개인 장점: 프로젝트 실무 경험에서 발휘된 핵심 엔지니어링 역량, 문제 해결 능력 및 협업 시의 기술적 기여도 서술
       - 업무계획: 입사 후 해당 직무에서 클라우드 인프라 아키텍처 아웃풋 향상 및 소프트웨어 안정성을 위해 기여할 구체적 액션 플랜 제시
       - 개인단점: 직무 수행에 치명적이지 않은 인간적/기술적 단점을 솔직히 명시하되, 이를 극복하기 위해 현재 수행 중인 구체적인 노력과 행동 서술
       - 마무리: 지원 직무와 기업의 핵심 인재상에 부합하는 확고한 기술적 다짐과 장기적인 성장 포부를 임팩트 있게 서술

    [레이아웃]
       - 각 문단은 소제목 없이 자연스럽게 이어지도록 작성합니다. 각 문단과 문단 사이는 오직 '줄바꿈(빈 줄)'으로만 구분하세요. 
       - 인사담당자가 읽을 때 문맥적 전환만으로 내용이 자연스럽게 이어지는 하나의 유기적인 서술형 에세이(자소서) 형태로 작성해야 합니다.

    2. 분량 조건: 전체 분량은 공백을 포함하여 **총 1500자 내외**가 되도록 각 항목의 분량을 균형 있게 분배하여 밀도 있게 작성하세요.
    3. 가독성 및 UI 규칙: 본문(content_markdown) 작성 시 중간에 큼직한 제목(#, ##, ### 등의 마크다운 헤더)이나 문장형 제목을 절대 사용하지 마세요.
    4. 톤앤매너: 모든 항목에서 이모티콘이나 이모지를 절대 사용하지 말고, 비즈니스 환경에 적합한 신뢰감 있고 담백한 프로페셔널 구어체 단정문(~했습니다, ~판단하여 빌드했습니다)을 일관되게 사용하세요.
    5. 엔지니어링 뎁스: 단순 나열식 서술은 배제하고, 어떤 기술적 한계 상황(Situation)에서 왜 특정 기술 스택을 선택했고, 어떤 조치(Action)를 취해 어떤 정량적 성과(Result)를 냈는지 STAR 구조에 기반하여 구체적인 수치와 함께 서술하세요.
    6. 다국어 매핑 규칙: 자소서 본문(content_markdown)과 제목(title)은 반드시 문맥상 오타와 어색함이 없도록 완벽한 '{language}'로 작성하세요. 반면 자소서 본문을 제외한 '나머지 모든 항목(reasoning, interview_questions)'은 사용자가 이해할 수 있도록 반드시 '한국어'로 작성해야 합니다.

    [타겟 기업 정보]
    - 기업명: {company_data.get('name', '알 수 없음')}
    - 지원 직무: {company_data.get('role', '알 수 없음')}
    - 요구 사항: {company_data.get('requirements', '')}
    - 핵심 가치/인재상: {company_data.get('core_values', '')}

    [사용자 프로필]
    - 학력: {profile_data.get('education', '')}
    - 핵심 역량: {profile_data.get('core_skills_text', '')}

    [사용자 경험 및 TMI]
    {experiences_json}

    [사용자 요청사항 및 강조항목]
    {additional_prompt}

    반드시 제공된 JSON 스키마 규격에 맞추어 응답해야 합니다.
    """


def _resume_generation_config() -> types.GenerateContentConfig:
    """자소서 생성에 사용하는 구조화 JSON 응답 설정입니다."""
    return types.GenerateContentConfig(
        temperature=0.7,
        response_mime_type="application/json",
        response_schema=RESUME_RESPONSE_SCHEMA,
    )


def parse_resume_response(response_text: str) -> dict:
    """Gemini가 반환한 구조화 JSON 텍스트를 자소서 결과 딕셔너리로 변환합니다.

    스트리밍 경로에서는 마지막 청크를 받은 뒤 한 번만 호출합니다. JSON이
    완성되지 않은 경우 예외를 호출자에게 전달하여 SSE의 ``error`` 이벤트로
    안내할 수 있게 합니다.
    """
    if not response_text.strip():
        raise ValueError("Gemini가 빈 응답을 반환했습니다.")
    result = json.loads(response_text)
    if not isinstance(result, dict):
        raise ValueError("Gemini 응답이 JSON 객체가 아닙니다.")
    return result


def generate_masterpiece_resume(
    profile_data: dict,
    experiences: list,
    company_data: dict,
    additional_prompt: str = "",
    language: str = "한국어",
) -> dict:
    """사용자의 포트폴리오와 목표 기업 정보로 자소서를 완성해 반환합니다.

    기존 동기식 ``POST /api/resumes/generate``가 사용하는 함수입니다. AI
    호출이 실패하면 기존 클라이언트 호환성을 위해 실패 결과를 반환합니다.
    실시간 진행 상황이 필요한 경우 ``stream_masterpiece_resume``를
    사용하세요.
    """
    profile_data, experiences, company_data = _normalise_resume_inputs(
        profile_data, experiences, company_data
    )
    prompt = _build_resume_prompt(
        profile_data=profile_data,
        experiences=experiences,
        company_data=company_data,
        additional_prompt=additional_prompt,
        language=language,
    )

    try:
        print(f"[{company_data.get('name', '자소서')}] 지원을 위한 자소서 생성 중...")
        response = client.models.generate_content(
            model=GEMINI_MODEL_NAME,
            contents=[prompt],
            config=_resume_generation_config(),
        )

        return parse_resume_response(response.text)

    except Exception as e:
        print(f"AI 자소서 생성 중 오류 발생: {e}")
        return {
            "title": "생성 실패",
            "content_markdown": "자소서 생성 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
            "reasoning": str(e),
            "enhanced_keywords": [],
            "interview_questions": [],
        }


def stream_masterpiece_resume(
    profile_data: dict,
    experiences: list,
    company_data: dict,
    additional_prompt: str = "",
    language: str = "한국어",
) -> Iterator[str]:
    """Gemini의 구조화된 JSON 응답 청크를 순서대로 전달합니다.

    ``google-genai``의 동기 ``generate_content_stream``을 사용하므로 이
    함수는 동기 이터레이터입니다. 각 문자열은 완성된 자소서가 아니라
    JSON 응답의 일부일 수 있으며, 호출자는 모두 이어 붙인 뒤
    :func:`parse_resume_response`로 최종 결과를 만들어야 합니다.

    예외를 내부에서 삼키지 않는 이유는 스트리밍 응답이 이미 시작된 뒤에는
    HTTP 상태 코드를 바꿀 수 없기 때문입니다. 라우터가 예외를 받아 SSE
    ``error`` 이벤트로 변환합니다.
    """
    prompt = _build_resume_prompt(
        profile_data=profile_data,
        experiences=experiences,
        company_data=company_data,
        additional_prompt=additional_prompt,
        language=language,
    )

    response_stream = client.models.generate_content_stream(
        model=GEMINI_MODEL_NAME,
        contents=[prompt],
        config=_resume_generation_config(),
    )
    for response in response_stream:
        text = getattr(response, "text", None)
        if text:
            yield text