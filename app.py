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

# 1. 페이지 설정
st.set_page_config(page_title="수매씽 무한 랜덤 문제 은행", layout="wide")

# 2. 세션 상태 안전하게 정의 및 초기화
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

# 3. 파일 검증 규칙 적용
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

# 4. 사이드바 인터페이스 구성
st.sidebar.title("🎮 수매씽 랜덤 문제 은행")
st.sidebar.markdown(f"### 🔥 연속 학습일: `{st.session_state.streak}일째`")
st.sidebar.markdown(f"### 🎯 오늘 푼 문항수: `{st.session_state.solved_count}개`")
menu = st.sidebar.radio("메뉴 이동", ["📁 자동 문제 은행 상태", "📝 풀이 시험장", "🔥 오답노트 관리"])

# 5. [메뉴 1] 문제 파일 상태 점검
if menu == "📁 자동 문제 은행 상태":
    st.header("📁 내장 문제 은행 관리 상태")
    if is_pdf_broken:
        st.error(f"❌ 깃허브 저장소에 {FIXED_PDF_NAME} 파일이 없거나 유효하지 않습니다.")
    else:
        st.success(f"✅ 편집본 문제집 연결 성공! (총 {total_pages_count}개의 엄선된 문항 적재 완료)")
        
    if has_answer_pdf:
        st.success(f"✅ 전체 해설지(answer.pdf) 연결 성공! (총 {total_answer_pages}페이지 탐색 가능)")
    else:
        st.warning("⚠️ 깃허브 저장소에 해설지 answer.pdf 파일이 발견되지 않았습니다.")

# 6. [메뉴 2] 랜덤 문제 풀이 및 수동 정답 대조 시험장
elif menu == "📝 풀이 시험장":
    st.header("📝 수매씽 무한 랜덤 시험장")
    
    if is_pdf_broken or st.session_state.current_target_page is None:
        st.error("📁 PDF 파일 로드 상태를 확인해 주세요.")
    else:
        file_page = st.session_state.current_target_page
        st.markdown(f"### 🎯 **현재 랜덤 출제 범위:** [ 발췌 파일 내 {file_page}번째 문항 ]")
        
        # 문제 화면 출력
        try:
            doc = fitz.open(FIXED_PDF_NAME)
            page = doc.load_page(file_page - 1)
            pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
            st.image(pix.tobytes("png"), use_container_width=True)
            doc.close()
        except Exception as e:
            st.error(f"❌ 문제 이미지를 불러오는 중 오류가 발생했습니다: {e}")

        st.write("")
        user_ans = st.text_input("여기에 본인이 생각한 정답을 입력하세요:", key=f"ans_{file_page}").strip()
        if user_ans:
            st.session_state.user_answer_text = user_ans

        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔍 내가 적은 정답 제출하고 해설지 확인", use_container_width=True):
                if not has_answer_pdf:
                    st.error("⚠️ 정답 확인을 위해 깃허브에 answer.pdf 파일이 필요합니다.")
                elif not user_ans:
                    st.warning("⚠️ 정답 칸에 답안을 먼저 작성한 뒤 제출해 주세요.")
                else:
                    st.session_state.show_answer_trigger = True
                    st.rerun()
                    
        with c2:
            if st.button("이 문제는 패스하고 다른 문제 뽑기 ➡️", use_container_width=True):
                st.session_state.show_answer_trigger = False
                st.session_state.user_answer_text = ""
                st.session_state.current_target_page = random.randint(1, total_pages_count)
                st.rerun()

        # 해설지 완전 수동 네비게이터 작동 파트
        if st.session_state.show_answer_trigger and has_answer_pdf:
            st.write("---")
            st.subheader("📖 해설지 수동 매칭 네비게이터")
            st.info(f"내가 작성한 답안: {st.session_state.user_answer_text}")
            
            current_idx = st.session_state.manual_answer_page_idx
            
            # 페이지 제어 버튼 및 슬라이더 UI
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
                    "문제가 속한 원본 책 기준의 해설지 쪽수 선택", 
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
            
            # 지정된 인덱스의 해설지 화면 출력
            try:
                ans_doc = fitz.open(ANSWER_PDF_NAME)
                ans_page = ans_doc[st.session_state.manual_answer_page_idx]
                pix_ans = ans_page.get_pixmap(matrix=fitz.Matrix(1.8, 1.8))
                st.image(
                    pix_ans.tobytes("png"), 
                    caption=f"해설지 파일 기준 [ {st.session_state.manual_answer_page_idx + 1} / {total_answer_pages} ] 페이지", 
                    use_container_width=True
                )
                ans_doc.close()
            except Exception as e:
                st.error(f"❌ 해설지 화면을 렌더링하는 데 실패했습니다: {e}")
            
            st.write("")
            st.markdown("#### 🎯 해설지와 대조하여 직접 채점을 완료해 주세요:")
            
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
                if st.button("❌ 틀렸습니다... (오답노트 저장)", use_container_width=True):
                    st.session_state.history_stats["total"] += 1
                    st.session_state.solved_count += 1
                    if file_page not in st.session_state.wrong_notes:
                        st.session_state.wrong_notes.append(file_page)
                    save_to_local()
                    st.session_state.show_answer_trigger = False
                    st.session_state.user_answer_text = ""
                    st.session_state.current_target_page = random.randint(1, total_pages_count)
                    st.rerun()

# 7. [메뉴 3] 오답 관리 구역
elif menu == "🔥 오답노트 관리":
    st.header("🔥 복습이 필요한 오답 목록")
    if not st.session_state.wrong_notes:
        st.success("🎉 현재 보관된 오답 문항이 없습니다!")
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
