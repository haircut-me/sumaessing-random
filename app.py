import streamlit as st
import random
import json
import os
from datetime import datetime
import fitz
from streamlit_drawable_canvas import st_canvas

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

st.set_page_config(page_title="Sumaessing Exam", layout="wide")

if 'initialized' not in st.session_state:
    st.session_state.wrong_notes = []
    st.session_state.history_stats = {"correct": 0, "total": 0}
    st.session_state.streak = 0
    st.session_state.last_login = ""
    load_from_local()
    today_str = datetime.now().strftime("%Y-%m-%d")
    if st.session_state.last_login and st.session_state.last_login != today_str:
        st.session_state.streak += 1
    elif not st.session_state.last_login:
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
if 'user_answer_text' not in st.session_state:
    st.session_state.user_answer_text = ""
if 'canvas_key_counter' not in st.session_state:
    st.session_state.canvas_key_counter = 0

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

st.sidebar.title("🎮 수매씽 스마트 탭 시험장")
st.sidebar.markdown(f"### 🔥 연속 학습일: `{st.session_state.streak}일째`")
st.sidebar.markdown(f"### 🎯 오늘 푼 문항수: `{st.session_state.solved_count}개`")
menu = st.sidebar.radio("메뉴 이동", ["📁 시스템 연결 상태", "📝 손글씨 랜덤 시험장", "🔥 오답노트 관리"])

if menu == "📁 시스템 연결 상태":
    st.header("📁 교재 및 해설지 파일 상태")
    if is_pdf_broken:
        st.error("❌ sumaessing.pdf 파일이 누락되었거나 손상되었습니다.")
    else:
        st.success(f"✅ 문제집 연결 성공! (총 {total_pages_count}개 문항)")
    if has_answer_pdf:
        st.success("✅ 해설지(answer.pdf) 연결 성공!")
    else:
        st.warning("⚠️ 해설지 answer.pdf 파일이 보이지 않습니다.")

elif menu == "📝 손글씨 랜덤 시험장":
    st.header("📝 수매씽 1:1 손글씨 랜덤 시험장")
    if is_pdf_broken or st.session_state.current_target_page is None:
        st.error("📁 PDF 파일 상태를 체크해 주세요.")
    else:
        file_page = st.session_state.current_target_page
        st.markdown(f"### 🎯 **현재 출제 문항:** [ {file_page}번째 문제 ]")
        try:
            doc = fitz.open(FIXED_PDF_NAME)
            page = doc.load_page(file_page - 1)
            pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
            st.image(pix.tobytes("png"), use_container_width=True)
            doc.close()
        except Exception as e:
            st.error(f"❌ 이미지 로드 실패: {e}")

        st.write("")
        st.markdown("#### ✍️ 탭 펜슬로 아래 도화지에 풀이를 적으세요:")
        
        tool_col1, tool_col2 = st.columns([1, 3])
        with tool_col1:
            drawing_mode = st.radio("도구", ("draw", "transform"), format_func=lambda x: "✏️ 펜슬 필기" if x=="draw" else "🖐️ 스크롤 대기")
            stroke_width = st.slider("두께", 1, 10, 3)
            stroke_color = st.color_picker("색상", "#0000FF")
        
        with tool_col2:
            try:
                canvas_result = st_canvas(
                    fill_color="rgba(255, 255, 255, 0)",
                    stroke_width=stroke_width,
                    stroke_color=stroke_color,
                    background_color="#FDFDFD",
                    height=380,
                    drawing_mode=drawing_mode,
                    key=f"can_{file_page}_{st.session_state.canvas_key_counter}",
                    update_streamlit=False,
                    display_toolbar=True
                )
            except:
                st.error("⚠️ 캔버스 로딩 실패. 잠시 후 새로고침 해주세요.")
            
        st.write("")
        user_ans = st.text_input("🎯 최종 정답 입력:", key=f"ans_{file_page}").strip()
        if user_ans:
            st.session_state.user_answer_text = user_ans

        st.write("")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔍 내 풀이 제출하고 해설 확인", use_container_width=True):
                if not has_answer_pdf:
                    st.error("⚠️ answer.pdf 파일이 필요합니다.")
                elif not user_ans:
                    st.warning("⚠️ 정답 칸을 채워주세요.")
                else:
                    st.session_state.show_answer_trigger = True
                    st.rerun()
        with c2:
            if st.button("이 문제는 패스하고 다른 문제 뽑기 ➡️", use_container_width=True):
                st.session_state.show_answer_trigger = False
                st.session_state.user_answer_text = ""
                st.session_state.canvas_key_counter += 1
                st.session_state.current_target_page = random.randint(1, total_pages_count)
                st.rerun()

        if st.session_state.show_answer_trigger and has_answer_pdf:
            st.write("---")
            st.subheader("📖 1:1 자동 매칭 정답 해설")
            st.info(f"내가 입력한 정답: {st.session_state.user_answer_text}")
            try:
                ans_doc = fitz.open(ANSWER_PDF_NAME)
                if (file_page - 1) < len(ans_doc):
                    ans_page = ans_doc[file_page - 1]
                    pix_ans = ans_page.get_pixmap(matrix=fitz.Matrix(1.8, 1.8))
                    st.image(pix_ans.tobytes("png"), use_container_width=True)
                else:
                    st.error("❌ 해설지 페이지 부족")
                ans_doc.close()
            except Exception as e:
                st.error(f"❌ 해설지 로드 실패: {e}")
            
            st.write("")
            b1, b2 = st.columns(2)
            with b1:
                if st.button("⭕ 정답입니다!", use_container_width=True):
                    st.session_state.history_stats["correct"] += 1
                    st.session_state.history_stats["total"] += 1
                    st.session_state.solved_count += 1
                    st.session_state.show_answer_trigger = False
                    st.session_state.user_answer_text = ""
                    st.session_state.canvas_key_counter += 1
                    st.session_state.current_target_page = random.randint(1, total_pages_count)
                    save_to_local()
                    st.rerun()
            with b2:
                if st.button("❌ 틀렸습니다...", use_container_width=True):
                    st.session_state.history_stats["total"] += 1
                    st.session_state.solved_count += 1
                    if file_page not in st.session_state.wrong_notes:
                        st.session_state.wrong_notes.append(file_page)
                    st.session_state.show_answer_trigger = False
                    st.session_state.user_answer_text = ""
                    st.session_state.canvas_key_counter += 1
                    st.session_state.current_target_page = random.randint(1, total_pages_count)
                    save_to_local()
                    st.rerun()

elif menu == "🔥 오답노트 관리":
    st.header("🔥 복습이 필요한 오답 목록")
    if not st.session_state.wrong_notes:
        st.success("🎉 오답 문항이 없습니다!")
    else:
        for w_page in sorted(st.session_state.wrong_notes):
            st.warning(f"📋 복습 대상: {w_page}번째 문항")
            try:
                doc = fitz.open(FIXED_PDF_NAME)
                page = doc.load_page(w_page - 1)
                pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
                st.image(pix.tobytes("png"), use_container_width=True)
                doc.close()
            except:
                pass
            if st.button("이 문항 복습 완료 (삭제)", key=f"del_{w_page}"):
                st.session_state.wrong_notes.remove(w_page)
                save_to_local()
                st.rerun()
            st.write("---")
