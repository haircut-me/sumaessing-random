import streamlit as st
import random
import json
import os
from datetime import datetime
import fitz  # PyMuPDF
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

# 1. 페이지 설정
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
if 'user_answer_text' not in st.session_state:
    st.session_state.user_answer_text = ""
if 'canvas_key_counter' not in st.session_state:
    st.session_state.canvas_key_counter = 0

# 3. PDF 파일 존재 유무 확인
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

# 4. 사이드바 구성
st.sidebar.title("🎮 수매씽 1:1 스마트 탭 시험장")
st.sidebar.markdown(f"### 🔥 연속 학습일: `{st.session_state.streak}일째`")
st.sidebar.markdown(f"### 🎯 오늘 푼 문항수: `{st.session_state.solved_count}개`")
menu = st.sidebar.radio("메뉴 이동", ["📁 시스템 연결 상태", "📝 손글씨 랜덤 시험장", "🔥 오답노트 관리"])

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

elif menu == "📝 손글씨 랜덤 시험장":
    st.header("📝 수매씽 1:1 손글씨 랜덤 시험장")
    
    if is_pdf_broken or st.session_state.current_target_page is None:
        st.error("📁 PDF 교재 상태를 사이드바 메뉴에서 확인해 주세요.")
    else:
        file_page = st.session_state.current_target_page
        st.markdown(f"### 🎯 **현재 출제 문항:** [ 발췌 파일 내 {file_page}번째 문제 ]")
        
        # 1단계: 문제 이미지 출력
        try:
            doc = fitz.open(FIXED_PDF_NAME)
            page = doc.load_page(file_page - 1)
            pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
            st.image(pix.tobytes("png"), use_container_width=True)
            doc.close()
        except Exception as e:
            st.error(f"❌ 문제 이미지를 로드하지 못했습니다: {e}")

        st.write("")
        st.markdown("#### ✍️ 탭 펜슬로 아래 캔버스에 풀이 과정을 직접 적으세요:")
        
        # 도구 선택 (연필 / 지우개 / 휴지통 역할)
        tool_col1, tool_col2 = st.columns([1, 4])
        with tool_col1:
            drawing_mode = st.radio("도구 선택", ("draw", "transform"), format_func=lambda x: "✏️ 펜슬 쓰기" if x=="draw" else "🖐️ 터치 이동/대기")
            stroke_width = st.slider("펜 굵기 조절", 1, 10, 3)
            stroke_color = st.color_picker("펜 색상 선택", "#0000FF") # 기본 파란색
        
        with tool_col2:
            # 디지털 손글씨 캔버스 배치 (태블릿 전용 가로형 넓은 풀이판)
            canvas_result = st_canvas(
                fill_color="rgba(255, 255, 255, 0)",
                stroke_width=stroke_width,
                stroke_color=stroke_color,
                background_color="#F9F9F9",  # 눈이 편안한 미색 배경
                height=350,
                drawing_mode=drawing_mode,
                key=f"canvas_{file_page}_{st.session_state.canvas_key_counter}",
                update_streamlit=False, # 펜을 쓸 때마다 화면이 출렁이며 리프레시되는 현상 방지
                display_toolbar=True    # 캔버스 자체 실행취소(Undo), 전체 지우기(Trash) 툴바 활성화
            )
            
        st.write("")
        user_ans = st.text_input("🎯 최종 정답 입력:", placeholder="정답을 입력하세요 (예: 5)", key=f"ans_{file_page}").strip()
        if user_ans:
            st.session_state.user_answer_text = user_ans

        st.write("")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔍 내 풀이 제출하고 해설지 확인", use_container_width=True):
                if not has_answer_pdf:
                    st.error("⚠️ 1:1 매칭된 answer.pdf 파일이 깃허브에 필요합니다.")
                elif not user_ans:
                    st.warning("⚠️ 채점을 위해 최종 정답 칸에 답안을 먼저 입력해 주세요!")
                else:
                    st.session_state.show_answer_trigger = True
                    st.rerun()
                    
        with c2:
            if st.button("이 문제는 패스하고 다른 문제 뽑기 ➡️", use_container_width=True):
                st.session_state.show_answer_trigger = False
                st.session_state.user_answer_text = ""
                st.session_state.canvas_key_counter += 1  # 캔버스 완전 초기화 포인터 증가
                st.session_state.current_target_page = random.randint(1, total_pages_count)
                st.rerun()

        # 정답 제출 후 하단에 정답 요약 및 1:1 매칭 해설지 출력 (내가 쓴 손글씨는 상단 캔버스에 그대로 유지됨)
        if st.session_state.show_answer_trigger and has_answer_pdf:
            st.write("---")
            st.subheader("📖 1:1 매칭 해설 대조창")
            st.success(f"**내가 입력한 최종 정답:** `{st.session_state.user_answer_text}`")
            
            try:
                ans_doc = fitz.open(ANSWER_PDF_NAME)
                if (file_page - 1) < len(ans_doc):
                    ans_page = ans_doc[file_page - 1]
                    pix_ans = ans_page.get_pixmap(matrix=fitz.Matrix(1.8, 1.8))
                    st.image(pix_ans.tobytes("png"), caption=f"현재 {file_page}번 문제에 매칭된 정답지 화면", use_container_width=True)
                else:
                    st.error(f"❌ 해설지(answer.pdf)의 페이지가 부족합니다.")
                ans_doc.close()
            except Exception as e:
                st.error(f"❌ 해설지 이미지를 불러오지 못했습니다: {e}")
            
            st.write("")
            st.markdown("#### 🎯 위의 정식 해설과 본인의 손글씨 풀이를 비교하여 채점해 주세요:")
            
            b1, b2 = st.columns(2)
            with b1:
                if st.button("⭕ 정답입니다! (맞춤 처리)", use_container_width=True):
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
                if st.button("❌ 틀렸습니다... (오답노트행)", use_container_width=True):
                    st.session_state.history_stats["total"] += 1
                    st.session_state.solved_count += 1
                    if file_page not in st.session_state.wrong_notes:
                        st.session_state.wrong_notes.append(file_page)
                    save_to_local()
                    st.session_state.show_answer_trigger = False
                    st.session_state.user_answer_text = ""
                    st.session_state.canvas_key_counter += 1
                    st.session_state.current_target_page = random.randint(1, total_pages_count)
                    st.rerun()

elif menu == "🔥 오답노트 관리":
    st.header("🔥 복습이 필요한 오답 목록")
    if not st.session_state.wrong_notes:
        st.success("🎉 누적된 오답 문항이 없습니다!")
    else:
        for w_page in sorted(st.session_state.wrong_notes):
            st.warning(f"📋 복습 대상: 편집 파일 내 {w_page}번째 문항")
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
