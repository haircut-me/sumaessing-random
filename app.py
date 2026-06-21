import streamlit as st
import random
import json
import os
from datetime import datetime
import fitz  # PyMuPDF
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
        except:
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
if 'user_answer_text' not in st.session_state:
    st.session_state.user_answer_text = ""

# 해설지 오차 미세조정용 변수 초기화
if 'ans_offset' not in st.session_state:
    st.session_state.ans_offset = 0

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
        st.markdown(f"### 🎯 **현재 출제 문항:** [ 발췌 파일 내 {file_page}번째 문제 ]")
        
        # 문제 이미지 출력
        try:
            doc = fitz.open(FIXED_PDF_NAME)
            page = doc.load_page(file_page - 1)
            pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
            st.image(pix.tobytes("png"), use_container_width=True)
            doc.close()
        except Exception as e:
            st.error(f"❌ 문제 스캔 이미지를 로드하지 못했습니다: {e}")

        # 💡 [독립형 웹 표준 스케치패드 구현] 스트림릿 노드와 완벽히 격리되어 에러를 원천 차단합니다.
        st.write("")
        st.markdown("✍️ **여기에 패드로 자유롭게 풀이를 적으세요:**")
        
        canvas_html = f"""
        <div style="background-color: #F8F9FA; padding: 10px; border-radius: 8px; border: 1px solid #E0E0E0; font-family: sans-serif;">
            <div style="margin-bottom: 8px; display: flex; gap: 10px;">
                <button onclick="clearCanvas()" style="padding: 6px 12px; background-color: #FF4B4B; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold;">🗑️ 전체 지우기</button>
                <span style="color: #666; font-size: 13px; margin-top: 5px;">※ 펜/손가락 필기 지원 (문제 변경 시 자동 리셋)</span>
            </div>
            <canvas id="paintCanvas_{file_page}" style="background-color: #FFFFFF; border: 1px solid #D3D3D3; border-radius: 4px; touch-action: none; cursor: crosshair;"></canvas>
        </div>
        <script>
            const canvas = document.getElementById('paintCanvas_{file_page}');
            const ctx = canvas.getContext('2d');
            
            // 컨테이너 크기에 맞춰 캔버스 해상도 유동적 설정
            canvas.width = window.innerWidth - 60;
            canvas.height = 320;
            
            ctx.strokeStyle = '#1E1E1E';
            ctx.lineWidth = 3;
            ctx.lineCap = 'round';
            ctx.lineJoin = 'round';
            
            let isDrawing = false;
            let lastX = 0;
            let lastY = 0;
            
            function getPos(e) {{
                let x, y;
                const rect = canvas.getBoundingClientRect();
                if (e.touches && e.touches.length > 0) {{
                    x = e.touches[0].clientX - rect.left;
                    y = e.touches[0].clientY - rect.top;
                }} else {{
                    x = e.clientX - rect.left;
                    y = e.clientY - rect.top;
                }}
                return {{ x, y }};
            }}
            
            function startDrawing(e) {{
                isDrawing = true;
                const pos = getPos(e);
                lastX = pos.x;
                lastY = pos.y;
            }}
            
            function draw(e) {{
                if (!isDrawing) return;
                e.preventDefault();
                const pos = getPos(e);
                ctx.beginPath();
                ctx.moveTo(lastX, lastY);
                ctx.lineTo(pos.x, pos.y);
                ctx.stroke();
                lastX = pos.x;
                lastY = pos.y;
            }}
            
            function stopDrawing() {{
                isDrawing = false;
            }}
            
            function clearCanvas() {{
                ctx.clearRect(0, 0, canvas.width, canvas.height);
            }}
            
            // 마우스 이벤트
            canvas.addEventListener('mousedown', startDrawing);
            canvas.addEventListener('mousemove', draw);
            canvas.addEventListener('mouseup', stopDrawing);
            canvas.addEventListener('mouseout', stopDrawing);
            
            // 터치 이벤트 (패드/모바일 완벽 지원)
            canvas.addEventListener('touchstart', startDrawing, {{ passive: false }});
            canvas.addEventListener('touchmove', draw, {{ passive: false }});
            canvas.addEventListener('touchend', stopDrawing);
        </script>
        """
        components.html(canvas_html, height=410, scrolling=False)

        st.write("")
        user_ans = st.text_input("여기에 본인이 생각한 정답을 입력하세요:", key=f"ans_{file_page}").strip()
        if user_ans:
            st.session_state.user_answer_text = user_ans

        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔍 정답 제출하고 해설지 즉시 보기", use_container_width=True):
                if not has_answer_pdf:
                    st.error("⚠️ 1:1 매칭된 answer.pdf 파일이 깃허브에 필요합니다.")
                elif not user_ans:
                    st.warning("⚠️ 정답 칸에 본인의 답안을 먼저 작성해 주세요!")
                else:
                    st.session_state.show_answer_trigger = True
                    st.rerun()
                    
        with c2:
            if st.button("이 문제는 패스하고 다른 문제 뽑기 ➡️", use_container_width=True):
                st.session_state.show_answer_trigger = False
                st.session_state.user_answer_text = ""
                st.session_state.current_target_page = random.randint(1, total_pages_count)
                st.rerun()

        # 정답 제출 버튼 클릭 시 하단에 1:1 매칭된 해설지 즉시 출력
        if st.session_state.show_answer_trigger and has_answer_pdf:
            st.write("---")
            st.subheader("📖 1:1 매칭 해설 확인창")
            st.info(f"내가 작성한 답안: {st.session_state.user_answer_text}")
            
            # 해설지와 문제지 페이지 밀림 보정 컨트롤러
            st.markdown("🔧 **해설지 페이지 번호가 맞지 않으면 아래 버튼으로 조절하세요:**")
            move_col1, move_col2, move_col3 = st.columns([1, 2, 1])
            with move_col1:
                if st.button("⬅️ 해설지 1장 앞으로", use_container_width=True):
                    st.session_state.ans_offset -= 1
                    st.rerun()
            with move_col2:
                st.markdown(f"<p style='text-align: center; font-weight: bold; margin-top: 6px;'>현재 해설지 조정 값: {st.session_state.ans_offset} 장</p>", unsafe_allow_html=True)
            with move_col3:
                if st.button("해설지 1장 뒤로 ➡️", use_container_width=True):
                    st.session_state.ans_offset += 1
                    st.rerun()
            
            # 계산된 오프셋 값을 인덱스에 반영
            try:
                ans_doc = fitz.open(ANSWER_PDF_NAME)
                target_ans_page = (file_page - 1) + st.session_state.ans_offset
                
                if 0 <= target_ans_page < len(ans_doc):
                    ans_page = ans_doc[target_ans_page]
                    pix_ans = ans_page.get_pixmap(matrix=fitz.Matrix(1.8, 1.8))
                    st.image(pix_ans.tobytes("png"), caption=f"현재 매칭된 해설지 화면 (오프셋 반영: {target_ans_page + 1}쪽)", use_container_width=True)
                else:
                    st.error(f"❌ 설정된 해설지 페이지({target_ans_page + 1}쪽)가 파일의 실제 범위(1~{len(ans_doc)}쪽)를 벗어났습니다. 조절 버튼을 다시 이용해 주세요.")
                ans_doc.close()
            except Exception as e:
                st.error(f"❌ 해설지 화면을 불러오지 못했습니다: {e}")
            
            st.write("")
            st.markdown("#### 🎯 해설을 확인하신 후 채점 버튼을 눌러주세요:")
            
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

# 7. [메뉴 3] 오답노트 관리 구역
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
