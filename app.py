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
if 'user_answer_text' not in st.session_state:
    st.session_state.user_answer_text = ""
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

        # 💡 [1번 패드] 대형 문제 풀이 연습장 (부분 지우개 모드 추가 버전)
        st.write("")
        st.markdown("✍️ **여기에 패드로 자유롭게 풀이를 적으세요:**")
        
        canvas_html = """
        <div style="background-color: #F8F9FA; padding: 10px; border-radius: 8px; border: 1px solid #E0E0E0; font-family: sans-serif;">
            <div style="margin-bottom: 8px; display: flex; gap: 8px; align-items: center; flex-wrap: wrap;">
                <button id="btnPen" onclick="setMode('pen')" style="padding: 6px 14px; background-color: #007BFF; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; font-size:12px;">✏️ 연필 모드</button>
                <button id="btnEraser" onclick="setMode('eraser')" style="padding: 6px 14px; background-color: #6C757D; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; font-size:12px;">🧽 부분 지우개</button>
                <button onclick="clearCanvas()" style="padding: 6px 12px; background-color: #FF4B4B; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; font-size:12px;">🗑️ 풀이 싹 지우기</button>
                <span id="modeStatus" style="color: #007BFF; font-size: 12px; font-weight: bold; margin-left: 5px;">[현재: 연필 쓰기 모드]</span>
            </div>
            <canvas id="paintCanvas" style="background-color: #FFFFFF; border: 1px solid #D3D3D3; border-radius: 4px; touch-action: none; cursor: crosshair; width: 100%; height: 280px;"></canvas>
        </div>
        <script>
            const canvas = document.getElementById('paintCanvas');
            const ctx = canvas.getContext('2d');
            const btnPen = document.getElementById('btnPen');
            const btnEraser = document.getElementById('btnEraser');
            const modeStatus = document.getElementById('modeStatus');
            
            let isDrawing = false;
            let lastX = 0; let lastY = 0;
            let currentMode = 'pen'; // 'pen' 또는 'eraser'
            
            function resizeCanvas() {
                // 캔버스 내용 보존용 임시 저장
                const tempCanvas = document.createElement('canvas');
                tempCanvas.width = canvas.width;
                tempCanvas.height = canvas.height;
                const tempCtx = tempCanvas.getContext('2d');
                tempCtx.drawImage(canvas, 0, 0);
                
                canvas.width = canvas.offsetWidth;
                canvas.height = 280;
                
                // 기존 내용 복원 및 스타일 재정의
                ctx.drawImage(tempCanvas, 0, 0);
                applyModeSettings();
            }
            
            function applyModeSettings() {
                ctx.lineCap = 'round';
                ctx.lineJoin = 'round';
                if (currentMode === 'pen') {
                    ctx.globalCompositeOperation = 'source-over';
                    ctx.strokeStyle = '#1E1E1E';
                    ctx.lineWidth = 3;
                    btnPen.style.backgroundColor = '#007BFF';
                    btnEraser.style.backgroundColor = '#6C757D';
                    modeStatus.textContent = '[현재: 연필 쓰기 모드]';
                    modeStatus.style.color = '#007BFF';
                } else {
                    // 투명 배경으로 지워지도록 compositeOperation 변경
                    ctx.globalCompositeOperation = 'destination-out';
                    ctx.lineWidth = 24; // 지우개는 굵직하게 설정
                    btnPen.style.backgroundColor = '#6C757D';
                    btnEraser.style.backgroundColor = '#E0A800';
                    modeStatus.textContent = '[현재: 부분 지우개 모드]';
                    modeStatus.style.color = '#E0A800';
                }
            }
            
            function setMode(mode) {
                currentMode = mode;
                applyModeSettings();
            }
            
            window.addEventListener('resize', resizeCanvas);
            setTimeout(resizeCanvas, 200);
            
            function getPos(e) {
                const rect = canvas.getBoundingClientRect();
                let x = (e.touches ? e.touches[0].clientX : e.clientX) - rect.left;
                let y = (e.touches ? e.touches[0].clientY : e.clientY) - rect.top;
                return { x, y };
            }
            
            canvas.addEventListener('mousedown', (e) => { isDrawing = true; const p = getPos(e); lastX = p.x; lastY = p.y; });
            canvas.addEventListener('mousemove', (e) => {
                if (!isDrawing) return; e.preventDefault(); const p = getPos(e);
                ctx.beginPath(); ctx.moveTo(lastX, lastY); ctx.lineTo(p.x, p.y); ctx.stroke();
                lastX = p.x; lastY = p.y;
            });
            window.addEventListener('mouseup', () => isDrawing = false);
            
            canvas.addEventListener('touchstart', (e) => { isDrawing = true; const p = getPos(e); lastX = p.x; lastY = p.y; }, {passive:false});
            canvas.addEventListener('touchmove', (e) => {
                if (!isDrawing) return; e.preventDefault(); const p = getPos(e);
                ctx.beginPath(); ctx.moveTo(lastX, lastY); ctx.lineTo(p.x, p.y); ctx.stroke();
                lastX = p.x; lastY = p.y;
            }, {passive:false});
            canvas.addEventListener('touchend', () => isDrawing = false);
            
            function clearCanvas() { 
                // 전체 삭제 시 잠시 연필 모드로 전환해서 밀어버린 후 복귀
                const prevComposite = ctx.globalCompositeOperation;
                ctx.globalCompositeOperation = 'destination-out';
                ctx.fillRect(0, 0, canvas.width, canvas.height);
                ctx.globalCompositeOperation = prevComposite;
            }
        </script>
        """
        components.html(canvas_html, height=360, scrolling=False)

        # 💡 [2번 패드] 안전하게 분리한 정답 입력용 필기 패드 구성
        st.write("")
        st.markdown("🎯 **최종 정답을 아래 사각형 안에 손글씨로 적으세요:**")
        
        user_ans_written = st.text_input("📝 여기에 손글씨 정답을 기재하거나 직접 타이핑하세요:", key=f"text_input_{file_page}").strip()
        if user_ans_written:
            st.session_state.user_answer_text = user_ans_written

        ans_pad_html = """
        <div style="background-color: #EBF3FF; padding: 10px; border-radius: 8px; border: 1px solid #A3C7FF; font-family: sans-serif;">
            <div style="margin-bottom: 6px; display: flex; justify-content: space-between;">
                <span style="color: #004085; font-weight: bold; font-size: 13px;">✏️ 손글씨 정답 적는 칸</span>
                <button onclick="clearAns()" style="padding: 3px 8px; background-color: #6C757D; color: white; border: none; border-radius: 4px; cursor: pointer; font-size:11px;">다시 쓰기</button>
            </div>
            <canvas id="ansCanvas" style="background-color: #FFFFFF; border: 2px dashed #7FB3FF; border-radius: 4px; touch-action: none; width: 100%; height: 110px; cursor: crosshair;"></canvas>
            <div style="color: #555; font-size: 11px; margin-top: 5px; text-align: right;">※ 패드로 정답을 자유롭게 그리신 뒤 아래 [🔍 정답 제출] 버튼을 눌러주세요!</div>
        </div>
        <script>
            const aCanvas = document.getElementById('ansCanvas');
            const aCtx = aCanvas.getContext('2d');
            
            function resizeAnsCanvas() {
                aCanvas.width = aCanvas.offsetWidth;
                aCanvas.height = 110;
                aCtx.strokeStyle = '#0056B3';
                aCtx.lineWidth = 4;
                aCtx.lineCap = 'round';
                aCtx.lineJoin = 'round';
            }
            window.addEventListener('resize', resizeAnsCanvas);
            setTimeout(resizeAnsCanvas, 200);
            
            let aDrawing = false;
            let aX = 0; let aY = 0;

            function getAPos(e) {
                const r = aCanvas.getBoundingClientRect();
                let x = (e.touches ? e.touches[0].clientX : e.clientX) - r.left;
                let y = (e.touches ? e.touches[0].clientY : e.clientY) - r.top;
                return { x, y };
            }
            
            aCanvas.addEventListener('mousedown', (e) => { aDrawing = true; const p = getAPos(e); aX = p.x; aY = p.y; });
            aCanvas.addEventListener('mousemove', (e) => {
                if (!aDrawing) return; e.preventDefault(); const p = getAPos(e);
                aCtx.beginPath(); aCtx.moveTo(aX, aY); aCtx.lineTo(p.x, p.y); aCtx.stroke();
                aX = p.x; aY = p.y;
            });
            window.addEventListener('mouseup', () => aDrawing = false);
            
            aCanvas.addEventListener('touchstart', (e) => { aDrawing = true; const p = getAPos(e); aX = p.x; aY = p.y; }, {passive:false});
            aCanvas.addEventListener('touchmove', (e) => {
                if (!aDrawing) return; e.preventDefault(); const p = getAPos(e);
                aCtx.beginPath(); aCtx.moveTo(aX, aY); aCtx.lineTo(p.x, p.y); aCtx.stroke();
                aX = p.x; aY = p.y;
            }, {passive:false});
            aCanvas.addEventListener('touchend', () => aDrawing = false);

            function clearAns() { 
                aCtx.clearRect(0, 0, aCanvas.width, aCanvas.height); 
            }
        </script>
        """
        components.html(ans_pad_html, height=170, scrolling=False)

        st.write("")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔍 정답 제출하고 해설지 즉시 보기", use_container_width=True):
                if not has_answer_pdf:
                    st.error("⚠️ 1:1 매칭된 answer.pdf 파일이 깃허브에 필요합니다.")
                else:
                    st.session_state.show_answer_trigger = True
                    st.rerun()
                    
        with c2:
            if st.button("이 문제는 패스하고 다른 문제 뽑기 ➡️", use_container_width=True):
                st.session_state.show_answer_trigger = False
                st.session_state.user_answer_text = ""
                st.session_state.current_target_page = random.randint(1, total_pages_count)
                st.rerun()

        # 정답 제출 버튼 클릭 시 하단에 해설지 즉시 출력
        if st.session_state.show_answer_trigger and has_answer_pdf:
            st.write("---")
            st.subheader("📖 1:1 매칭 해설 확인창")
            if st.session_state.user_answer_text:
                st.info(f"제출된 정답 표기: {st.session_state.user_answer_text}")
            
            # 해설지 오차 미세조정 보정 컨트롤러
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
            
            try:
                ans_doc = fitz.open(ANSWER_PDF_NAME)
                target_ans_page = (file_page - 1) + st.session_state.ans_offset
                
                if 0 <= target_ans_page < len(ans_doc):
                    ans_page = ans_doc[target_ans_page]
                    pix_ans = ans_page.get_pixmap(matrix=fitz.Matrix(1.8, 1.8))
                    st.image(pix_ans.tobytes("png"), caption=f"현재 매칭된 해설지 화면 (오프셋 반영: {target_ans_page + 1}쪽)", use_container_width=True)
                else:
                    st.error(f"❌ 설정된 해설지 페이지가 범위를 벗어났습니다. 조절 버튼을 다시 이용해 주세요.")
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
                    save_to_local()
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
            except Exception:
                pass
                
            if st.button("이 문항 복습 완료 (삭제)", key=f"del_{w_page}"):
                st.session_state.wrong_notes.remove(w_page)
                save_to_local()
                st.rerun()
            st.write("---")
