"""
Utility functions for the AI Interview Coach
Handles helper functions, formatting, and voice features
"""

import streamlit as st
import json
import re
from datetime import datetime
import random
import base64
from typing import List, Dict, Any, Optional
import os
from dotenv import load_dotenv

from google import genai

import time

load_dotenv(override=True)
gemini_api_key = st.getenv("GEMINI_API_KEY")
client = None
if gemini_api_key:
    client = genai.Client(api_key=gemini_api_key)
GEMINI_MODEL = "models/gemini-2.5-flash"
GEMINI_FALLBACK = "models/gemini-2.5-pro"

def call_gemini(prompt: str, feature_name: str = "Unknown") -> Optional[str]:
    """
    Safely calls Gemini API using the new google-genai SDK.
    """
    if not client:
        return None
        
    # Rate limit protection
    time.sleep(0.5)
        
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )
        print(f"[Gemini] Called successfully | Model: {GEMINI_MODEL} | Feature: {feature_name}")
        return response.text.strip()
    except Exception as e:
        print(f"[Gemini] {GEMINI_MODEL} failed for {feature_name}: {e}. Trying fallback...")
        try:
            response = client.models.generate_content(
                model=GEMINI_FALLBACK,
                contents=prompt
            )
            print(f"[Gemini] Called successfully | Model: {GEMINI_FALLBACK} | Feature: {feature_name}")
            return response.text.strip()
        except Exception as fallback_e:
            print(f"Gemini API Error for {feature_name}: {fallback_e}")
            return None

# Try to import voice libraries (optional)
try:
    import speech_recognition as sr
    import pyttsx3
    VOICE_AVAILABLE = True
except ImportError:
    VOICE_AVAILABLE = False

# =============================================================================
# ANIMATION FUNCTIONS
# =============================================================================

def get_typing_animation():
    """Returns CSS for typing animation"""
    return """
    <style>
    .typing-indicator {
        display: flex;
        align-items: center;
        margin: 10px 0;
    }
    .typing-indicator span {
        height: 10px;
        width: 10px;
        background: #667eea;
        border-radius: 50%;
        display: inline-block;
        margin: 0 2px;
        animation: typing 1.5s infinite ease-in-out;
    }
    .typing-indicator span:nth-child(2) {
        animation-delay: 0.2s;
    }
    .typing-indicator span:nth-child(3) {
        animation-delay: 0.4s;
    }
    @keyframes typing {
        0% { transform: translateY(0); }
        50% { transform: translateY(-10px); }
        100% { transform: translateY(0); }
    }
    
    .pulse {
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    .rotate {
        animation: rotate 2s linear infinite;
    }
    @keyframes rotate {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    
    .float {
        animation: float 3s ease-in-out infinite;
    }
    @keyframes float {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
        100% { transform: translateY(0px); }
    }
    
    .glow {
        animation: glow 2s ease-in-out infinite;
    }
    @keyframes glow {
        0% { box-shadow: 0 0 5px #667eea; }
        50% { box-shadow: 0 0 20px #667eea; }
        100% { box-shadow: 0 0 5px #667eea; }
    }
    
    .fade-in {
        animation: fadeIn 1s ease-in;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .slide-in {
        animation: slideIn 0.5s ease-out;
    }
    @keyframes slideIn {
        from { transform: translateX(-20px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    .bounce {
        animation: bounce 2s infinite;
    }
    @keyframes bounce {
        0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
        40% { transform: translateY(-20px); }
        60% { transform: translateY(-10px); }
    }
    </style>
    """

def get_confetti_animation():
    """Returns JavaScript for confetti animation"""
    return """
    <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1"></script>
    <script>
    function launchConfetti() {
        confetti({
            particleCount: 100,
            spread: 70,
            origin: { y: 0.6 }
        });
    }
    function launchBigConfetti() {
        confetti({
            particleCount: 150,
            spread: 100,
            origin: { y: 0.6 }
        });
        confetti({
            particleCount: 150,
            spread: 100,
            origin: { y: 0.6, x: 0.2 }
        });
        confetti({
            particleCount: 150,
            spread: 100,
            origin: { y: 0.6, x: 0.8 }
        });
    }
    </script>
    """

def get_robot_avatar(emotion="neutral"):
    """
    Returns a polished AI interviewer avatar SVG.
    Emotions: 'neutral' | 'happy' | 'thinking' | 'listening'
    """
    # Base colours per emotion
    colours = {
        "neutral":   ("#667eea", "#764ba2", "float"),
        "happy":     ("#10b981", "#059669", "bounce"),
        "thinking":  ("#f59e0b", "#d97706", "pulse"),
        "listening": ("#ea4335", "#c62828", "pulse"),
    }
    c1, c2, anim = colours.get(emotion, colours["neutral"])

    return f"""
    <div style="display:flex;flex-direction:column;align-items:center;gap:8px;">
      <svg width="130" height="130" viewBox="0 0 130 130" class="{anim}"
           xmlns="http://www.w3.org/2000/svg">
        <defs>
          <linearGradient id="bg_grad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%"  stop-color="{c1}" stop-opacity="0.25"/>
            <stop offset="100%" stop-color="{c2}" stop-opacity="0.15"/>
          </linearGradient>
          <linearGradient id="body_grad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%"  stop-color="{c1}"/>
            <stop offset="100%" stop-color="{c2}"/>
          </linearGradient>
        </defs>
        <!-- Background glow circle -->
        <circle cx="65" cy="65" r="58" fill="url(#bg_grad)" />
        <!-- Head -->
        <rect x="32" y="28" width="66" height="56" rx="16" ry="16" fill="url(#body_grad)" opacity="0.95"/>
        <!-- Visor -->
        <rect x="38" y="34" width="54" height="30" rx="8" ry="8" fill="#0f172a" opacity="0.85"/>
        <!-- Eyes -->
        <circle cx="52" cy="49" r="7" fill="{c1}" opacity="0.9"/>
        <circle cx="78" cy="49" r="7" fill="{c1}" opacity="0.9"/>
        <circle cx="54" cy="47" r="2.5" fill="white" opacity="0.8"/>
        <circle cx="80" cy="47" r="2.5" fill="white" opacity="0.8"/>
        <!-- Mouth / speaker -->
        <rect x="46" y="73" width="38" height="6" rx="3" fill="{c1}" opacity="0.7"/>
        <!-- Antenna -->
        <line x1="65" y1="28" x2="65" y2="14" stroke="{c1}" stroke-width="3"
              stroke-linecap="round"/>
        <circle cx="65" cy="12" r="5" fill="{c1}">
          <animate attributeName="opacity" values="1;0.3;1" dur="1.2s" repeatCount="indefinite"/>
        </circle>
        <!-- Shoulders / body stub -->
        <rect x="24" y="84" width="82" height="20" rx="10" fill="url(#body_grad)" opacity="0.6"/>
      </svg>
    </div>
    """

def get_loading_spinner():
    """Returns loading spinner HTML"""
    return """
    <div style="display: flex; justify-content: center; align-items: center; margin: 20px 0;">
        <div class="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
        </div>
    </div>
    """

def get_progress_ring(percentage, size=100):
    """Returns a progress ring SVG"""
    return f"""
    <svg width="{size}" height="{size}" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r="40" fill="none" stroke="#e2e8f0" stroke-width="8"/>
        <circle cx="50" cy="50" r="40" fill="none" stroke="#667eea" stroke-width="8"
                stroke-dasharray="251.2" 
                stroke-dashoffset="{251.2 - (251.2 * percentage / 100)}"
                transform="rotate(-90 50 50)">
            <animate attributeName="stroke-dashoffset" 
                     values="{251.2};{251.2 - (251.2 * percentage / 100)}" 
                     dur="1s" fill="freeze"/>
        </circle>
        <text x="50" y="55" text-anchor="middle" fill="#667eea" font-size="20" font-weight="bold">
            {percentage}%
        </text>
    </svg>
    """

# =============================================================================
# ORIGINAL UTILITY FUNCTIONS
# =============================================================================

def get_difficulty_level(question):
    """Extract difficulty level from question"""
    if isinstance(question, dict):
        # Check multiple possible keys for difficulty
        difficulty = question.get('difficulty_level') or question.get('difficulty') or 'beginner'
        return difficulty
    return 'beginner'

def format_feedback(feedback):
    """Format feedback for display with animations"""
    score = feedback.get('score', 0)
    if score >= 7:
        score_class = "score-high"
        icon = "🎉"
    elif score >= 5:
        score_class = "score-medium"
        icon = "📊"
    else:
        score_class = "score-low"
        icon = "💪"
    
    html = f"""
    <div class="feedback-box fade-in">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem;">
            <h4 style="margin: 0;">{icon} Score: <span class="{score_class}">{feedback['score']}/10</span></h4>
            <div class="glow" style="width: 40px; height: 40px; border-radius: 50%; background: #667eea20;"></div>
        </div>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem;">
            <div style="background: #d1fae5; padding: 1rem; border-radius: 10px;" class="slide-in">
                <h5 style="color: #065f46; margin: 0 0 0.5rem 0;">✅ Strengths:</h5>
                <ul style="margin: 0; padding-left: 1.2rem;">
    """
    
    for strength in feedback.get('strengths', []):
        html += f"<li style='color: #065f46;'>{strength}</li>"
    
    html += """
                </ul>
            </div>
            
            <div style="background: #fee2e2; padding: 1rem; border-radius: 10px;" class="slide-in">
                <h5 style="color: #991b1b; margin: 0 0 0.5rem 0;">🔧 Areas to Improve:</h5>
                <ul style="margin: 0; padding-left: 1.2rem;">
    """
    
    for weakness in feedback.get('weaknesses', []):
        html += f"<li style='color: #991b1b;'>{weakness}</li>"
    
    html += """
                </ul>
            </div>
        </div>
        
        <div style="background: #e0e7ff; padding: 1rem; border-radius: 10px; margin: 1rem 0;" class="fade-in">
            <h5 style="color: #1e40af; margin: 0 0 0.5rem 0;">💡 Suggestions:</h5>
            <ul style="margin: 0; padding-left: 1.2rem;">
    """
    
    for suggestion in feedback.get('suggestions', []):
        html += f"<li style='color: #1e40af;'>{suggestion}</li>"
    
    html += """
            </ul>
        </div>
        
        <div style="background: #f3e8ff; padding: 1rem; border-radius: 10px;" class="fade-in">
            <h5 style="color: #6b21a8; margin: 0 0 0.5rem 0;">📝 Ideal Answer Should Include:</h5>
            <ul style="margin: 0; padding-left: 1.2rem;">
    """
    
    for point in feedback.get('ideal_answer', {}).get('key_points', []):
        html += f"<li style='color: #6b21a8;'>{point}</li>"
    
    html += """
            </ul>
    """
    
    if feedback.get('ideal_answer', {}).get('example'):
        html += f"""
            <div style="background: #1e293b; padding: 1rem; border-radius: 10px; margin-top: 1rem;">
                <pre style="color: #a5f3fc; margin: 0; font-family: 'Courier New', monospace;"><code>{feedback['ideal_answer']['example']}</code></pre>
            </div>
        """
    
    html += """
        </div>
    </div>
    """
    
    return html

def speech_to_text(audio_bytes: bytes) -> str | None:
    """
    Convert raw audio bytes (WAV / PCM from audio-recorder-streamlit)
    to a text string using the Google Speech Recognition API.

    Returns:
        str  — transcribed text, or
        None — if recognition failed (error already displayed to user)
    """
    if not audio_bytes:
        return None
    try:
        import speech_recognition as sr
        from io import BytesIO

        recognizer = sr.Recognizer()
        # Adjust sensitivity for background noise
        recognizer.energy_threshold = 300
        recognizer.dynamic_energy_threshold = True

        audio_file = BytesIO(audio_bytes)
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)

        text = recognizer.recognize_google(audio_data)
        return text.strip()

    except sr.UnknownValueError:
        # Silence or unintelligible speech
        st.warning(
            "⚠️ Could not understand your answer. "
            "Please speak clearly, avoid background noise, or type below."
        )
        return None
    except sr.RequestError as req_err:
        # Network / API error
        st.error(
            f"❌ Speech recognition service unavailable: {req_err}. "
            "Please check your internet connection or type your answer."
        )
        return None
    except Exception as generic_err:
        st.error(f"❌ Transcription error: {generic_err}")
        return None


import edge_tts
import asyncio
import tempfile
import os

VOICE_NAME = "en-US-JennyNeural"

async def _generate_tts_async(text: str, voice: str) -> bytes:
    communicate = edge_tts.Communicate(text, voice)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
        temp_path = f.name
    await communicate.save(temp_path)
    with open(temp_path, "rb") as f:
        audio_bytes = f.read()
    os.unlink(temp_path)
    return audio_bytes

def text_to_speech_autoplay(text: str) -> None:
    if not text or not text.strip():
        return
        
    cache_key = f"tts_cache_{hash(text)}"
    if cache_key in st.session_state:
        b64 = st.session_state[cache_key]
        audio_html = f"""
            <audio autoplay>
                <source src="data:audio/mp3;base64,{b64}" type="audio/mpeg">
            </audio>
        """
        st.components.v1.html(audio_html, height=0)
        return

    voice = st.session_state.get("selected_voice", VOICE_NAME)
    try:
        audio_bytes = asyncio.run(_generate_tts_async(text, voice))
        b64 = base64.b64encode(audio_bytes).decode()
        st.session_state[cache_key] = b64
        audio_html = f"""
            <audio autoplay>
                <source src="data:audio/mp3;base64,{b64}" type="audio/mpeg">
            </audio>
        """
        st.components.v1.html(audio_html, height=0)
        print(f"[TTS] edge-tts success | Voice: {voice}")
    except Exception as e:
        print(f"[TTS] edge-tts failed: {e} | Falling back to gTTS...")
        try:
            from gtts import gTTS
            import io
            tts = gTTS(text=text, lang='en')
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            b64 = base64.b64encode(fp.read()).decode()
            st.session_state[cache_key] = b64
            audio_html = f"""
                <audio autoplay>
                    <source src="data:audio/mp3;base64,{b64}" type="audio/mpeg">
                </audio>
            """
            st.components.v1.html(audio_html, height=0)
            print("[TTS] gTTS fallback success")
        except Exception as fallback_e:
            print(f"[TTS] Both TTS systems failed: {fallback_e}")

def save_interview_session(session_data, filename=None):
    """Save interview session to file"""
    if filename is None:
        filename = f"interview_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(filename, 'w') as f:
        json.dump(session_data, f, indent=2)
    
    return filename

def load_interview_session(filename):
    """Load interview session from file"""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading session: {str(e)}")
        return None

def calculate_similarity(text1, text2):
    """Calculate simple similarity between two texts"""
    # Convert to lowercase and split into words
    words1 = set(re.findall(r'\w+', text1.lower()))
    words2 = set(re.findall(r'\w+', text2.lower()))
    
    if not words1 or not words2:
        return 0.0
    
    # Calculate Jaccard similarity
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    return intersection / union if union > 0 else 0.0

def extract_keywords(text):
    """Extract important keywords from text"""
    # Simple keyword extraction - can be improved with NLP
    words = re.findall(r'\w+', text.lower())
    
    # Filter out common stop words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                  'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has',
                  'had', 'do', 'does', 'did', 'will', 'would', 'shall', 'should',
                  'may', 'might', 'must', 'can', 'could', 'this', 'that', 'these',
                  'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'my', 'your',
                  'his', 'her', 'its', 'our', 'their'}
    
    keywords = [word for word in words if word not in stop_words and len(word) > 2]
    
    # Count frequencies
    freq = {}
    for word in keywords:
        freq[word] = freq.get(word, 0) + 1
    
    # Return top keywords
    sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, count in sorted_words[:10]]

def generate_question_id():
    """Generate unique question ID"""
    return f"Q{random.randint(1000, 9999)}"

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def format_time(seconds):
    """Format seconds into readable time"""
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes}:{seconds:02d}"

def create_progress_chart(scores):
    """Create a progress chart"""
    fig = {
        "data": [
            {
                "type": "scatter",
                "x": list(range(1, len(scores) + 1)),
                "y": scores,
                "mode": "lines+markers",
                "name": "Score Progression",
                "line": {"color": "#1E88E5", "width": 3},
                "marker": {"size": 10}
            }
        ],
        "layout": {
            "title": "Your Performance Trend",
            "xaxis": {"title": "Question Number"},
            "yaxis": {"title": "Score", "range": [0, 10]},
            "showlegend": False
        }
    }
    return fig

def get_welcome_animation():
    """Returns welcome animation HTML"""
    return """
    <div style="text-align: center; padding: 2rem;">
        <div class="float" style="font-size: 5rem;">🎯</div>
        <h1 class="pulse" style="color: #667eea;">Welcome to AI Interview Coach</h1>
        <div class="typing-indicator" style="justify-content: center;">
            <span></span>
            <span></span>
            <span></span>
        </div>
    </div>
    """

def get_success_animation():
    """Returns success animation HTML"""
    return """
    <div style="text-align: center; padding: 1rem;">
        <div class="bounce" style="font-size: 3rem;">✅</div>
        <div class="glow" style="width: 100%; height: 4px; background: #10b981; border-radius: 2px; margin: 1rem 0;">
            <div style="width: 100%; height: 100%; background: #10b981; border-radius: 2px;" class="pulse"></div>
        </div>
    </div>
    """
def get_stepper_html(total_questions: int, current_index: int) -> str:
    """Returns the glassmorphism horizontal progress stepper HTML."""
    dots = []
    for i in range(total_questions):
        if i < current_index:
            classes = "step-dot completed"
        elif i == current_index:
            classes = "step-dot active"
        else:
            classes = "step-dot"
        dots.append(f'<div class="{classes}"></div>')
        
    return f"""
    <div class="stepper">
        {''.join(dots)}
    </div>
    """

def get_meet_control_bar() -> str:
    """Returns the Google Meet-style control bar."""
    return """
    <div class="control-bar">
        <div class="ctrl-btn" title="Toggle Mic">🎙️</div>
        <div class="ctrl-btn" title="Toggle Camera">📹</div>
        <div class="ctrl-btn" title="Settings">⚙️</div>
        <div class="ctrl-btn ctrl-danger" title="End Call">📞</div>
    </div>
    """

def get_waveform_animation() -> str:
    """Returns a CSS animated audio waveform."""
    return """
    <div class="waveform">
        <div class="wave-bar"></div>
        <div class="wave-bar"></div>
        <div class="wave-bar"></div>
        <div class="wave-bar"></div>
        <div class="wave-bar"></div>
    </div>
    """

def get_score_ring(score: float, max_score: float = 10.0, size: int = 120) -> str:
    """
    Returns an animated circular progress ring specifically for the score.
    Animates counting up to the final score using CSS variables.
    """
    percentage = (score / max_score) * 100
    circumference = 2 * 3.14159 * 45
    offset = circumference - (percentage / 100) * circumference
    
    color = "#00d4aa" if score >= 7 else "#f59e0b" if score >= 5 else "#ff4757"
    
    return f"""
    <div style="position:relative; width:{size}px; height:{size}px; margin: 0 auto;">
        <svg width="{size}" height="{size}" viewBox="0 0 100 100" style="transform: rotate(-90deg);">
            <!-- Background circle -->
            <circle cx="50" cy="50" r="45" fill="none" stroke="rgba(255,255,255,0.05)" stroke-width="8"/>
            <!-- Animated progress circle -->
            <circle cx="50" cy="50" r="45" fill="none" stroke="{color}" stroke-width="8"
                    stroke-dasharray="{circumference}" stroke-dashoffset="{circumference}"
                    stroke-linecap="round">
                <animate attributeName="stroke-dashoffset" 
                         from="{circumference}" to="{offset}" 
                         dur="1.5s" fill="freeze" calcMode="spline" keySplines="0.1 0.8 0.2 1"/>
            </circle>
        </svg>
        <div style="position:absolute; top:50%; left:50%; transform:translate(-50%, -50%); text-align:center;">
            <div style="font-family:'Space Grotesk',sans-serif; font-size:1.8rem; font-weight:700; color:{color};">{score}</div>
            <div style="font-size:0.6rem; color:var(--text-secondary); text-transform:uppercase;">/ {max_score}</div>
        </div>
    </div>
    """
    
def display_question_card(question_idx: int, difficulty: str, topic: str, text: str):
    """Generates the styled glassmorphism question card."""
    diff_class = f"q-card-{difficulty.lower()}"
    return f"""
    <div class="q-card {diff_class}">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
            <span style="font-family:'Space Grotesk',sans-serif; color:var(--accent-2); font-weight:600; font-size:0.9rem;">
                Question {question_idx}
            </span>
            <span style="background:rgba(255,255,255,0.1); padding:4px 10px; border-radius:12px; font-size:0.75rem;">
                {topic.upper()} • {difficulty.upper()}
            </span>
        </div>
        <p style="font-size:1.15rem; line-height:1.6; font-weight:400; color:white; margin:0;">
            {text}
        </p>
    </div>
    """
