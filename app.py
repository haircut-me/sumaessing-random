import streamlit as st
import random
import json
import os
from datetime import datetime
import fitz  # PyMuPDF
from PIL import Image
import io
import streamlit.components.v1 as components

SAVE_FILE = "math_pilot_solo_data.json"
FIXED_PDF_NAME = "sumaessing.pdf"
ANSWER_PDF_NAME = "answer.pdf"

def save_to_local():
    data = {
        "wrong_notes": st.session_state.wrong_notes,
        "history_stats": st.session_state.history_stats,
        "streak": st.session_state.streak,
        "last_login": st.session_state.last_login
    }
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_from_local():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                st.session_state.wrong_notes = data.get("wrong_notes", [])
                st.session_state.history_stats = data.get("history_stats", {"correct": 0, "total": 0})
                st.session_state.streak = data.get("streak", 0)
                st.session_state.last_login = data.get("last_login", "")
        except Exception:
            pass

# 1. 페이지 초기화
st.set_page_config(page_title="수매씽 무한 랜덤 문제 은행", layout="wide")

# 2. 세션 상태 안전하게 초기화
if 'initialized' not in st.session_state:
    st.session_state.wrong_notes = []
    st.session_state.history_stats = {"correct": 0, "total": 0}
    st.session_state.streak = 0
    st.session_state.last_login = ""
    load_from_local()
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    if st.session_state.last_login:
        if st.session_state.last_login != today_str:
            st.session_state.streak += 1
    else:
        st.session_state.streak = 1
    st.session_state.last_login = today_str
    st.session_state.initialized = True
    save_to_local()

if 'current_target_page' not in st.session_state:
    st.session_state.current_target_page = None
if 'solved_count' not in st.session_state:
    st.session_state.solved_count = 0
if 'show_answer_trigger' not in st.session_state:
    st.session_state.show_answer_trigger = False
if 'ans_offset' not in st.session_state:
    st.session_state.ans_offset = 0

# 3. PDF 파일 연결 상태 확인 체크
is_pdf_broken = False
total_pages_count = 0

if os.path.exists(FIXED_PDF_NAME):
    try:
        doc = fitz.open(FIXED_PDF_NAME)
        total_pages_count = len(doc)
        doc.close()
    except Exception:
        is_pdf_broken = True
else:
    is_pdf_broken = True

if not is_pdf_broken and total_pages_count > 0:
    if st.session_state.current_target_page is None:
        st.session_state.current_target_page = random.randint(1, total_pages_count)

has_answer_pdf = os.path.exists(ANSWER_PDF_NAME)

# 하단 공백을 감지하고 크롭(Crop)하는 스마트 헬퍼 함수
def get_cropped_image_bytes(pdf_path, page_idx, zoom=2.0):
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_idx)
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    img_data = pix.tobytes("png")
    doc.close()
    
    img = Image.open(io.BytesIO(img_data))
    gray_img = img.convert("L")
    
    width, height = gray_img.size
    content_bottom = height
    step = 4
    
    for y in range(height - 1, 0, -step):
        is_row_white = True
        for x in range(0, width, 10):
            if gray_img.getpixel((x, y)) < 245:
                is_row_white = False
                break
        if not is_row_white:
            content_bottom = min(y + 35, height)
            break
            
    if content_bottom < height and content_bottom > 250:
        img = img.crop((0, 0, width, content_bottom))
        
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# 4. 사이드바 구성
st.sidebar.title("🎮 수매씽 1:1 매칭 문제 은행")
st.sidebar.markdown(f"### 🔥 연속 학습일: `{st.session_state.streak}일째`")
st.sidebar.markdown(f"### 🎯 오늘 푼 문항수: `{st.session_state.solved_count}개`")
menu = st.sidebar.radio("메뉴 이동", ["📁 시스템 연결 상태", "📝 1:1 랜덤 시험장", "🔥 오답노트 관리"])

# 5. [메뉴 1] 상태 확인 구역
if menu == "📁 시스템 연결 상태":
    st.header("📁 교재 및 해설지 파일 상태")
    if is_pdf_broken:
        st.error(f"❌ 깃허브 저장소에 {FIXED_PDF_NAME} 파일이 누락되었거나 손상되었습니다.")
    else:
        st.success(f"✅ 편집본 문제집 연결 성공! (총 {total_pages_count}개 문항 탑재)")
        
    if has_answer_pdf:
        st.success(f"✅ 1:1 매칭 해설지({ANSWER_PDF_NAME}) 연결 성공!")
    else:
        st.warning(f"⚠️ 깃허브 저장소에 해설지 {ANSWER_PDF_NAME} 파일이 아직 보이지 않습니다.")

# 6. [메뉴 2] 1:1 랜덤 시험장 구역
elif menu == "📝 1:1 랜덤 시험장":
    st.header("📝 1:1 매칭 랜덤 시험장")
    
    if is_pdf_broken or st.session_state.current_target_page is None:
        st.error("📁 PDF 교재 상태를 사이드바 메뉴에서 확인해 주세요.")
    else:
        file_page = st.session_state.current_target_page
        
        # 상단 레이아웃 분할: 문제 제목과 실시간 인터랙티브 스톱워치 배치
        t_col1, t_col2 = st.columns([2, 1])
        with t_col1:
            st.markdown(f"### 🎯 **현재 출제 문항:** [ 발췌 파일 내 {file_page}번째 문제 ]")
        with t_col2:
            init_running = "false" if st.session_state.show_answer_trigger else "true"
            
            stopwatch_html = f"""
            <div id="sw-box" style="background-color: #FFF3CD; padding: 12px; border-radius: 10px; border: 1px solid #FFEBAA; font-family: sans-serif; text-align: center; box-sizing: border-box;">
                <span style="color: #856404; font-weight: bold; font-size: 14px;">⏱️ 문제 풀이 시간</span>
                <div id="stopwatch-display" style="font-size: 22px; font-weight: bold; color: #856404; margin: 6px
