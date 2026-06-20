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
        st.success("✅ 스마트 정밀 매칭형 정답지(answer.pdf) 연결 성공!")
    else:
        st.warning("⚠️ 깃허브에 자동 채점용 `answer.pdf` 파일이 아직 보이지 않습니다.")

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

        if st.session_state.scoring_result is not None:
            if st.session_state.scoring_result == "정답":
                st.success("🎉 정답입니다! 아주 잘하셨어요!")
            elif st.session_state.scoring_result == "오답":
                st.error("❌ 아쉬워요! 틀린 풀이이거나 다른 답입니다. 오답노트에 보관되었습니다.")
            elif st.session_state.scoring_result == "탐색실패":
                st.info("ℹ️ 정답지에서 해당 페이지 구역을 찾지 못했습니다. 아래 '패스' 버튼을 눌러주세요.")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("💯 정답 제출 및 실시간 채점", use_container_width=True):
                if not has_answer_pdf:
                    st.error("⚠️ 채점용 `answer.pdf` 파일이 깃허브 저장소에 존재하지 않습니다.")
                elif not user_ans:
                    st.warning("⚠️ 정답 칸에 정답을 먼저 적어주세요!")
                else:
                    try:
                        ans_doc = fitz.open(ANSWER_PDF_NAME)
                        cleaned_user_ans = user_ans.replace(" ", "")
                        
                        # 객관식 기호 변환 배열
                        circle_numbers = ["①", "②", "③", "④", "⑤"]
                        user_circle = ""
                        if cleaned_user_ans.isdigit() and 1 <= int(cleaned_user_ans) <= 5:
                            user_circle = circle_numbers[int(cleaned_user_ans) - 1]
                        
                        is_correct = False
                        found_page_zone = False
                        
                        # 1단계 탐색: 정답지 안에서 "빠른정답/바른정답/정답" 코너(표 형태)가 밀집된 곳 우선 검색
                        # 해당 구역은 단순 텍스트 매칭의 오류를 최소화합니다.
                        for p_idx in range(len(ans_doc)):
                            raw_text = ans_doc[p_idx].get_text("text")
                            # '정답'이나 '빠른' 단어가 포함된 페이지 우선 타겟팅
                            if "정답" in raw_text or "바른" in raw_text:
                                text_lines = [line.strip().replace(" ", "") for line in raw_text.split("\n") if line.strip()]
                                combined_text = "".join(text_lines)
                                
                                # 예: "72페이지 쪽 번호 뒤에 바로 정답 기호가 오는지 정밀 검색"
                                # 72번 문항 혹은 72쪽 뒤 15글자 내외 근방만 정밀 컷팅
                                page_pos = combined_text.find(str(target_page))
                                if page_pos != -1:
                                    found_page_zone = True
                                    snippet = combined_text[page_pos:page_pos+20] # 쪽 번호 주변 데이터만 추출
                                    if cleaned_user_ans in snippet or (user_circle and user_circle in snippet):
                                        is_correct = True
                                        break
                        
                        # 2단계 탐색 (해설지 본문 스캔): 본문 해설 단락 내부 매칭 구조 고도화
                        if not is_correct:
                            for p_idx in range(len(ans_doc)):
                                raw_text = ans_doc[p_idx].get_text("text")
                                if str(target_page) in raw_text:
                                    found_page_zone = True
                                    # 줄 바꿈을 보존한 상태에서 각 문항의 최종 정답 행만 추적
                                    lines = raw_text.split("\n")
                                    for line in lines:
                                        cleaned_line = line.replace(" ", "")
                                        # 유저 정답이 단독으로 명확히 매칭되거나 정답 선지에 포함되는지 필터링
                                        # 단순히 아무 글자에나 매칭되는 현상을 막기 위해 '따라서', '정답은', '🛒' 등의 컨텍스트와 매칭 강도 강화
                                        if cleaned_user_ans in cleaned_line or (user_circle and user_circle in cleaned_line):
                                            # 단순 연산 과정의 숫자 기호가 아닐 확률 검증 (기호나 정답 명시 텍스트 주변부 체크)
                                            if any(keyword in cleaned_line for keyword in ["정답", "따라서", "🎯", "①", "②", "③", "④", "⑤", "="]):
                                                is_correct = True
                                                break
                                if is_correct:
                                    break
                                    
                        ans_doc.close()
                        
                        if is_correct:
                            st.session_state.scoring_result = "정답"
                            st.session_state.history_stats["correct"] += 1
                            st.session_state.history_stats["total"] += 1
                            st.rerun()
                        elif found_page_zone:
                            st.session_state.scoring_result = "오답"
                            st.session_state.history_stats["total"] += 1
                            if target_page not in st.session_state.wrong_notes:
                                st.session_state.wrong_notes.append(target_page)
                            save_to_local()
                            st.rerun()
                        else:
                            st.session_state.scoring_result = "탐색실패"
                            st.rerun()
                            
                    except Exception as e:
                        st.error(f" 정답지 파일 검증 오류: {e}")
                    
        with c2:
            if st.button("이 문제는 넘어가기 (패스)", use_container_width=True):
                st.session_state.scoring_result = None
                st.session_state.current_target_page = random.randint(1, total_pages_count)
                st.rerun()

        st.write("---")
        if st.button("다음 랜덤 문제 뽑기 ➡️", use_container_width=True):
            if total_pages_count > 0:
                st.session_state.solved_count += 1
                st.session_state.scoring_result = None
                st.session_state.current_target_page = random.randint(1, total_pages_count)
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
