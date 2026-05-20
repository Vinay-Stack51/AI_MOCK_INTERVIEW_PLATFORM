import streamlit as st
import streamlit.components.v1 as components
from utils import get_robot_avatar

def render_avatar_panel(v_label: str, is_muted: bool):
    avatar_emotion = "listening" if not is_muted else "neutral"
    status_color = "#10b981" if not is_muted else "#9aa0a6"
    status_bg = "rgba(16,185,129,0.1)" if not is_muted else "rgba(154,160,166,0.1)"
    status_text = "Listening" if not is_muted else "Waiting"
    
    avatar_html = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    @keyframes pulse {{
        0% {{ opacity:1; transform:scale(1); }}
        50% {{ opacity:0.6; transform:scale(1.3); }}
        100% {{ opacity:1; transform:scale(1); }}
    }}
    .pulse {{ animation: pulse 2s infinite; }}
    </style>
    <div style="
        background: var(--panel-bg, #1a1b1e);
        border: 2px solid var(--panel-border, #3c4043);
        border-radius: 14px;
        padding: 20px;
        height: 496px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        font-family: 'Inter', sans-serif;
        box-shadow: 0 0 15px {"rgba(16,185,129,0.15)" if not is_muted else "rgba(154,160,166,0.15)"};
    ">
        <div style="margin-bottom:auto; color:var(--text-muted, #9aa0a6); font-size:0.85rem; font-weight:500; width:100%; text-align:left; border-bottom:1px solid var(--panel-border, #2d2f31); padding-bottom:10px;">
            🤖 AI Coach — <strong style="color:var(--text-main, #e8eaed);">{v_label}</strong>
        </div>
        
        <div style="margin: auto 0; display:flex; flex-direction:column; align-items:center;">
            {get_robot_avatar(avatar_emotion)}
            <div style="margin-top:35px; padding:8px 20px; border-radius:20px; font-size:0.8rem; font-weight:600; 
                        background:{status_bg}; color:{status_color}; text-transform:uppercase; letter-spacing:0.5px;">
                <span style="display:inline-block; width:8px; height:8px; border-radius:50%; background:currentColor; margin-right:6px; animation: pulse 1.5s infinite;"></span>
                {status_text}
            </div>
        </div>
    </div>
    """
    components.html(avatar_html, height=540, scrolling=False)

def render_camera_pane(cand_name: str, is_cam_off: bool):
    cam_hidden = "true" if is_cam_off else "false"

    camera_html = f"""
    <div style="
        background: var(--panel-bg, #1a1b1e);
        border: 2px solid var(--panel-border, #3c4043);
        border-radius: 14px;
        overflow: hidden;
        font-family: 'Inter', sans-serif;
        box-shadow: 0 0 15px rgba(16, 185, 129, 0.15);
    ">
        <div style="
            padding:10px 18px;
            display:flex;
            justify-content:space-between;
            align-items:center;
            border-bottom:1px solid var(--panel-border, #2d2f31);
        ">
            <span style="color:var(--text-muted, #9aa0a6);font-size:0.85rem;font-weight:500;">
                &#128249;&nbsp; Live Camera &mdash;
                <strong style="color:var(--text-main, #e8eaed);">{cand_name}</strong>
            </span>
            <span id="liveTag" style="
                background:rgba(234,67,53,0.18);color:#ea4335;
                font-size:0.7rem;padding:3px 10px;border-radius:20px;
                font-weight:600;letter-spacing:0.4px;
            ">&#9210; LIVE</span>
        </div>

        <div id="videoWrapper" style="position:relative;background:#000;text-align:center;">
            <video id="localVideo"
                autoplay playsinline muted
                style="
                    width:100%;
                    height:490px;
                    object-fit:cover;
                    display:block;
                    transform:scaleX(-1);
                "
            ></video>

            <div id="camOff" style="
                display:none;
                position:absolute;top:0;left:0;right:0;bottom:0;
                background:#0f172a;
                align-items:center;justify-content:center;
                flex-direction:column;
                color:#475569;
                min-height:300px;
            ">
                <div style="font-size:2.8rem;">&#128247;</div>
                <p style="margin:10px 0 0;font-size:0.9rem;">Camera is off</p>
                <p style="font-size:0.75rem;opacity:0.55;margin-top:4px;">
                    Click <strong style="color:#9aa0a6;">Cam On</strong> below
                </p>
            </div>

            <div id="camError" style="
                display:none;
                position:absolute;top:0;left:0;right:0;bottom:0;
                background:#1a1b1e;
                align-items:center;justify-content:center;
                flex-direction:column;
                color:#64748b;
                min-height:300px;
            ">
                <div style="font-size:2.8rem;">&#128247;</div>
                <p style="margin:10px 0 0;font-size:0.9rem;color:#f87171;">
                    Camera permission denied
                </p>
                <p style="font-size:0.75rem;opacity:0.7;margin-top:6px;text-align:center;max-width:280px;">
                    Click the camera icon in your browser address bar and allow camera access,
                    then refresh the page.
                </p>
            </div>
        </div>
    </div>

    <script>
    (function() {{
        var video      = document.getElementById('localVideo');
        var camOffDiv  = document.getElementById('camOff');
        var camErrDiv  = document.getElementById('camError');
        var liveTag    = document.getElementById('liveTag');
        var currentStream = null;
        var isCamOff = {cam_hidden};

        function startCamera() {{
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {{
                camErrDiv.style.display = 'flex';
                return;
            }}
            navigator.mediaDevices.getUserMedia({{ video: true, audio: false }})
                .then(function(stream) {{
                    currentStream = stream;
                    video.srcObject = stream;
                    video.style.display = 'block';
                    camOffDiv.style.display  = 'none';
                    camErrDiv.style.display  = 'none';
                    liveTag.style.display    = 'inline';
                }})
                .catch(function(err) {{
                    console.warn('Camera error:', err);
                    if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {{
                        camErrDiv.style.display = 'flex';
                    }} else if (err.name === 'NotFoundError') {{
                        camErrDiv.innerHTML = '<div style="font-size:2.5rem;">&#128247;</div><p style="margin:10px 0 0;color:#f87171;">No camera detected</p>';
                        camErrDiv.style.display = 'flex';
                    }} else {{
                        camErrDiv.style.display = 'flex';
                    }}
                }});
        }}

        function stopCamera() {{
            if (currentStream) {{
                currentStream.getTracks().forEach(function(t) {{ t.stop(); }});
                currentStream = null;
            }}
            video.srcObject = null;
            video.style.display    = 'none';
            camOffDiv.style.display = 'flex';
            liveTag.style.display  = 'none';
        }}

        if (isCamOff) {{
            stopCamera();
        }} else {{
            startCamera();
        }}
    }})();
    </script>
    """
    components.html(camera_html, height=540, scrolling=False)
