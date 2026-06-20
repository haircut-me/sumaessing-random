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

# 1. 페이지 초기 설정
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
if 'manual_answer_page_idx' not in st.session_state:
    st.session_state.manual_answer_page_idx = 0

# 3. 파일 유효성 체크
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
total_answer_pages = 0
if has_answer_pdf:
    try:
        ans_doc = fitz.open(ANSWER_PDF_NAME)
        total_answer_pages = len(ans_doc)
        ans_doc.close()
    except:
        pass

# 4. 사이드바 UI
st.sidebar.title("🎮 수매씽 랜덤 문제 은행")
st.sidebar.markdown(f"### 🔥 연속 학습일: `{st.session_state.streak}일째`")
st.sidebar.markdown(f"### 🎯 오늘 푼 문항수: `{st.session_state.solved_count}개`")
menu = st.sidebar.radio("메뉴 이동", ["📁 자동 문제 은행 상태", "📝 풀이 시험장", "🔥 오답노트 관리"])

if menu == "📁 자동 문제 은행 상태":
    st.header("📁 내장 문제 은행 관리 상태")
    if is_pdf_broken:
        st.error(f"❌ 깃허브에 {FIXED_PDF_NAME} 파일이 없거나 올바르지 않습니다.")
    else:
        st.success(f"✅ 편집본 문제집 연결 성공! (총 {total_pages_count}개 문제 적재됨)")
        
    if has_answer_pdf:
        st.success(f"✅ 해설지(answer.pdf) 연결 성공! (총 {total_answer_pages}페이지 사용 가능)")
    else:
        st.warning("⚠️ 깃허브에 해설지 answer.pdf 파일이 보이지 않습니다.")

elif menu == "📝 풀이 시험장":
    st.header("📝 수매씽 무한 랜덤 시험장")
    
    if is_pdf_broken or st.session_state.current_target_page is None:
        st.error("📁 PDF 교재 파일을 먼저 확인해 주세요.")
    else:
        file_page = st.session_state.current_target_page
        st.markdown(f"### 🎯 **현재 랜덤 출제 문항:** [ 편집 파일 내부 {file_page}번째 문제 ]")
        
        # 문제 시각화
        try:
            doc = fitz.open(FIXED_PDF_NAME)
            page = doc.load_page(file_page - 1)
            pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
            st.image(pix.tobytes("png"), use_container_width=True)
            doc.close()
        except Exception as e:
            st.error(f"❌ 문제 이미지를 로드하는 중 에러가 발생했습니다: {e}")

        st.write("")
        user_ans = st.text_input("여기에 본인이 생각한 정답을 입력하세요:", key=f"ans_{file_page}").strip()
        if user_ans:
            st.session_state.user_answer_text = user_ans

        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔍 내가 적은 정답 제출하고 해설지 확인", use_container_width=True):
                if not has_answer_pdf:
                    st.error("⚠️ 깃허브 저장소에 answer.pdf 파일이 필요합니다.")
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

        # 해설지 수동 싱크 조절 뷰어 구역
        if st.session_state.show_answer_trigger and has_answer_pdf:
            st.write("---")
            st.subheader("📖 해설지 조절 네비게이터")
            st.info(f"내가 입력한 답안: {st.session_state.user_answer_text}")
            
            current_idx = st.session_state.manual_answer_page_idx
            
            # 버튼과 슬라이더로 편집본의 정답 페이지를 직접 맞출 수 있는 장치
            col_nav1, col_nav2, col_nav3 = st.columns([1, 4, 1])
            with col_nav1:
                if st.button("⬅️ 이전 쪽 해설", use_container_width=True):
                    if current_idx > 0:
                        st.session_state.manual_answer_page_idx -= 1
                        st.rerun()
            with col_nav2:
                safe_max_val = total_answer_pages if total_answer_pages > 0 else 1
                safe_val = min(max(current_idx + 1, 1), safe_max_val)
                selected_page = st.slider(
                    "현재 표시 중인 해설지 파일의 실제 쪽수 선택", 
                    min_value=1, 
                    max_value=safe_max_val, 
                    value=safe_val
                )
                if selected_page - 1 != current_idx:
                    st.session_state.manual_answer_page_idx = selected_page - 1
                    st.rerun()
            with col_nav3:
                if st.button("다음 쪽 해설 ➡️", use_container_width=True):
                    if current_idx < total_answer_pages - 1:
                        st.session_state.manual_answer_page_idx += 1
                        st.rerun()
            
            # 최종 해설 이미지 렌더링
            try:
                ans_doc = fitz.open(ANSWER_PDF_NAME)
                ans_page = ans_doc[st.session_state.manual_answer_page_idx]
                pix_ans = ans_page.get_pixmap(matrix=fitz.Matrix(1.8, 1.8))
                st.image(
                    pix_ans.tobytes("png"), 
                    caption=f"해설지 PDF 기준 [ {st.session_state.manual_answer_page_idx + 1} / {total_answer_pages} ] 페이지 화면", 
                    use_container_width=True
                )
                ans_doc.close()
            except Exception as e:
                st.error(f"❌ 해설지 이미지를 가져오지 못했습니다: {e}")
            
            st.write("")
            st.markdown("#### 🎯 해설지를 확인하셨다면 채점을 선택해 주세요:")
            
            b1, b2 = st.columns(2)
            with b1:
                if st.button("⭕ 정답입니다! (맞춤 처리)", use_container_width=True):
                    st.session_state.history_stats["correct"] += 1
                    st.session_state.history_stats["total"] += 1
                    st.session_state.solved_count += 1
                    st.session_state.show_answer_trigger = False
                    st.session_state.user_answer_text = ""
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
                    st.session_state.current_target_page = random.randint(1, total_pages_count)
                    st.rerun()

elif menu == "🔥 오답노트 관리":
    st.header("🔥 복습이 필요한 오답 목록")
    if not st.session_state.wrong_notes:
        st.success("🎉 누적된 오답 문항이 없습니다!")
    else:
        for w_page in sorted(st.session_state.wrong_notes):
            st.warning(f"📋 복습 대상: 편집 파일 내부 {w_page}번째 문제")
            try:
                doc = fitz.open(FIXED_PDF_NAME)
                page = doc.load_page(w_page - 1)
                pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
                st.image(pix.tobytes("png"), use_container_width=True)
                doc.close()
            except:
                pass
                
            if st.button("이 문제 삭제 (마스터 완료)", key=f"del_{w_page}"):
                st.session_state.wrong_notes.remove(w_page)
                save_to_local()
                st.rerun()
            st.write("---")
      
