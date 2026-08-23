# -*- coding: utf-8 -*-
"""
고전시가 종합 분석 & AI 시각화 웹 애플리케이션
================================================
- 향가 / 고려가요 / 시조 / 가사 25편 내장 데이터베이스
- 사이드바 실시간 검색 및 갈래 필터
- GPT 기반 공간 구도(원경·중경·근경) 및 표현 기법 분석 (JSON 응답)
- 분석 결과 기반 DALL·E 3 수묵산수화 프롬프트 자동 생성 및 이미지 렌더링
- st.secrets 기반 API 키 처리 + 시뮬레이션 모드(예외 발생 시 자동 대체)

Streamlit Community Cloud 배포용으로 작성되었습니다.
"""

import json
import textwrap
from datetime import datetime

import streamlit as st

try:
    from openai import OpenAI
except ImportError:  # openai 패키지가 없는 극단적 상황에도 앱이 죽지 않도록 처리
    OpenAI = None

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = None


# ============================================================================
# 0. 페이지 기본 설정
# ============================================================================
st.set_page_config(
    page_title="고전시가 종합 분석 & AI 시각화",
    page_icon="🖋️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .main .block-container {padding-top: 2rem; padding-bottom: 3rem;}
    .poem-box {
        background-color: #FBF8F2;
        border: 1px solid #E4DCC8;
        border-left: 5px solid #8B5E34;
        border-radius: 8px;
        padding: 1.1rem 1.3rem;
        font-size: 1.02rem;
        line-height: 2.0;
        white-space: pre-wrap;
        margin-bottom: 0.8rem;
        color: #2B2620;
    }
    .poem-box.modern {
        border-left: 5px solid #4A7A6B;
        background-color: #F5FAF8;
    }
    .tag-badge {
        display: inline-block;
        background-color: #EFE7D8;
        color: #6B4A2A;
        border-radius: 999px;
        padding: 0.15rem 0.75rem;
        font-size: 0.80rem;
        margin-right: 0.4rem;
        margin-bottom: 0.3rem;
        border: 1px solid #DDCBA8;
    }
    .spatial-card {
        border: 1px solid #DCE4E0;
        border-radius: 10px;
        padding: 0.9rem;
        background: linear-gradient(180deg, #FAFBFA 0%, #F1F5F3 100%);
        margin-bottom: 0.6rem;
    }
    .spatial-title {
        font-weight: 700;
        color: #3D5C50;
        font-size: 0.95rem;
        margin-bottom: 0.25rem;
    }
    .technique-card {
        border-left: 4px solid #B0763F;
        background-color: #FFF9F0;
        border-radius: 6px;
        padding: 0.6rem 0.9rem;
        margin-bottom: 0.5rem;
    }
    .sim-banner {
        background-color: #FFF3CD;
        border: 1px solid #FFE69C;
        color: #7A5B00;
        padding: 0.6rem 1rem;
        border-radius: 8px;
        font-size: 0.88rem;
        margin-bottom: 0.8rem;
    }
    div.stButton > button {
        border-radius: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================================
# 1. 내장 데이터베이스 — 고전시가 25편 (향가 5 / 고려가요 5 / 시조 11 / 가사 4)
# ============================================================================
POEMS_DB = {
    # ------------------------------------------------------------------ 향가
    "서동요": {
        "genre": "향가", "author": "서동(무왕)", "period": "삼국(백제)",
        "original": "善化公主主隱\n他密只嫁良置古\n薯童房乙\n夜矣卯乙抱遣去如",
        "modern": "선화공주님은\n남몰래 결혼하고서\n서동 도련님을\n밤에 몰래 안고 간다.",
        "theme": "삼국유사에 전하는 4구체 향가로, 서동이 선화공주와 혼인하기 위해 지어 아이들에게 부르게 한 참요(讖謠) 성격의 노래이다. 소박하고 직설적인 어법으로 남녀의 애정을 노래했다.",
        "keywords": ["서동", "선화공주", "삼국유사", "참요", "4구체"],
    },
    "제망매가": {
        "genre": "향가", "author": "월명사", "period": "신라 경덕왕",
        "original": "生死路隱 此矣有阿米次肸伊遣\n吾隱去內如辭叱都 毛如云遣去內尼叱古\n於內秋察早隱風未 此矣彼矣浮良落尸葉如\n一等隱枝良出古 去奴隱處毛冬乎丁\n阿也彌陀刹良逢乎吾 道修良待是古如",
        "modern": "삶과 죽음의 길은\n여기 있으매 두려워지고\n'나는 간다'는 말도\n다 이르지 못하고 가버렸는가.\n어느 가을 이른 바람에\n여기저기 떨어지는 잎처럼\n한 가지에 나고서도\n가는 곳을 모르는구나.\n아아, 미타찰에서 만날 나는\n도(道) 닦으며 기다리겠노라.",
        "theme": "월명사가 죽은 누이를 추모하며 지은 10구체 향가(추도가). 낙엽의 비유를 통해 죽음의 허무함을 형상화하고, 종교적 승화(미타찰에서의 재회)로 슬픔을 극복하려는 의지를 보여준다.",
        "keywords": ["월명사", "죽음", "낙엽", "미타찰", "추모", "10구체"],
    },
    "찬기파랑가": {
        "genre": "향가", "author": "충담사", "period": "신라 경덕왕",
        "original": "咽嗚爾處米 露曉邪隱月羅理\n白雲音逐于浮去隱安支下 沙是八陵隱汀理也中\n耆郎矣皃史是史藪邪 逸烏川理叱磧惡希\n郎也持以支如賜烏隱 心未際叱肹逐內良齊\n阿耶栢史叱枝次高支好 雪是毛冬乃乎尸花判也",
        "modern": "흐느끼며 바라보매\n이슬 밝힌 달이\n흰 구름 따라 떠간 언저리에\n모래 가른 물가에\n기파랑의 모습이올시 수풀이여.\n일오내 자갈 벌에서\n낭이 지니시던\n마음의 끝을 따르고 있노라.\n아아, 잣나무 가지가 높아\n서리 모를 그 씩씩한 모습이여.",
        "theme": "화랑 기파랑의 고매한 인품을 자연물(달, 잣나무)에 비유하여 예찬한 10구체 향가. 문답 형식과 상징적 이미지의 절제된 사용이 뛰어나 향가 중 문학성이 가장 높은 작품으로 평가받는다.",
        "keywords": ["충담사", "기파랑", "화랑", "예찬", "잣나무"],
    },
    "헌화가": {
        "genre": "향가", "author": "견우노옹(실명 미상)", "period": "신라 성덕왕",
        "original": "紫布岩乎希 執音乎手母牛放教遣\n吾肹不喩慚肹伊賜等 花肹折叱可獻乎理音如",
        "modern": "자줏빛 바위 가에\n잡고 있던 손의 암소를 놓게 하시고\n나를 부끄러워하지 않으신다면\n꽃을 꺾어 바치오리다.",
        "theme": "수로부인의 아름다움에 반한 한 노인이 벼랑 위의 철쭉꽃을 꺾어 바치며 부른 4구체 향가. 아름다움에 대한 예찬과 헌신의 태도가 소박하게 드러난다.",
        "keywords": ["수로부인", "철쭉", "노옹", "헌신", "4구체"],
    },
    "처용가": {
        "genre": "향가", "author": "처용", "period": "신라 헌강왕",
        "original": "東京明期月良 夜入伊遊行如可\n入良沙寢矣見昆 脚烏伊四是良羅\n二肹隱吾下於叱古 二肹隱誰支下焉古\n本矣吾下是如馬於隱 奪叱良乙何如爲理古",
        "modern": "서울 밝은 달밤에\n밤늦도록 놀고 다니다가\n들어와 잠자리를 보니\n다리가 넷이로구나.\n둘은 내 것이었지만\n둘은 누구의 것인가.\n본디 내 것이지마는\n빼앗긴 것을 어찌하리.",
        "theme": "아내를 범한 역신 앞에서 관용과 체념의 춤을 추어 역신을 감복시켰다는 설화가 전하는 8구체 향가. 무가(巫歌)적 성격을 지니며 고려·조선의 처용무로 계승되었다.",
        "keywords": ["처용", "역신", "관용", "무가", "벽사"],
    },

    # --------------------------------------------------------------- 고려가요
    "청산별곡": {
        "genre": "고려가요", "author": "작자 미상", "period": "고려",
        "original": "살어리 살어리랏다 쳥산(靑山)애 살어리랏다\n멀위랑 ᄃᆞ래랑 먹고 쳥산(靑山)애 살어리랏다\n얄리얄리 얄랑셩 얄라리 얄라\n\n우러라 우러라 새여 자고 니러 우러라 새여\n널라와 시름 한 나도 자고 니러 우니노라\n얄리얄리 얄랑셩 얄라리 얄라",
        "modern": "살겠노라 살겠노라. 청산에 살겠노라.\n머루랑 다래를 먹고 청산에 살겠노라.\n얄리얄리 얄랑셩 얄라리 얄라(후렴)\n\n울어라 울어라 새여, 자고 일어나 울어라 새여.\n너보다 근심이 많은 나도 자고 일어나 울며 지내노라.\n얄리얄리 얄랑셩 얄라리 얄라(후렴)",
        "theme": "삶의 고뇌와 비애를 피해 청산과 바다라는 이상향을 동경하는 고려 속요. 'ㄹ'음 반복의 경쾌한 후렴구와 대조적으로 애상적 정서가 깊이 깔려 있어 현실 도피와 체념의 정서를 형상화한 대표작으로 꼽힌다.",
        "keywords": ["청산", "이상향", "후렴구", "애상", "현실도피"],
    },
    "가시리": {
        "genre": "고려가요", "author": "작자 미상", "period": "고려",
        "original": "가시리 가시리잇고 나ᄂᆞᆫ\nᄇᆞ리고 가시리잇고 나ᄂᆞᆫ\n위 증즐가 太平盛代(태평성대)\n\n날러는 엇디 살라 ᄒᆞ고\nᄇᆞ리고 가시리잇고 나ᄂᆞᆫ\n위 증즐가 太平盛代(태평성대)\n\n잡ᄉᆞ와 두어리마ᄂᆞᆫᄂᆞᆫ\n선ᄒᆞ면 아니 올셰라\n위 증즐가 太平盛代(태평성대)",
        "modern": "가시렵니까 가시렵니까\n(나를) 버리고 가시렵니까\n위 증즐가 태평성대\n\n나더러는 어찌 살라 하고\n버리고 가시렵니까\n위 증즐가 태평성대\n\n붙잡아 두고 싶지마는\n서운하면 아니 올까 두렵습니다\n위 증즐가 태평성대",
        "theme": "임과의 이별을 애절하게 노래한 고려가요로, 이별의 정한(情恨)이라는 한국 문학의 보편적 정서를 대표한다. 소극적·자기희생적 태도로 임을 보내는 화자의 심리가 후대 '가시는 듯 돌아오소서'(정석가) 등과 함께 이별시가의 원류로 평가된다.",
        "keywords": ["이별", "정한", "태평성대", "후렴구", "체념"],
    },
    "서경별곡": {
        "genre": "고려가요", "author": "작자 미상", "period": "고려",
        "original": "셔경(西京)이 아즐가 셔경(西京)이 셔울히마르는\n위 두어렁셩 두어렁셩 다링디리\n닷곤ᄃᆡ 아즐가 닷곤ᄃᆡ 쇼셩경 고ᄋᆡ마른\n위 두어렁셩 두어렁셩 다링디리\n여ᄒᆡ므론 아즐가 여ᄒᆡ므론 질삼뵈 ᄇᆞ리시고\n위 두어렁셩 두어렁셩 다링디리\n괴시란ᄃᆡ 아즐가 괴시란ᄃᆡ 우러곰 좃니노이다\n위 두어렁셩 두어렁셩 다링디리",
        "modern": "서경이, 아즐가, 서경이 서울이지마는\n(후렴) 위 두어렁셩 두어렁셩 다링디리\n새로 닦은, 아즐가, 새로 닦은 소성경을 사랑합니다마는\n(후렴)\n이별할 바에는, 아즐가, 이별할 바에는 (제가 하던) 길쌈 베도 버리고\n(후렴)\n사랑해 주신다면, 아즐가, 사랑해 주신다면 울면서 따르겠습니다\n(후렴)",
        "theme": "서경(평양)을 배경으로 임과의 이별을 거부하는 적극적이고 격정적인 여성 화자의 목소리가 두드러지는 고려가요. '가시리'의 체념적 태도와 달리 사랑을 위해 생업(길쌈)마저 버리겠다는 능동적 정서를 보인다.",
        "keywords": ["서경", "이별", "적극적", "여음구", "길쌈"],
    },
    "동동": {
        "genre": "고려가요", "author": "작자 미상", "period": "고려",
        "original": "덕(德)으란 곰ᄇᆡ예 받ᄌᆞᆸ고 복(福)으란 림ᄇᆡ예 받ᄌᆞᆸ고\n덕(德)이여 복(福)이라 호ᄂᆞᆯ 나ᅀᆞ라 오소이다\n아으 동동(動動)다리\n\n정월(正月)ㅅ 나릿 므른 아으 어져 녹져 ᄒᆞ논ᄃᆡ\n누릿 가온ᄃᆡ 나곤 몸하 ᄒᆞ올로 녈셔\n아으 동동(動動)다리",
        "modern": "덕은 뒷잔에 바치옵고 복은 앞잔에 바치오니\n덕이며 복이라 하는 것을 (임께) 드리러 오십시오\n아으 동동다리(후렴)\n\n정월 냇물은 아으 얼었다가 녹으려 하는데\n세상 가운데 태어난 이 몸은 홀로 살아가는구나\n아으 동동다리(후렴)",
        "theme": "월령체(月令體) 형식으로 정월부터 섣달까지 열두 달의 세시풍속과 자연 경물에 임에 대한 그리움을 결합한 고려가요. 우리 문학사 최초의 월령체 노래로 평가되며, 이별과 연모의 정서가 달마다 반복·변주된다.",
        "keywords": ["월령체", "세시풍속", "그리움", "정월", "후렴"],
    },
    "정석가": {
        "genre": "고려가요", "author": "작자 미상", "period": "고려",
        "original": "딩아 돌하 當今(당금)에 계샹이다\n딩아 돌하 當今(당금)에 계샹이다\n先王聖代(선왕성대)예 노니ᄋᆞ와지이다\n\n삭삭기 셰몰애 별헤 나ᄂᆞᆫ\n삭삭기 셰몰애 별헤 나ᄂᆞᆫ\n구은 밤 닷 되를 심고이다\n그 바미 우미 도다 삭나거시아\n그 바미 우미 도다 삭나거시아\n有德(유덕)ᄒᆞ신 님믈 여ᄒᆡᄋᆞ와지이다",
        "modern": "징이여 돌이여 지금 세상에 계십니다\n징이여 돌이여 지금 세상에 계십니다\n이 태평성대에 노닐고 싶습니다\n\n바삭바삭한 가는 모래 벼랑에\n바삭바삭한 가는 모래 벼랑에\n구운 밤 닷 되를 심습니다\n그 밤이 움이 돋아 싹이 난다면\n그 밤이 움이 돋아 싹이 난다면\n그제서야 유덕하신 임과 이별하겠습니다",
        "theme": "불가능한 상황(구운 밤에서 싹이 남)을 설정하여 임과 영원히 이별하지 않겠다는 역설적 소망을 노래한 고려가요. 불가능한 조건의 설정을 통해 이별을 거부하는 발상이 시조 '이화우 흩날릴 제' 등 후대 시가에도 영향을 주었다.",
        "keywords": ["불가능한 상황", "영원한 사랑", "역설", "태평성대"],
    },

    # --------------------------------------------------------------------- 시조
    "하여가": {
        "genre": "시조", "author": "이방원", "period": "고려 말",
        "original": "이런들 엇더ᄒᆞ며 뎌런들 엇더ᄒᆞ료\n만수산(萬壽山) 드렁츩이 얼거진들 긔 엇더ᄒᆞ리\n우리도 이ᄀᆞᆺ치 얼거져 백년(百年)ᄭᆞ지 누리리라",
        "modern": "이런들 어떠하며 저런들 어떠하리\n만수산의 드렁칡이 얽혀진들 그것이 어떠하리\n우리도 이렇게 얽혀져서 백 년까지 누리리라",
        "theme": "이방원이 정몽주의 마음을 떠보기 위해 지었다는 시조. 고려 왕조에 대한 절의를 굽히고 조선 건국 세력과 함께할 것을 회유하는 내용으로, 정몽주의 '단심가'와 대구를 이루는 문답 시조로 유명하다.",
        "keywords": ["이방원", "정몽주", "회유", "역성혁명", "단심가"],
    },
    "단심가": {
        "genre": "시조", "author": "정몽주", "period": "고려 말",
        "original": "이 몸이 주거주거 일백 번(一百番) 고쳐 주거\n백골(白骨)이 진토(塵土) ᄃᆡ여 넉시라도 잇고 업고\n님 향(向)ᄒᆞᆫ 일편단심(一片丹心)이야 가싈 줄이 이시랴",
        "modern": "이 몸이 죽고 죽어 백 번을 다시 죽어\n백골이 흙먼지가 되어 넋이야 있든 없든\n임을 향한 한 조각 붉은 마음이야 변할 리가 있으랴",
        "theme": "고려 왕조에 대한 변함없는 충절을 노래한 시조로, 이방원의 회유(하여가)에 대한 단호한 거절의 답가이다. 죽음을 거듭해도 변치 않을 절의를 강조하며 '일편단심'이라는 표현으로 우리말 성어에 큰 영향을 남겼다.",
        "keywords": ["정몽주", "충절", "일편단심", "고려", "절의"],
    },
    "오우가": {
        "genre": "시조", "author": "윤선도", "period": "조선",
        "original": "[서시]\n내 버디 몇치나 ᄒᆞ니 수석(水石)과 송죽(松竹)이라\n동산(東山)의 ᄃᆞᆯ오르니 긔 더옥 반갑고야\n두어라 이 다ᄉᆞᆺ 밧긔 또 더ᄒᆞ야 머엇ᄒᆞ리\n\n[죽(竹)]\n나모도 아닌 거시 플도 아닌 거시\n곳기ᄂᆞᆫ 뉘 시기며 속은 어이 뷔연ᄂᆞᆫ다\n뎌러코 사시(四時)예 프르니 그를 됴하ᄒᆞ노라",
        "modern": "[서시]\n내 벗이 몇인가 하니 물과 돌, 소나무와 대나무이다\n동산에 달 오르니 그것이 더욱 반갑구나\n두어라, 이 다섯 밖에 또 더하여 무엇하리\n\n[대나무]\n나무도 아닌 것이 풀도 아닌 것이\n곧기는 누가 시켰으며 속은 어찌 비어 있는가\n저러고도 사계절 내내 푸르니 그를 좋아하노라",
        "theme": "물, 돌, 소나무, 대나무, 달 다섯 가지 자연물을 벗으로 삼아 각각의 덕성을 예찬한 연시조. 자연물에 인격적 가치를 부여하는 물아일체의 강호가도 시조를 대표하며, 대상의 속성을 관찰하여 유교적 덕목을 이끌어내는 기법이 뛰어나다.",
        "keywords": ["윤선도", "자연", "강호가도", "연시조", "대나무"],
    },
    "훈민가": {
        "genre": "시조", "author": "정철", "period": "조선",
        "original": "아바님 날 나ᄒᆞ시고 어마님 날 기ᄅᆞ시니\n두 분곳 아니시면 이 몸이 사라시랴\n하ᄂᆞᆯ ᄀᆞ툰 ᄀᆞᅀᅵ 업슨 은덕(恩德)을 어ᄃᆡ ᄃᆞ혀 갑ᄉᆞ오리",
        "modern": "아버님 나를 낳으시고 어머님 나를 기르시니\n두 분이 아니었으면 이 몸이 살았으랴\n하늘같이 끝없는 은덕을 어디에다 갚을 수 있으리",
        "theme": "백성을 교화하기 위해 정철이 강원도 관찰사 시절 지은 연시조로, 유교적 윤리 덕목(효, 우애, 충)을 알기 쉬운 우리말로 풀어 노래했다. 관념적 교훈을 부모의 은혜라는 구체적 감정으로 형상화하여 설득력을 높였다.",
        "keywords": ["정철", "효", "교훈", "백성교화", "연시조"],
    },
    "동짓달_기나긴_밤을": {
        "genre": "시조", "author": "황진이", "period": "조선",
        "original": "동지(冬至)ㅅᄃᆞᆯ 기나긴 밤을 한 허리를 버혀 내여\n춘풍(春風) 니불 아래 서리서리 너헛다가\n어론 님 오신 날 밤이여든 구뷔구뷔 펴리라",
        "modern": "동짓달 기나긴 밤의 한가운데를 베어내어\n봄바람 이불 아래 서리서리 넣어 두었다가\n정든 임 오신 날 밤이면 굽이굽이 펴리라",
        "theme": "추상적 시간(밤)을 구체적 사물처럼 베고 넣고 편다고 표현한 참신한 발상이 돋보이는 조선 기녀 시조. 임에 대한 그리움을 감각적이고도 여성적인 섬세한 어조로 형상화한 걸작으로 손꼽힌다.",
        "keywords": ["황진이", "그리움", "시간의 형상화", "기녀시조", "참신한 발상"],
    },
    "이화에_월백하고": {
        "genre": "시조", "author": "이조년", "period": "고려",
        "original": "이화(梨花)에 월백(月白)ᄒᆞ고 은한(銀漢)이 삼경(三更)인 제\n일지춘심(一枝春心)을 자규(子規)야 알랴마ᄂᆞᆫ\n다정(多情)도 병(病)인 냥ᄒᆞ여 잠 못 드러 ᄒᆞ노라",
        "modern": "배꽃에 달이 환히 비치고 은하수는 삼경(한밤중)인데\n나뭇가지에 서린 봄날의 마음을 소쩍새가 알랴마는\n정이 많은 것도 병인 양하여 잠을 이루지 못하노라",
        "theme": "다정가(多情歌)로도 불리며, 봄밤의 애상적 정서를 시각(배꽃, 달)과 청각(소쩍새 울음) 이미지의 결합으로 섬세하게 형상화한 고려 말 시조. '다정도 병인 양하여'라는 구절은 다정다한(多情多恨)의 정서를 대표하는 표현으로 널리 인용된다.",
        "keywords": ["이조년", "다정가", "봄밤", "감각적 이미지", "애상"],
    },
    "수양산_바라보며": {
        "genre": "시조", "author": "성삼문", "period": "조선",
        "original": "수양산(首陽山) 바라보며 이제(夷齊)를 한(恨)ᄒᆞ노라\n주려 주글진들 채미(採薇)도 ᄒᆞᄂᆞᆫ 것가\n비록애 프새엣 거신들 긔 뉘 ᄯᅡ해 낫ᄃᆞᆫ가",
        "modern": "수양산을 바라보며 백이와 숙제를 한탄하노라\n차라리 굶어 죽을지언정 고사리는 왜 캐어 먹었는가\n비록 산에 절로 난 풀이라 해도 그것이 누구의 땅에서 났단 말인가",
        "theme": "단종 복위를 꾀하다 처형된 사육신 성삼문이 지은 절의가. 주나라 곡식을 먹지 않겠다며 고사리를 캐 먹은 백이·숙제의 절의조차 부족하다고 질책하며, 세조 정권에 대한 자신의 결코 타협하지 않을 지조를 극단적으로 강조했다.",
        "keywords": ["성삼문", "절의", "사육신", "백이숙제", "단종"],
    },
    "삭풍은_나무_끝에_불고": {
        "genre": "시조", "author": "김종서", "period": "조선",
        "original": "삭풍(朔風)은 나모 긋ᄐᆡ 불고 명월(明月)은 눈 속에 찬듸\n만리(萬里) 변성(邊城)에 일장검(一長劍) 집고 셔셔\n긴 파람 큰 ᄒᆞᆫ 소ᄅᆡ에 거칠 것이 업세라",
        "modern": "북풍은 나뭇가지 끝에 불고 밝은 달은 눈 속에 차가운데\n멀고 먼 변방의 성에서 긴 칼 짚고 서서\n휘파람 크게 한 번 불어 젖히니 거칠 것이 없구나",
        "theme": "북방 변경을 지키던 무인 김종서가 호방한 기개를 노래한 시조. 삭풍, 명월, 눈 등 차갑고 웅장한 변방의 이미지와 '일장검'을 짚고 선 화자의 기상이 결합되어 강건하고 씩씩한 호기(豪氣)를 드러낸다.",
        "keywords": ["김종서", "변방", "호방", "기개", "무인"],
    },
    "십년을_경영하여": {
        "genre": "시조", "author": "송순", "period": "조선",
        "original": "십년(十年)을 경영(經營)ᄒᆞ여 초려삼간(草廬三間) 지어내니\n나 한 간 ᄃᆞᆯ 한 간에 청풍(淸風) 한 간 맛져 두고\n강산(江山)은 드릴 듸 업스니 둘러 두고 보리라",
        "modern": "십 년을 계획하여 초가삼간을 지어내니\n나 한 칸, 달 한 칸에 맑은 바람 한 칸을 맡겨 두고\n강산은 (집 안에) 들일 곳이 없으니 (집을) 둘러 두고 보리라",
        "theme": "자연 속 소박한 초가에서 달과 바람을 벗 삼아 사는 삶을 노래한 강호가도 시조. 작은 초가삼간에 자신, 달, 바람을 각각 배치하고 강산 전체를 둘러싼 병풍처럼 여기는 스케일 큰 발상이 인상적이다.",
        "keywords": ["송순", "강호가도", "초가삼간", "안분지족", "자연"],
    },
    "태산이_높다_하되": {
        "genre": "시조", "author": "양사언", "period": "조선",
        "original": "태산(泰山)이 노파 ᄒᆞ되 하ᄂᆞᆯ 아래 뫼히로다\n오르고 또 오ᄅᆞ면 못 오ᄅᆞᆯ 리 업건마ᄂᆞᆫ\n사ᄅᆞᆷ이 졔 아니 오르고 뫼만 놉다 ᄒᆞ더라",
        "modern": "태산이 높다 하되 하늘 아래 산이로다\n오르고 또 오르면 못 오를 리 없건마는\n사람이 스스로 오르지 않고 산만 높다 하더라",
        "theme": "끊임없는 노력과 실천의 중요성을 태산이라는 구체적 대상을 통해 설파한 교훈적 시조. 이상을 향한 도전을 포기한 채 어려움만 탓하는 인간의 나태함을 경계하는 권면적 성격이 뚜렷하다.",
        "keywords": ["양사언", "노력", "교훈", "태산", "실천"],
    },
    "청산리_벽계수야": {
        "genre": "시조", "author": "황진이", "period": "조선",
        "original": "청산리(靑山裏) 벽계수(碧溪水)야 수이 감을 자랑 마라\n일도창해(一到滄海)ᄒᆞ면 다시 오기 어려오니\n명월(明月)이 만공산(滿空山)ᄒᆞ니 쉬여 간들 엇더리",
        "modern": "푸른 산속 맑은 시냇물아 빨리 흘러감을 자랑하지 마라\n한번 넓은 바다에 이르면 다시 돌아오기 어려우니\n밝은 달이 빈 산에 가득한데 잠시 쉬어 간들 어떠하리",
        "theme": "'벽계수'라는 종친의 이름과 시냇물을 중의적으로 활용하고, 자신을 '명월'에 빗대어 유혹한 황진이의 대표 시조. 언어유희(중의법)를 절묘하게 구사한 기녀 시조의 백미로 꼽힌다.",
        "keywords": ["황진이", "중의법", "명월", "벽계수", "언어유희"],
    },

    # ---------------------------------------------------------------------- 가사
    "상춘곡": {
        "genre": "가사", "author": "정극인", "period": "조선",
        "original": "홍진(紅塵)에 뭇친 분네 이내 생애(生涯) 엇더ᄒᆞᆫ고\n녯 사ᄅᆞᆷ 풍류(風流)를 미ᄎᆞᆯ가 못 미ᄎᆞᆯ가\n텬디간(天地間) 남자(男子) 몸이 날만ᄒᆞᆫ 이 하건마ᄂᆞᆫ\n산림(山林)에 뭇쳐 이셔 지락(至樂)을 ᄆᆞᄅᆞᆯ 것가\n수간모옥(數間茅屋)을 벽계수(碧溪水) 앏픠 두고\n송죽(松竹) 울울리(鬱鬱裏)예 풍월주인(風月主人) 되어셔라",
        "modern": "속세에 묻혀 사는 분들이여, 나의 생활이 어떠한가\n옛사람의 풍류를 따를 것인가 못 따를 것인가\n천지간 남자 몸으로 나만 한 사람이 많건마는\n산림에 묻혀 살면서 지극한 즐거움을 모를 것인가\n몇 칸짜리 초가집을 맑은 시냇물 앞에 지어 두고\n소나무와 대나무 우거진 속에서 자연을 즐기는 주인이 되었구나",
        "theme": "현전하는 최초의 양반 가사로, 봄날 자연 속에서의 유유자적한 삶을 예찬한 강호가도 문학의 효시로 평가된다. 물아일체의 흥취와 안빈낙도의 삶의 태도가 유려한 대구와 설의법으로 펼쳐진다.",
        "keywords": ["정극인", "강호가도", "안빈낙도", "봄", "최초의 가사"],
    },
    "사미인곡": {
        "genre": "가사", "author": "정철", "period": "조선",
        "original": "이 몸 삼기실 제 님을 조ᄎᆞ 삼기시니\nᄒᆞᆫ평ᄉᆡᆼ 연분(緣分)이며 하ᄂᆞᆯ 모ᄅᆞᆯ 일이런가\n나 ᄒᆞ나 졈어 잇고 님 ᄒᆞ나 날 괴시니\n이 ᄆᆞᄋᆞᆷ 이 ᄉᆞ랑 견졸 ᄃᆡ 노여 업다\n평ᄉᆡᆼ애 원(願)ᄒᆞ요ᄃᆡ ᄒᆞᆫᄃᆡ 녜쟈 ᄒᆞ얏더니\n늙거야 므ᄉᆞᆷ 일로 외오 두고 그리는고",
        "modern": "이 몸이 태어날 때 임을 따라 태어나니\n한평생 함께할 인연이며 하늘이 모를 일이던가\n나는 오직 젊어 있고 임은 오직 나를 사랑하시니\n이 마음 이 사랑 견줄 곳이 전혀 없다\n평생에 원하되 (임과) 함께 살아가자 하였더니\n늙어서야 무슨 일로 외따로 두고 그리워하는가",
        "theme": "임금을 떠나 있는 신하의 충정을 이별한 여인이 임을 그리워하는 형식(충신연주지사)으로 노래한 정철의 대표 가사. 계절의 흐름에 따라 임에 대한 그리움을 형상화하는 구성이 '속미인곡'과 함께 가사 문학의 절정으로 꼽힌다.",
        "keywords": ["정철", "충신연주지사", "임금", "그리움", "계절"],
    },
    "관동별곡": {
        "genre": "가사", "author": "정철", "period": "조선",
        "original": "강호(江湖)애 병(病)이 깁퍼 듁님(竹林)의 누엇더니\n관동(關東) 팔백(八百) 니(里)에 방면(方面)을 맛디시니\n어와 셩은(聖恩)이야 가지록 망극(罔極)ᄒᆞ다\n연츄문(延秋門) 드리ᄃᆞ라 경회(慶會) 남문(南門) ᄇᆞ라보며\n하직(下直)고 믈너나니 옥졀(玉節)이 알ᄑᆡ 셧다",
        "modern": "자연을 사랑하는 병이 깊어 대숲에 누워 있었더니\n강원도 관찰사의 직분을 맡겨 주시니\n아아, 임금의 은혜야말로 갈수록 그지없다\n연추문으로 달려 들어가 경회루 남문을 바라보며\n하직하고 물러나니 관찰사의 신표(玉節)가 앞에 서 있다",
        "theme": "강원도 관찰사로 부임한 정철이 관동팔경의 절경을 유람하며 그 감흥과 애민 정신, 신선 사상을 노래한 기행 가사의 대표작. 웅장한 자연 묘사와 연군지정(戀君之情)이 조화를 이루는 걸작으로 평가된다.",
        "keywords": ["정철", "기행가사", "관동팔경", "연군", "관찰사"],
    },
    "규원가": {
        "genre": "가사", "author": "허난설헌", "period": "조선",
        "original": "엊그제 저멋더니 ᄒᆞ마 어이 다 늙거니\n소년행락(少年行樂) 생각ᄒᆞ니 일러도 쇽졀업다\n늙거야 셜운 말ᄉᆞᆷ ᄒᆞ자ᄒᆞ니 목이 멘다\n부모(父母) 성친(生親)ᄒᆞ야 이 내 몸 길러 낼 제\n공후배필(公侯配匹)은 못 바라도 군자호구(君子好逑) 원(願)ᄒᆞ더니",
        "modern": "엊그제 젊었더니 어느새 어찌 이리 다 늙었는가\n젊은 시절의 즐거움을 생각하니 말해도 소용없다\n늙어서야 서러운 말씀을 하려 하니 목이 멘다\n부모님이 나를 낳으시어 이 몸을 길러 내실 때\n높은 벼슬아치의 배필은 못 바라도 좋은 남편감을 원하였더니",
        "theme": "규방(閨房)에 갇힌 여인의 한(恨)과 남편에 대한 원망을 절절하게 토로한 조선 시대 규방 가사의 대표작. 유교적 가부장제 속에서 억눌린 여성의 내면을 섬세한 언어로 형상화하여 여성 문학사에서 중요한 위치를 차지한다.",
        "keywords": ["허난설헌", "규방가사", "여성의 한", "가부장제", "원망"],
    },
}


# ============================================================================
# 2. 세션 상태 초기화
# ============================================================================
if "selected_poem" not in st.session_state:
    st.session_state.selected_poem = None
if "analysis_cache" not in st.session_state:
    st.session_state.analysis_cache = {}
if "image_cache" not in st.session_state:
    st.session_state.image_cache = {}
if "last_error" not in st.session_state:
    st.session_state.last_error = {}


# ============================================================================
# 3. 검색/필터 유틸리티
# ============================================================================
def filter_poems(query: str, genres: list) -> list:
    """제목·원문·현대어풀이·키워드 기준으로 실시간 필터링."""
    query = (query or "").strip().lower()
    results = []
    for title, poem in POEMS_DB.items():
        if poem["genre"] not in genres:
            continue
        if not query:
            results.append(title)
            continue
        haystack = " ".join([
            title,
            poem["author"],
            poem["original"],
            poem["modern"],
            " ".join(poem.get("keywords", [])),
        ]).lower()
        if query in haystack:
            results.append(title)
    return results


# ============================================================================
# 4. OpenAI 클라이언트 & API 키 처리 (Streamlit Cloud 배포 최적화)
# ============================================================================
def get_api_key() -> str:
    """st.secrets에서 안전하게 API 키를 조회. 없으면 빈 문자열 반환."""
    try:
        return str(st.secrets.get("OPENAI_API_KEY", "")).strip()
    except Exception:
        return ""


def api_key_available() -> bool:
    return bool(get_api_key())


@st.cache_resource(show_spinner=False)
def get_client(_api_key: str):
    """OpenAI 클라이언트를 생성. 실패 시 None을 반환하여 시뮬레이션 모드로 전환."""
    if OpenAI is None or not _api_key:
        return None
    try:
        return OpenAI(api_key=_api_key)
    except Exception:
        return None


# ============================================================================
# 5. AI 분석 파이프라인 (GPT: 공간구도 · 표현기법 JSON 추출)
# ============================================================================
ANALYSIS_SYSTEM_PROMPT = """당신은 한국 고전시가 전문 국문학자입니다.
주어진 고전시가(원문과 현대어 풀이)를 분석하여 반드시 아래 스키마에 맞는 JSON 객체만 출력하세요.
설명, 코드블록 표시(```), 그 외 부가 텍스트를 절대 포함하지 마세요. 오직 JSON만 반환합니다.

JSON 스키마:
{
  "spatial_composition": {
    "distant": "원경(遠景)에 해당하는 장면과 그 의미에 대한 2~3문장 설명",
    "middle": "중경(中景)에 해당하는 장면과 그 의미에 대한 2~3문장 설명",
    "near": "근경(近景) 혹은 화자의 정서가 응집된 장면에 대한 2~3문장 설명"
  },
  "techniques": [
    {"name": "표현 기법 이름 (예: 선경후정, 설의법, 대구법, 의인법, 중의법, 감정이입 등)",
     "explanation": "해당 기법이 무엇인지에 대한 1~2문장 설명",
     "evidence": "작품 속에서 이 기법이 드러나는 구체적 구절 인용 또는 서술"}
    // 2~4개 항목
  ],
  "emotion": "작품 전체를 관통하는 화자의 정서를 한 문장으로 요약",
  "theme_summary": "작품의 주제 의식을 2~3문장으로 종합 해설",
  "dalle_prompt": "위 공간 구도(원경·중경·근경)와 정서를 반영한, 한국 전통 수묵산수화(Korean ink wash landscape painting, sumukhwa) 스타일의 영문 이미지 생성 프롬프트. 구체적인 시각 요소(산, 물, 나무, 인물, 계절감, 여백의 미 등)를 포함하여 100단어 내외의 영어로 작성"
}
"""


def call_gpt_analysis(poem: dict, title: str, client, model_name: str = "gpt-4o"):
    """GPT를 호출하여 공간 구도 및 표현 기법을 JSON으로 추출."""
    user_prompt = f"""작품명: {title}
갈래: {poem['genre']} / 작가: {poem['author']} / 시대: {poem['period']}

[원문]
{poem['original']}

[현대어 풀이]
{poem['modern']}

[작품 개관]
{poem['theme']}

위 작품을 분석하여 지시된 JSON 스키마로만 응답하세요."""

    response = client.chat.completions.create(
        model=model_name,
        temperature=0.5,
        max_tokens=1200,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )
    raw = response.choices[0].message.content
    # response_format을 지원하지 않는 모델을 대비해 코드펜스 방어적으로 제거
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
    data = json.loads(cleaned)
    return data


def build_simulation_analysis(poem: dict, title: str) -> dict:
    """API 키가 없거나 호출 실패 시 사용하는 규칙 기반 시뮬레이션 분석 결과."""
    genre = poem["genre"]
    default_techniques_by_genre = {
        "향가": [
            {"name": "돈호법", "explanation": "대상을 부름으로써 시상을 환기하는 기법입니다.",
             "evidence": "화자가 대상(임, 자연물, 신)을 직접 부르는 구절에서 확인됩니다."},
            {"name": "비유법", "explanation": "자연물에 화자의 정서나 인물의 성격을 빗대어 표현합니다.",
             "evidence": "낙엽, 잣나무, 달 등 자연물을 통한 비유가 드러납니다."},
        ],
        "고려가요": [
            {"name": "반복법(후렴구)", "explanation": "동일한 여음구를 반복하여 운율감과 정서적 여운을 형성합니다.",
             "evidence": "각 연 뒤에 반복되는 후렴구에서 확인됩니다."},
            {"name": "영탄법", "explanation": "감탄의 어조로 화자의 정서를 직접적으로 드러냅니다.",
             "evidence": "'아으', '위' 등 감탄 표현에서 확인됩니다."},
        ],
        "시조": [
            {"name": "대구법", "explanation": "형태나 의미가 대응되는 구절을 나란히 배치하는 기법입니다.",
             "evidence": "초장과 중장, 혹은 중장 내부의 대응 구조에서 확인됩니다."},
            {"name": "설의법", "explanation": "의문의 형식을 빌려 화자의 확신이나 정서를 강조합니다.",
             "evidence": "종장의 의문형 종결 어미에서 확인됩니다."},
        ],
        "가사": [
            {"name": "선경후정", "explanation": "먼저 자연 경관을 묘사한 뒤 화자의 정서를 서술하는 구성 방식입니다.",
             "evidence": "경관 묘사 이후 정서 표출로 이어지는 흐름에서 확인됩니다."},
            {"name": "대구법", "explanation": "대응되는 구절의 반복적 배치로 리듬감을 형성합니다.",
             "evidence": "4음보의 대구적 구절 배치에서 확인됩니다."},
        ],
    }
    techniques = default_techniques_by_genre.get(genre, default_techniques_by_genre["시조"])

    dalle_prompt = (
        f"A traditional Korean ink wash landscape painting (sumukhwa) in monochrome grey tones, "
        f"depicting layered mountains fading into misty distance (distant view), mid-ground pine trees "
        f"and a winding river (middle view), and a solitary scholar or small hanok pavilion in the "
        f"foreground (near view). Delicate brush strokes, generous negative space (yeobaek), soft rice "
        f"paper texture, evoking the mood of the Korean classical poem '{title}'. Minimalist, serene, "
        f"muted ink tones, vertical hanging scroll composition."
    )

    return {
        "spatial_composition": {
            "distant": f"[시뮬레이션] {genre} 특유의 원경은 대체로 하늘, 달, 먼 산 등 화자를 둘러싼 거시적 배경으로 나타나며, 작품의 정서적 배경을 형성합니다.",
            "middle": f"[시뮬레이션] 중경에서는 강, 나무, 길 등 화자와 대상 사이를 매개하는 경물이 배치되어 시선의 흐름을 안내합니다.",
            "near": f"[시뮬레이션] 근경에는 화자 자신 또는 화자의 정서가 응축된 구체적 사물이 놓여, '{poem['theme'][:40]}...' 로 요약되는 주제 의식이 응집됩니다.",
        },
        "techniques": techniques,
        "emotion": f"[시뮬레이션] {poem['theme'][:60]}...",
        "theme_summary": f"[시뮬레이션 모드] 실제 GPT 분석이 아닌 규칙 기반 예시 데이터입니다. OpenAI API 키를 설정하면 이 작품에 특화된 실제 AI 분석 결과를 확인할 수 있습니다. 개관: {poem['theme']}",
        "dalle_prompt": dalle_prompt,
        "_simulated": True,
    }


# ============================================================================
# 6. 이미지 생성 파이프라인 (DALL·E 3 / 로컬 시뮬레이션)
# ============================================================================
def call_dalle_image(prompt: str, client, quality: str = "standard", style: str = "natural"):
    """DALL·E 3를 호출하여 이미지 URL을 반환."""
    result = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality=quality,
        style=style,
        n=1,
    )
    return result.data[0].url


def build_simulation_image(title: str, genre: str):
    """PIL로 그리는 수묵산수화 풍 시뮬레이션 placeholder 이미지 (API 미사용)."""
    if Image is None:
        return None

    width, height = 900, 700
    bg_color = (247, 243, 233)
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # 원경: 옅은 먼 산 능선 (여러 겹)
    import random
    random.seed(hash(title) % (2**31))
    far_colors = [(196, 196, 188), (176, 176, 168), (156, 156, 148)]
    for i, color in enumerate(far_colors):
        base_y = 220 + i * 40
        points = [(0, base_y)]
        x = 0
        while x < width:
            x += random.randint(60, 120)
            y = base_y + random.randint(-45, 10)
            points.append((min(x, width), y))
        points += [(width, height), (0, height)]
        draw.polygon(points, fill=color)

    # 중경: 강물 띠
    river_y = 430
    draw.polygon(
        [(0, river_y), (width, river_y - 20), (width, river_y + 60), (0, river_y + 90)],
        fill=(222, 228, 220),
    )

    # 근경: 짙은 산/소나무 실루엣
    near_color = (60, 58, 52)
    points = [(0, height)]
    x = 0
    while x < width:
        x += random.randint(70, 140)
        y = height - random.randint(120, 260)
        points.append((min(x, width), y))
    points += [(width, height)]
    draw.polygon(points, fill=near_color)

    # 달 (원형)
    draw.ellipse([width - 160, 60, width - 90, 130], fill=(235, 225, 195), outline=(210, 195, 150))

    # 액자 테두리
    draw.rectangle([15, 15, width - 15, height - 15], outline=(120, 100, 70), width=3)

    # 텍스트 (시뮬레이션 워터마크 + 제목)
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
    draw.text((30, height - 55), f"[SIMULATION] {title} · {genre}", fill=(90, 80, 60), font=font)
    draw.text((30, height - 40), "실제 DALL·E 3 생성 이미지가 아닌 로컬 시뮬레이션 이미지입니다.", fill=(90, 80, 60), font=font)

    return img


# ============================================================================
# 7. 파이프라인 실행기 — 분석 + 이미지 생성을 하나로 묶어 예외를 안전하게 처리
# ============================================================================
def run_ai_pipeline(title: str, poem: dict, model_name: str, img_quality: str, img_style: str):
    api_key = get_api_key()
    client = get_client(api_key)
    errors = []

    # ---- 1) 분석 단계 ----
    analysis_data = None
    used_simulation_for_analysis = False
    if client is not None:
        try:
            with st.spinner("🧠 GPT가 공간 구도와 표현 기법을 분석하는 중입니다..."):
                analysis_data = call_gpt_analysis(poem, title, client, model_name=model_name)
        except Exception as e:
            errors.append(f"GPT 분석 호출 실패 → 시뮬레이션으로 대체: {e}")
            analysis_data = None

    if analysis_data is None:
        used_simulation_for_analysis = True
        analysis_data = build_simulation_analysis(poem, title)

  # ---- 2) 이미지 생성 단계 ----
    image_payload = None
    used_simulation_for_image = False
    
    try:
        with st.spinner("🎨 인물을 제외하고 시의 풍경과 배경을 그리는 중입니다..."):
            import urllib.parse
            
            real_text = poem.get("modern", "")[:200]  # 현대어 풀이 내용
            theme = poem.get("theme", "")             # 시의 주제
            
            # 💡 핵심: '인물 없이 자연 풍경만(no humans, no people, empty landscape scenery)' 지시어 추가
            final_prompt = f"Beautiful empty landscape scenery, purely nature, no humans, no people. Visualizing this atmosphere and place: {theme}, {real_text}"
            
            # URL 인코딩 및 이미지 요청
            encoded_prompt = urllib.parse.quote(final_prompt)
            url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"
            
            image_payload = {"type": "url", "data": url}
            dalle_prompt = final_prompt 
            
    except Exception as e:
        errors.append(f"무료 이미지 생성 실패 → 시뮬레이션으로 대체: {e}")
        image_payload = None
    if image_payload is None:
        used_simulation_for_image = True
        pil_img = build_simulation_image(title, poem["genre"])
        image_payload = {"type": "pil", "data": pil_img}

    analysis_data["_simulated"] = used_simulation_for_analysis
    image_payload["_simulated"] = used_simulation_for_image
    image_payload["prompt"] = dalle_prompt

    st.session_state.analysis_cache[title] = analysis_data
    st.session_state.image_cache[title] = image_payload
    st.session_state.last_error[title] = errors


# ============================================================================
# 8. 결과 렌더링 함수
# ============================================================================
def render_analysis(data: dict):
    
    st.markdown("#### 🗺️ 공간 구도 분석")
    sc = data.get("spatial_composition", {})
    c1, c2, c3 = st.columns(3)
    labels = [("🏔️ 원경(遠景)", "distant", c1), ("🌊 중경(中景)", "middle", c2), ("🌿 근경(近景)", "near", c3)]
    for label, key, col in labels:
        with col:
            st.markdown(
                f"""<div class="spatial-card">
                <div class="spatial-title">{label}</div>
                <div style="font-size:0.88rem; line-height:1.55;">{sc.get(key, '-')}</div>
                </div>""",
                unsafe_allow_html=True,
            )

    st.markdown("#### 🖌️ 문학적 표현 기법")
    for tech in data.get("techniques", []):
        st.markdown(
            f"""<div class="technique-card">
            <b>{tech.get('name', '')}</b><br/>
            <span style="font-size:0.87rem;">{tech.get('explanation', '')}</span><br/>
            <span style="font-size:0.85rem; color:#7A5B00;">▶ 근거: {tech.get('evidence', '')}</span>
            </div>""",
            unsafe_allow_html=True,
        )

    st.markdown("#### 💗 정서 및 주제")
    st.markdown(f"**정서:** {data.get('emotion', '-')}")
    st.write(data.get("theme_summary", "-"))


def render_image(payload: dict):
    st.markdown("#### 🖼️ AI 생성 수묵산수화")
    if payload.get("_simulated"):
        st.caption("⚠️ 시뮬레이션 이미지 (실제 DALL·E 3 호출 아님)")
    if payload["type"] == "url":
        st.image(payload["data"], use_container_width=True, caption="DALL·E 3 생성 이미지")
    elif payload["type"] == "pil" and payload["data"] is not None:
        st.image(payload["data"], use_container_width=True, caption="시뮬레이션 이미지")
    else:
        st.info("이미지를 표시할 수 없습니다. Pillow 패키지 설치 상태를 확인해 주세요.")

    with st.expander("🔍 생성에 사용된 영문 프롬프트 보기"):
        st.code(payload.get("prompt", ""), language="text")


# ============================================================================
# 9. 사이드바 UI — 검색 및 필터
# ============================================================================
with st.sidebar:
    st.markdown("## 📚 고전시가 검색")
    search_query = st.text_input(
        "제목 · 원문 · 현대어 풀이 검색",
        placeholder="예: 청산, 임, 달, 이별 ...",
        key="search_input",
    )

    genre_options = ["향가", "고려가요", "시조", "가사"]
    selected_genres = st.multiselect("갈래 필터", genre_options, default=genre_options)

    filtered_titles = filter_poems(search_query, selected_genres)
    st.markdown(f"**검색 결과: {len(filtered_titles)}편 / 전체 {len(POEMS_DB)}편**")
    st.divider()

    list_container = st.container(height=380)
    with list_container:
        if not filtered_titles:
            st.caption("검색 결과가 없습니다. 다른 키워드로 시도해 보세요.")
        for t in filtered_titles:
            p = POEMS_DB[t]
            display_title = t.replace("_", " ")
            is_selected = st.session_state.selected_poem == t
            btn_label = f"{'👉 ' if is_selected else ''}{display_title}  ·  {p['genre']} · {p['author']}"
            if st.button(btn_label, key=f"select_{t}", use_container_width=True):
                st.session_state.selected_poem = t
                st.rerun()

    st.divider()
    st.markdown("### ⚙️ AI 설정")
    if api_key_available():
        st.success("🔑 OpenAI API 키 연결됨")
    else:
        st.warning("⚠️ API 키 미설정 → 시뮬레이션 모드 작동")
        with st.expander("API 키 등록 방법 (Streamlit Cloud)"):
            st.markdown(
                "1. 앱 관리 화면에서 **Settings → Secrets** 이동\n"
                "2. 아래 내용을 추가 후 저장"
            )
            st.code('OPENAI_API_KEY = "sk-..."', language="toml")

    with st.expander("고급 옵션"):
        model_choice = st.selectbox("분석 모델 (GPT)", ["gpt-4o", "gpt-4o-mini"], index=0)
        img_quality = st.selectbox("이미지 품질 (DALL·E 3)", ["standard", "hd"], index=0)
        img_style = st.selectbox("이미지 스타일 (DALL·E 3)", ["natural", "vivid"], index=0)

    st.divider()
    st.caption(f"© {datetime.now().year} 고전시가 종합 분석 & AI 시각화 · 교육용 데모")


# ============================================================================
# 10. 메인 화면 UI
# ============================================================================
st.title("🖋️ 고전시가 종합 분석 & AI 시각화")
st.caption("향가 · 고려가요 · 시조 · 가사의 공간 구도와 표현 기법을 AI로 분석하고, 수묵산수화로 시각화하는 웹 애플리케이션입니다.")

if not st.session_state.selected_poem or st.session_state.selected_poem not in POEMS_DB:
    st.info("👈 왼쪽 사이드바에서 작품을 검색하고 선택해 주세요.")
    st.markdown("### 📖 수록 작품 한눈에 보기")
    genre_order = ["향가", "고려가요", "시조", "가사"]
    for g in genre_order:
        items = [(t, p) for t, p in POEMS_DB.items() if p["genre"] == g]
        st.markdown(f"**{g} ({len(items)}편)**")
        badge_html = "".join(
            f'<span class="tag-badge">{t.replace("_"," ")} · {p["author"]}</span>' for t, p in items
        )
        st.markdown(badge_html, unsafe_allow_html=True)
        st.write("")
else:
    title = st.session_state.selected_poem
    poem = POEMS_DB[title]
    display_title = title.replace("_", " ")

    st.markdown(f"## {display_title}")
    st.markdown(
        f'<span class="tag-badge">{poem["genre"]}</span>'
        f'<span class="tag-badge">{poem["author"]}</span>'
        f'<span class="tag-badge">{poem["period"]}</span>',
        unsafe_allow_html=True,
    )
    st.write("")

    left_col, right_col = st.columns([1, 1], gap="large")

    # ------------------------------------------------ 좌측: 원문 & 현대어 풀이
    with left_col:
        st.markdown("### 📜 원문")
        st.markdown(f'<div class="poem-box">{poem["original"]}</div>', unsafe_allow_html=True)

        st.markdown("### 💬 현대어 풀이")
        st.markdown(f'<div class="poem-box modern">{poem["modern"]}</div>', unsafe_allow_html=True)

        with st.expander("ℹ️ 작품 개관 및 문학사적 의의", expanded=False):
            st.write(poem["theme"])
            if poem.get("keywords"):
                st.markdown(
                    "".join(f'<span class="tag-badge">#{k}</span>' for k in poem["keywords"]),
                    unsafe_allow_html=True,
                )

    # ------------------------------------------------ 우측: AI 분석 & 이미지
    with right_col:
        st.markdown("### 🤖 AI 분석 & 시각화")

        has_cache = title in st.session_state.analysis_cache
        btn_label = "🔄 다시 분석하기" if has_cache else "✨ AI 분석 및 이미지 생성 시작"

        if st.button(btn_label, type="primary", use_container_width=True, key=f"run_{title}"):
            run_ai_pipeline(
                title, poem,
                model_name=model_choice,
                img_quality=img_quality,
                img_style=img_style,
            )
            st.rerun()

        if has_cache:
            errs = st.session_state.last_error.get(title, [])
            for e in errs:
                st.error(e)

            render_analysis(st.session_state.analysis_cache[title])
            st.divider()
            render_image(st.session_state.image_cache[title])
        else:
            st.caption("버튼을 눌러 이 작품의 공간 구도·표현 기법 분석과 AI 이미지 생성을 시작하세요.")
            if not api_key_available():
                st.caption("※ 현재 API 키가 설정되어 있지 않아 시뮬레이션 모드로 실행됩니다.")
