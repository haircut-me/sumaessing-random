 import streamlit as st
import random
import json
import os
import re
from datetime import datetime
import fitz  # PyMuPDF

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
        except:
            pass

st.set_page_config(page_title="수매씽 무한 랜덤 문제 은행", layout="wide")

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
if 'scoring_result' not in st.session_state:
    st.session_state.scoring_result = None

is_pdf_broken = False
total_pages_count = 0

if os.path.exists(FIXED_PDF_NAME):
    try:
        doc = fitz.open(FIXED_PDF_NAME)
        total_pages_count = len(doc)
        doc.close()
        if total_pages_count > 0 and st.session_state.current_target_page is None:
            st.session_state.current_target_page = random.randint(1, total_pages_count)
    except:
        is_pdf_broken = True
else:
    is_pdf_broken = True

has_answer_pdf = os.path.exists(ANSWER_PDF_NAME)

st.sidebar.title("🎮 수매씽 무한 랜덤 문제 은행")
st.sidebar.markdown(f"### 🔥 연속 학습일: `{st.session_state.streak}일째`")
st.sidebar.markdown(f"### 🎯 오늘 푼 문항수: `{st.session_state.solved_count}개`")
menu = st.sidebar.radio("메뉴 이동", ["📁 자동 문제 은행 상태", "📝 풀이 시험장", "🔥 오답노트 관리"])

if menu == "📁 자동 문제 은행 상태":
    st.header("📁 내장 문제 은행 관리 상태")
    if is_pdf_broken:
        st.error(f"❌ 깃허브에 `{FIXED_PDF_NAME}` 파일이 없거나 올바르지 않습니다.")
    else:
        st.success(f"✅ 수매씽 문제집 연결 성공! (총 {total_pages_count}페이지)")
        
    if has_answer_pdf:
        st.success("✅ 스마트 AI 채점용 정답지(answer.pdf) 연결 성공!")
    else:
        st.warning("⚠️ 깃허브에 `answer.pdf` 파일이 없습니다. 파일을 올려주셔야 자동 채점이 작동합니다!")

elif menu == "📝 풀이 시험장":
    st.header("📝 수매씽 무한 랜덤 시험장")
    
    if is_pdf_broken or st.session_state.current_target_page is None:
        st.error("📁 PDF 교재 상태를 먼저 확인해 주세요.")
    else:
        target_page = st.session_state.current_target_page
        st.markdown(f"### 🎯 **현재 랜덤 출제 범위:** [ 원본 {target_page} 페이지 ]")
        
        try:
            doc = fitz.open(FIXED_PDF_NAME)
            page = doc.load_page(target_page - 1)
            zoom = 2.0
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            st.image(pix.tobytes("png"), caption=f"수매씽 {target_page}페이지 문제", use_container_width=True)
            doc.close()
        except Exception as e:
            st.error(f"❌ 페이지 이미지를 불러오는 중 오류가 발생했습니다: {e}")

        st.write("")
        
        user_ans = st.text_input("여기에 정답을 입력하세요 (예: 3 또는 24):", key=f"ans_{target_page}").strip()

        # ⭕ ❌ 디자인 출력 부분 에러(오타) 완전 수정 완료!
        if st.session_state.scoring_result is not None:
            if st.session_state.scoring_result == "정답":
                st.markdown("<div style='text-align:center; padding:10px;'><span style='font-size:100px; color:#FF4B4B;'>⭕</span><h3 style='color:#FF4B4B;'>정답입니다! 🎉</h3></div>", unsafe_allowed_html=True)
            elif st.session_state.scoring_result == "오답":
                st.markdown("<div style='text-align:center; padding:10px;'><span style='font-size:100px; color:#FF4B4B;'>❌</span><h3 style='color:#FF4B4B;'>아쉬워요! 오답노트에 보관되었습니다. 💪</h3></div>", unsafe_allowed_html=True)
            elif st.session_state.scoring_result == "탐색실패":
                st.info("ℹ️ 정답지에서 해당 페이지 해설 구역을 찾지 못했습니다. 오른쪽 패스 버튼을 눌러주세요.")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("💯 정답 제출 및 실시간 채점", use_container_width=True):
                if not has_answer_pdf:
                    st.error("⚠️ 깃허브에 `answer.pdf` 정답지 파일이 없어 채점할 수 없습니다.")
                elif not user_ans:
                    st.warning("⚠️ 정답을 먼저 입력해 주세요!")
                else:
                    try:
                        ans_doc = fitz.open(ANSWER_PDF_NAME)
                        found_target_zone = False
                        full_matched_text = ""
                        
                        page_pattern = str(target_page)
                        for p_idx in range(len(ans_doc)):
                            page_content = ans_doc[p_idx].get_text("text")
                            if page_pattern in page_content:
                                full_matched_text += "\n" + page_content
                                found_target_zone = True
                        
                        ans_doc.close()
                        
                        if found_target_zone:
                            cleaned_ans_pool = re.sub(r'\s+', '', full_matched_text)
                            cleaned_
