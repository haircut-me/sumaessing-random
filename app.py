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

# 1. 기본 페이지 설정 및 스타일 초기화
st.set_page_config(page_title="수매씽 무한 랜덤 문제 은행", layout="wide")

# 2. 세션 상태 정의 및 초기화
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

# 3. PDF 파일 존재 유무 및 파일 정상 여부 확인
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

# 4. 사이드바 구성
st.sidebar.title("🎮 수매씽 무한 랜덤 문제 은행")
st.sidebar.markdown(f"### 🔥 연속 학습일: `{st.session_state.streak}일째`")
st.sidebar.markdown(f"### 🎯 오늘 푼 문항수: `{st.session_state.solved_count}개`")
menu = st.sidebar.radio("메뉴 이동", ["📁 자동 문제 은행 상태", "📝 풀이 시험장", "🔥 오답노트 관리"])

# 5. [메뉴 1] 자동 문제 은행 상태 관리 구역
if menu == "📁 자동 문제 은행 상태":
    st.header("📁 내장 문제 은행 관리 상태")
    if is_pdf_broken:
        st.error(f"❌ 깃허브에 {FIXED_PDF_NAME} 파일이 없거나 올바르지 않습니다.")
    else:
        st.success(f"✅ 수매씽 문제집 연결 성공! (총 {total_pages_count}페이지)")
        
    if has_answer_pdf:
        st.success(f"✅ 해설지(answer.pdf) 연결 성공! (총 {total_answer_pages}페이지)")
    else:
        st.warning("⚠️ 깃허브에 해설지 answer.pdf 파일이 아직 보이지 않습니다.")

# 6. [메뉴 2] 핵심 랜덤 문제 풀이 시험장 구역
elif menu == "📝 풀이 시험장":
    st.header("📝 수매씽 무한 랜덤 시험장")
    
    if is_pdf_broken or st.session_state.current_target_page is None:
        st.error("📁 PDF 교재 상태를 먼저 확인해 주세요.")
    else:
        target_page = st.session_state.current_target_page
        st.markdown(f"### 🎯 **현재 랜덤 출제 범위:** [ 원본 {target_page} 페이지 ]")
        
        # 6-1. 문제 이미지 화면 렌더링
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
        
        # 6-2. 정답 입력 창
        user_ans = st.text_input("여기에 본인이 생각한 정답을 입력하세요:", key=f"ans_{target_page}").strip()
        if user_ans:
            st.session_state.user_answer_text = user_ans

        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔍 내가 적은 정답 제출하고 해설지 보기", use_container_width=True):
                if not has_answer_pdf:
                    st.error("⚠️ 깃허브 저장소에 answer.pdf 파일이 필요합니다.")
                elif not user_ans:
                    st.warning("⚠️ 정답 칸에 먼저 답안을 작성해 주세요!")
                else:
                    st.session_state.show_answer_trigger = True
                    
                    # 최초 제출 시 시스템이 검색을 통해 가장 근접한 해설지 페이지 인덱스 자동 추정
                    best_idx = 0
                    try:
                        ans_doc = fitz.open(ANSWER_PDF_NAME)
                        page_pattern = str(target_page)
                        for p_idx in range(len(ans_doc)):
                            if page_pattern in ans_doc[p_idx].get_text("text"):
                                best_idx = p_idx
                                break
                        ans_doc.close()
                    except:
                        pass
                    
                    st.session_state.manual_answer_page_idx = best_idx
                    st.rerun()
                    
        with c2:
            if st.button("이 문제는 패스하고 다른 문제 뽑기 ➡️", use_container_width=True):
                st.session_state.show_answer_trigger = False
                st.session_state.user_answer_text = ""
                st.session_state.current_target_page = random.randint(1, total_pages_count)
                st.rerun()

        # 6-3. [Trigger 활성화 시 작동] 하단 실시간 해설지 뷰어 및 수동 조절 창 생성
        if st.session_state.show_answer_trigger and has_answer_pdf:
            st.write("---")
            st.subheader("📖 해설지 확인 및 수동 조절창")
            st.info(f"내가 입력한 답안: {st.session_state.user_answer_text}")
            
            current_idx = st.session_state.manual_answer_page_idx
            
            # 해설 페이지를 유저가 직접 싱크를 맞춰 조절할 수 있는 네비게이터 컨트롤러
            col_nav1, col_nav2, col_nav3 = st.columns([1, 4, 1])
            with col_nav1:
                if st.button("⬅️ 이전 쪽 해설", use_container_width=True):
                    if current_idx > 0:
                        st.session_state.manual_answer_page_idx -= 1
                        st.rerun()
            with col_nav2:
                # 안전한 인덱스 바인딩 보장 범위 설정
                safe_max_val = total_answer_pages if total_answer_pages > 0 else 1
                safe_val = min(max(current_idx + 1, 1), safe_max_val)
                selected_page = st.slider(
                    "해설지 PDF 내부 실제 파일 쪽수 선택", 
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
            
            # 선택한 해설지 인덱스 기반으로 이미지 렌더링
            try:
                ans_doc = fitz.open(ANSWER_PDF_NAME)
                ans_page = ans_doc[st.session_state.manual_answer_page_idx]
                pix_ans = ans_page.get_pixmap(matrix=fitz.Matrix(1.8, 1.8))
                st.image(
                    pix_ans.tobytes("png"), 
                    caption=f"해설지 PDF의 [ {st.session_state.manual_answer_page_idx + 1} / {total_answer_pages} ] 페이지 화면", 
                    use_container_width=True
                )
                ans_doc.close()
            except Exception as e:
                st.error(f"❌ 해설지 이미지를 불러오는 과정에서 오류가 발생했습니다: {e}")
            
            st.write("")
            st.markdown("#### 🎯 해설지를 보고 직접 채점해 주세요:")
            
            # 유저의 최종 수동 판단 채점 단추
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
                    if target_page not in st.session_state.wrong_notes:
                        st.session_state.wrong_notes.append(target_page)
                    save_to_local()
                    st.session_state.show_answer_trigger = False
                    st.session_state.user_answer_text = ""
                    st.session_state.current_target_page = random.randint(1, total_pages_count)
                    st.rerun()

# 7. [메뉴 3] 누적 오답노트 관리 구역
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
                st.rerun()
            st.write("---")
