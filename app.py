import streamlit as st
import random
import json
import os
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
if 'show_answer_trigger' not in st.session_state:
    st.session_state.show_answer_trigger = False
if 'user_answer_text' not in st.session_state:
    st.session_state.user_answer_text = ""

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
        st.success("✅ 자가 검증용 해설지(answer.pdf) 연결 성공!")
    else:
        st.warning("⚠️ 깃허브에 해설지 `answer.pdf` 파일이 아직 보이지 않습니다. 파일을 업로드 하시면 정답 확인 기능이 활성화됩니다.")

elif menu == "📝 풀이 시험장":
    st.header("📝 수매씽 무한 랜덤 시험장")
    
    if is_pdf_broken or st.session_state.current_target_page is None:
        st.error("📁 PDF 교재 상태를 먼저 확인해 주세요.")
    else:
        target_page = st.session_state.current_target_page
        st.markdown(f"### 🎯 **현재 랜덤 출제 범위:** [ 원본 {target_page} 페이지 ]")
        
        # 1. 문제 이미지 출력
        try:
            doc = fitz.open(FIXED_PDF_NAME)
            page = doc.load_page(target_page - 1)
            zoom = 2.0
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            st.image(pix.tobytes("png"), caption=f"수매씽 {target_page}페이지 문제", use_container_width=True)
            doc.close()
        except Exception as e:
            st.error(f"❌ 문제 이미지를 불러오는 중 오류가 발생했습니다: {e}")

        st.write("")
        
        # 2. 정답 입력 칸
        user_ans = st.text_input("여기에 본인이 생각한 정답을 입력하세요:", key=f"ans_{target_page}").strip()
        if user_ans:
            st.session_state.user_answer_text = user_ans

        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔍 내가 적은 정답 제출하고 해설지 보기", use_container_width=True):
                if not has_answer_pdf:
                    st.error("⚠️ 깃허브 저장소에 `answer.pdf` 파일이 필요합니다.")
                elif not user_ans:
                    st.warning("⚠️ 정답 칸에 먼저 답안을 작성해 주세요!")
                else:
                    st.session_state.show_answer_trigger = True
                    st.rerun()
                    
        with c2:
            if st.button("이 문제는 패스하고 다른 문제 뽑기 ➡️", use_container_width=True):
                st.session_state.show_answer_trigger = False
                st.session_state.user_answer_text = ""
                st.session_state.current_target_page = random.randint(1, total_pages_count)
                st.rerun()

        # 3. [Trigger 활성화 시] 아래에 답지 화면 띄워주기 및 셀프 채점 버튼 제공
        if st.session_state.show_answer_trigger and has_answer_pdf:
            st.write("---")
            st.subheader("📖 해설지 확인 단락")
            st.info(f"내가 입력한 답안: **{st.session_state.user_answer_text}**")
            
            found_ans_zone = False
            try:
                ans_doc = fitz.open(ANSWER_PDF_NAME)
                page_pattern = str(target_page)
                
                # 정답지 전체를 돌며 해당 페이지 번호 텍스트가 있는 페이지를 아래에 렌더링
                for p_idx in range(len(ans_doc)):
                    raw_text = ans_doc[p_idx].get_text("text")
                    if page_pattern in raw_text:
                        found_ans_zone = True
                        ans_page = ans_doc[p_idx]
                        pix_ans = ans_page.get_pixmap(matrix=fitz.Matrix(1.8, 1.8))
                        st.image(pix_ans.tobytes("png"), caption=f"해설지 내 {target_page}페이지 관련 구역", use_container_width=True)
                ans_doc.close()
                
                if not found_ans_zone:
                    st.warning(f"ℹ️ 정답지 파일 안에서 '{target_page}' 페이지 번호 텍스트 구역을 명확히 찾지 못했습니다. 전체 해설지를 업로드하셨는지 확인해 주세요.")
            except Exception as e:
                st.error(f"❌ 해설지 이미지를 불러오는 과정에서 오류가 발생했습니다: {e}")
            
            st.write("")
            st.markdown("#### 🎯 해설지를 보고 직접 채점해 주세요:")
            
            b1, b2 = st.columns(2)
            with b1:
                if st.button("⭕ 정답입니다! (맞춤 처리)", use_container_width=True):
                    st.session_state.history_stats["correct"] += 1
                    st.session_state.history_stats["total"] += 1
                    st.session_state.solved_count += 1
                    st.session_state.show_answer_trigger = False
                    st.session_state.user_answer_text = ""
                    st.session_state.current_target_page = random.randint(1, total_pages_count)
                    st.success("정답 처리되었습니다! 다음 문제로 넘어갑니다.")
                    st.rerun()
            with b2:
                if st.button("❌ 틀렸습니다... (오답노트행)", use_container_width=True):
                    st.session_state.history_stats["total"] += 1
                    st.session_state.solved_count += 1
                    if target_page not in st.session_state.wrong_notes:
                        st.session_state.wrong_notes.append(target_page)
                    save_to_local()
                    st.session_state.show_answer_trigger = False
                    st.session_state.user_answer_text = ""
                    st.session_state.current_target_page = random.randint(1, total_pages_count)
                    st.error("오답노트에 기록되었습니다! 다음 문제로 넘어갑니다.")
                    st.rerun()

elif menu == "🔥 오답노트 관리":
    st.header("🔥 복습이 필요한 오답 목록")
    if not st.session_state.wrong_notes:
        st.success("🎉 현재 누적된 오답 페이지가 없습니다!")
    else:
        sorted_notes = sorted(st.session_state.wrong_notes)
        for w_page in sorted_notes:
            st.warning(f"📋 복습 범위: **{w_page} 페이지**")
            try:
                doc = fitz.open(FIXED_PDF_NAME)
                page = doc.load_page(w_page - 1)
                pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
                st.image(pix.tobytes("png"), use_container_width=True)
                doc.close()
            except:
                pass
                
            if st.button("이 페이지 완벽 마스터 (삭제)", key=f"del_page_{w_page}"):
                st.session_state.wrong_notes.remove(w_page)
                save_to_local()
                st.success("제거되었습니다.")
                st.rerun()
            st.write("---")
