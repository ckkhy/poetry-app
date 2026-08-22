# 고전시가 종합 분석 & AI 시각화

향가 · 고려가요 · 시조 · 가사 25편의 원문/현대어 풀이를 내장하고, GPT로 공간 구도(원경·중경·근경)와
표현 기법을 분석한 뒤 DALL·E 3로 수묵산수화를 자동 생성하는 Streamlit 웹앱입니다.

## 파일 구성
- `app.py` — 앱 전체 소스 코드 (단일 파일)
- `requirements.txt` — 의존 패키지 목록

## 로컬 실행
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Community Cloud 배포
1. 이 두 파일을 GitHub 저장소에 업로드합니다 (`app.py`, `requirements.txt`).
2. https://share.streamlit.io 에서 저장소를 연결하고 `app.py`를 메인 파일로 지정해 배포합니다.
3. 배포된 앱의 **Settings → Secrets** 메뉴에 아래 내용을 추가합니다.
   ```toml
   OPENAI_API_KEY = "sk-여기에_발급받은_키_입력"
   ```
4. 저장 후 앱을 재시작(Reboot)하면 실제 GPT/DALL·E 3 분석·이미지 생성이 활성화됩니다.

## API 키가 없을 때
`OPENAI_API_KEY`가 설정되어 있지 않거나 API 호출 중 오류(rate limit, 네트워크 오류 등)가 발생해도
앱이 멈추지 않고 **시뮬레이션 모드**로 자동 전환되어, 규칙 기반 예시 분석과 PIL로 생성한
수묵산수화 풍 placeholder 이미지를 대신 보여줍니다. 화면 상단/카드에 시뮬레이션 여부가 명확히 표시됩니다.

## 주요 기능
- 사이드바 실시간 검색(제목/원문/현대어풀이/키워드) + 갈래(향가·고려가요·시조·가사) 필터
- 좌: 원문·현대어 풀이·작품 개관 / 우: AI 분석(공간 구도, 표현 기법, 정서·주제) + 생성 이미지
- GPT `response_format=json_object`로 구조화된 분석 결과 추출 → DALL·E 3 영문 프롬프트 자동 생성
- 분석 모델(gpt-4o / gpt-4o-mini), 이미지 품질·스타일을 사이드바에서 조정 가능
- 결과는 세션 상태에 캐시되어 같은 작품 재조회 시 즉시 표시, "다시 분석하기"로 재생성 가능
