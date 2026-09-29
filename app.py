import json
import re
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from collections import Counter
import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy.orm import Session

import importlib
import ai_analyzer
importlib.reload(ai_analyzer)
from ai_analyzer import AIAnalyzer

import database
importlib.reload(database)
from database import (
    init_db, SessionLocal, JobListing, ScrapeLog,
    register_user, authenticate_user, toggle_user_favorite, get_user_favorite_job_ids
)
from scraper import WebScraper
from notifier import TelegramNotifier

# Page Configuration
st.set_page_config(
    page_title="Akıllı Piyasa & Yetenek Analiz Platformu",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Clean Light Mode Page + Sleek Dark Sidebar + High Contrast Text)
st.markdown("""
<style>
    /* Unhide and Translate Top Header, Deploy Button, and 3-Dots Menu to Turkish */
    header[data-testid="stHeader"] {
        background-color: transparent !important;
        display: flex !important;
        visibility: visible !important;
    }

    div[data-testid="stToolbar"] {
        display: flex !important;
        visibility: visible !important;
    }

    #MainMenu {
        display: block !important;
        visibility: visible !important;
    }

    .stDeployButton {
        display: inline-block !important;
        visibility: visible !important;
    }

    .stDeployButton button {
        background-color: #0F172A !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        border: 1px solid #CBD5E1 !important;
        padding: 4px 12px !important;
    }

    .stDeployButton button * {
        font-size: 0 !important;
        visibility: hidden !important;
    }

    .stDeployButton button::after {
        content: "Yayına Al" !important;
        font-size: 0.85rem !important;
        font-weight: 700 !important;
        color: #FFFFFF !important;
        visibility: visible !important;
    }

    /* Reduce Main Page Top Padding */
    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 2rem !important;
    }

    /* Main Page Background & Base Text */
    .main, .stApp {
        background-color: #FFFFFF !important;
        color: #1A202C !important;
    }
    
    .main p, .main span, .main label, .main h1, .main h2, .main h3, .main h4, .main h5, .main h6, .main li {
        color: #1A202C !important;
    }

    /* Metric Cards */
    .stMetric {
        background-color: #F8FAFC !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 10px !important;
        padding: 16px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
    }
    div[data-testid="stMetricValue"] * {
        color: #0F172A !important;
        font-weight: 800 !important;
        font-size: 2rem !important;
    }
    div[data-testid="stMetricLabel"] * {
        color: #475569 !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
    }

    /* Lock Left Sidebar Permanently Open (Hide all toggle/collapse buttons) */
    [data-testid="stSidebarCollapseButton"],
    [data-testid="collapsedControl"],
    button[aria-label="Close sidebar"],
    button[aria-label="Open sidebar"],
    section[data-testid="stSidebar"] button[kind="header"],
    div[data-testid="stSidebarHeader"] button {
        display: none !important;
        visibility: hidden !important;
        pointer-events: none !important;
    }

    /* Left Sidebar: Sleek Dark Black Background */
    section[data-testid="stSidebar"] {
        background-color: #0D1117 !important;
        border-right: 1px solid #21262D !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stSidebarUserContent"] {
        padding-top: 0.5rem !important;
    }

    /* Main Sidebar Header (İlan & Yetenek Filtreleme) */
    section[data-testid="stSidebar"] h1:first-child,
    section[data-testid="stSidebar"] h2:first-child,
    section[data-testid="stSidebar"] h3:first-child {
        margin-top: -6px !important;
        font-size: 1.45rem !important;
        font-weight: 800 !important;
        color: #FFFFFF !important;
        letter-spacing: -0.02em !important;
        padding-bottom: 4px !important;
    }

    /* Left Sidebar Headers & Labels: Crisp White Text */
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span {
        color: #F8FAFC !important;
        font-weight: 600 !important;
    }

    /* Crisp High-Contrast White Divider Lines in Sidebar */
    section[data-testid="stSidebar"] hr {
        border-top: 2px solid #FFFFFF !important;
        border-bottom: none !important;
        opacity: 1 !important;
        margin: 18px 0 !important;
    }

    /* Left Sidebar Input Boxes */
    section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 8px !important;
    }
    
    section[data-testid="stSidebar"] div[data-baseweb="select"] * {
        color: #0F172A !important;
    }

    /* Multiselect Tags */
    section[data-testid="stSidebar"] span[data-baseweb="tag"] {
        background-color: #F1F5F9 !important;
        border: 1px solid #CBD5E1 !important;
        color: #0F172A !important;
        font-weight: 700 !important;
        border-radius: 6px !important;
    }
    
    section[data-testid="stSidebar"] span[data-baseweb="tag"] * {
        color: #0F172A !important;
    }

    section[data-testid="stSidebar"] input {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border-radius: 8px !important;
    }

    /* Status Badge (Sleek Dark Black Badge) */
    .status-badge {
        background-color: #0D1117 !important;
        border: 1px solid #30363D !important;
        color: #FFFFFF !important;
        padding: 6px 16px !important;
        border-radius: 20px !important;
        font-size: 0.85rem !important;
        font-weight: 700 !important;
        display: inline-block !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
    }

    /* Sidebar Action Buttons */
    section[data-testid="stSidebar"] .stButton > button {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
        transition: all 0.2s ease;
    }
    section[data-testid="stSidebar"] .stButton > button * {
        color: #0F172A !important;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        background-color: #F8FAFC !important;
        border-color: #94A3B8 !important;
        color: #0F172A !important;
    }

    /* Expander Accordions & Apply Buttons */
    .stExpander {
        background-color: #F8FAFC !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 8px !important;
        margin-bottom: 12px !important;
    }

    .apply-btn {
        background-color: #0F172A !important;
        color: #FFFFFF !important;
        border: 1px solid #0F172A !important;
        padding: 10px 20px !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        cursor: pointer !important;
        display: inline-block !important;
        text-decoration: none !important;
    }
    .apply-btn * {
        color: #FFFFFF !important;
        text-decoration: none !important;
    }
    .apply-btn:hover {
        background-color: #1E293B !important;
        color: #FFFFFF !important;
    }

    /* Vertical Divider Line between Left & Right Job Columns */
    .vertical-divider {
        border-left: 2px solid #CBD5E1 !important;
        height: 100% !important;
        min-height: 180px !important;
        margin: 0 auto !important;
        width: 1px !important;
        opacity: 0.8 !important;
    }

    /* ─── PDF CV Uploader Box Styling (Sleek Dark Theme + Crisp High Contrast White Text) ─── */
    section[data-testid="stSidebar"] div[data-testid="stFileUploader"] {
        background-color: #161B22 !important;
        border: 2px dashed #475569 !important;
        border-radius: 12px !important;
        padding: 12px !important;
    }
    
    section[data-testid="stSidebar"] div[data-testid="stFileUploader"] * {
        color: #F8FAFC !important;
        fill: #F8FAFC !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] {
        background-color: #0D1117 !important;
        border: 1px dashed #475569 !important;
        border-radius: 8px !important;
        padding: 12px !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stFileUploader"] section[data-testid="stFileUploaderDropzone"] * {
        color: #F8FAFC !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stFileUploader"] button {
        background-color: #2563EB !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: 700 !important;
        padding: 6px 14px !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stFileUploader"] button * {
        color: #FFFFFF !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stFileUploader"] button:hover {
        background-color: #1D4ED8 !important;
    }

    /* Clean Non-Overflowing Turkish Text Overrides for Dropzone Elements */
    section[data-testid="stSidebar"] div[data-testid="stFileUploaderDropzoneInstructions"] {
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 4px !important;
        text-align: center !important;
        width: 100% !important;
        box-sizing: border-box !important;
        overflow: hidden !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stFileUploaderDropzoneInstructions"] > div {
        visibility: hidden !important;
        height: 20px !important;
        position: relative !important;
        width: 100% !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stFileUploaderDropzoneInstructions"] > div::after {
        content: "CV'nizi buraya bırakın" !important;
        visibility: visible !important;
        position: absolute !important;
        left: 0 !important;
        right: 0 !important;
        top: 0 !important;
        text-align: center !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        color: #F8FAFC !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stFileUploaderDropzoneInstructions"] > small {
        visibility: hidden !important;
        height: 16px !important;
        position: relative !important;
        width: 100% !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stFileUploaderDropzoneInstructions"] > small::after {
        content: "PDF veya TXT" !important;
        visibility: visible !important;
        position: absolute !important;
        left: 0 !important;
        right: 0 !important;
        top: 0 !important;
        text-align: center !important;
        font-size: 0.75rem !important;
        font-weight: 500 !important;
        color: #94A3B8 !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stFileUploader"] button span {
        visibility: hidden !important;
        position: relative !important;
        width: 100% !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stFileUploader"] button span::after {
        content: "Dosya Seç" !important;
        visibility: visible !important;
        position: absolute !important;
        left: 0 !important;
        right: 0 !important;
        top: 0 !important;
        text-align: center !important;
        font-size: 0.85rem !important;
        font-weight: 700 !important;
        color: #FFFFFF !important;
    }

    /* ─── Bildirim Alarm Paneli Container (Beyaz kutu, siyah yazı) ─── */
    div[data-testid="stSidebar"] div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF !important;
        border: 2px solid #CBD5E1 !important;
        border-radius: 12px !important;
        padding: 16px !important;
        margin-top: 4px !important;
    }
    div[data-testid="stSidebar"] div[data-testid="stVerticalBlockBorderWrapper"] * {
        color: #0F172A !important;
    }
    div[data-testid="stSidebar"] div[data-testid="stVerticalBlockBorderWrapper"] label,
    div[data-testid="stSidebar"] div[data-testid="stVerticalBlockBorderWrapper"] p,
    div[data-testid="stSidebar"] div[data-testid="stVerticalBlockBorderWrapper"] span,
    div[data-testid="stSidebar"] div[data-testid="stVerticalBlockBorderWrapper"] div {
        color: #0F172A !important;
        background-color: transparent !important;
    }
    /* Radio seçenekleri siyah */
    div[data-testid="stSidebar"] div[data-testid="stVerticalBlockBorderWrapper"] div[data-testid="stRadio"] label span p {
        color: #0F172A !important;
        font-weight: 600 !important;
    }
    /* Input kutuları */
    div[data-testid="stSidebar"] div[data-testid="stVerticalBlockBorderWrapper"] input[type="text"],
    div[data-testid="stSidebar"] div[data-testid="stVerticalBlockBorderWrapper"] input[type="email"] {
        background-color: #F8FAFC !important;
        color: #0F172A !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 8px !important;
    }
    /* Multiselect kutuları */
    div[data-testid="stSidebar"] div[data-testid="stVerticalBlockBorderWrapper"] div[data-baseweb="select"] > div {
        background-color: #F8FAFC !important;
        border: 1px solid #CBD5E1 !important;
        color: #0F172A !important;
    }
    div[data-testid="stSidebar"] div[data-testid="stVerticalBlockBorderWrapper"] div[data-baseweb="select"] * {
        color: #0F172A !important;
    }
    /* Kaydet butonu */
    .alarm-save-btn > button {
        background-color: #0F172A !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        width: 100% !important;
    }
    .alarm-save-btn > button * {
        color: #FFFFFF !important;
    }
    .alarm-save-btn > button:hover {
        background-color: #1E293B !important;
    }
    /* İptal butonu */
    .alarm-cancel-btn > button {
        background-color: #F1F5F9 !important;
        color: #0F172A !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        width: 100% !important;
    }
    .alarm-cancel-btn > button * {
        color: #0F172A !important;
    }

    /* Floating AI FAB Button (Fixed to Viewport Bottom-Right Corner On Scroll) */
    .floating-ai-fab-btn,
    .floating-ai-fab-btn > div,
    .floating-ai-fab-btn .stButton {
        position: fixed !important;
        bottom: 24px !important;
        right: 24px !important;
        z-index: 99999999 !important;
        margin: 0 !important;
        padding: 0 !important;
        width: auto !important;
        height: auto !important;
    }

    .floating-ai-fab-btn button {
        background-color: #0F172A !important;
        color: #FFFFFF !important;
        border-radius: 30px !important;
        border: 2px solid #3B82F6 !important;
        padding: 8px 18px !important;
        font-weight: 800 !important;
        font-size: 0.85rem !important;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4) !important;
        transition: all 0.2s ease !important;
        cursor: pointer !important;
    }
    .floating-ai-fab-btn button * {
        color: #FFFFFF !important;
    }
    .floating-ai-fab-btn button:hover {
        background-color: #1E293B !important;
        border-color: #60A5FA !important;
        transform: scale(1.05) !important;
    }

    /* Fixed Floating Chat Window Container (Fixed to Viewport Bottom-Right Corner On Scroll) */
    .floating-chat-modal-wrapper,
    .floating-chat-modal-wrapper > div,
    .floating-chat-modal-wrapper div[data-testid="stVerticalBlockBorderWrapper"] {
        position: fixed !important;
        bottom: 24px !important;
        right: 24px !important;
        width: 340px !important;
        max-width: 90vw !important;
        background-color: #FFFFFF !important;
        border: 2px solid #3B82F6 !important;
        border-radius: 16px !important;
        padding: 12px !important;
        box-shadow: 0 10px 35px rgba(0, 0, 0, 0.35) !important;
        z-index: 99999999 !important;
    }

    /* Chat bubble styling */
    .chat-bubble-user {
        background-color: #0F172A !important;
        color: #FFFFFF !important;
        padding: 10px 14px !important;
        border-radius: 14px 14px 2px 14px !important;
        margin-bottom: 8px !important;
        font-size: 0.9rem !important;
        text-align: right !important;
    }
    .chat-bubble-user * {
        color: #FFFFFF !important;
    }

    .chat-bubble-assistant {
        background-color: #F1F5F9 !important;
        color: #0F172A !important;
        border: 1px solid #E2E8F0 !important;
        padding: 10px 14px !important;
        border-radius: 14px 14px 14px 2px !important;
        margin-bottom: 8px !important;
        font-size: 0.9rem !important;
    }
    .chat-bubble-assistant * {
        color: #0F172A !important;
    }

    /* Floating "Başa Dön" (Scroll to Top) Button (Far Right Edge) */
    .scroll-to-top-container,
    .scroll-to-top-container > div,
    div[data-testid="stElementContainer"]:has(.scroll-to-top-container) {
        position: fixed !important;
        bottom: 74px !important;
        right: 24px !important;
        z-index: 99999998 !important;
        margin: 0 !important;
        padding: 0 !important;
        width: auto !important;
    }
    
    .scroll-to-top-btn {
        background-color: #0F172A !important;
        color: #FFFFFF !important;
        border: 2px solid #3B82F6 !important;
        border-radius: 30px !important;
        padding: 8px 18px !important;
        font-weight: 800 !important;
        font-size: 0.85rem !important;
        text-decoration: none !important;
        display: inline-flex !important;
        align-items: center !important;
        gap: 6px !important;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4) !important;
        transition: all 0.2s ease !important;
        cursor: pointer !important;
    }

    .scroll-to-top-btn:hover {
        background-color: #1E293B !important;
        border-color: #60A5FA !important;
        color: #FFFFFF !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.5) !important;
    }

    .scroll-to-top-btn * {
        color: #FFFFFF !important;
        text-decoration: none !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize DB & AI Analyzer
init_db()
ai_analyzer = AIAnalyzer()
notifier = TelegramNotifier()

# Session state: bildirim paneli açık/kapalı & kayıtlı alarmlar & kullanıcı oturumu
if "show_alarm_panel" not in st.session_state:
    st.session_state.show_alarm_panel = False
if "saved_alarms" not in st.session_state:
    st.session_state.saved_alarms = []
if "alarm_success_msg" not in st.session_state:
    st.session_state.alarm_success_msg = ""
if "user" not in st.session_state:
    st.session_state.user = None
if "guest_favorites" not in st.session_state:
    st.session_state.guest_favorites = set()
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = None
if "show_ai_chat_modal" not in st.session_state:
    st.session_state.show_ai_chat_modal = False
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "assistant", "content": "Merhaba! Ben Platform Yapay Zeka Asistanıyım. Sitede takıldığınız veya öğrenmek istediğiniz her şeyi bana sorabilirsiniz. Size nasıl yardımcı olabilirim?"}
    ]

# Page Top Anchor & Floating "Başa Dön" Button
st.markdown('<div id="page-top"></div>', unsafe_allow_html=True)
st.markdown("""
<div class="scroll-to-top-container">
    <a href="#page-top" onclick="
        try {
            if (window.parent) {
                var mainSec = window.parent.document.querySelector('section.main');
                if (mainSec) mainSec.scrollTo({top: 0, behavior: 'smooth'});
                var appView = window.parent.document.querySelector('.stApp');
                if (appView) appView.scrollTo({top: 0, behavior: 'smooth'});
                window.parent.scrollTo({top: 0, behavior: 'smooth'});
            }
        } catch(e) {}
        return true;
    " class="scroll-to-top-btn">
        <span>↑</span> <span>Başa Dön</span>
    </a>
</div>
""", unsafe_allow_html=True)

def send_email_simulation(to_addr: str, subject: str, body: str) -> bool:
    """Simulates e-mail dispatch (logs to console). Replace with real SMTP for production."""
    print(f"[E-Posta Simülasyon] Alıcı: {to_addr}\nKonu: {subject}\n{body}")
    return True

def save_alarm_rule(channel: str, address: str, filter_skills: list,
                   filter_job_types: list, filter_levels: list) -> str:
    """Saves a new alarm rule to database and session_state, sending immediate confirmation."""
    if not address.strip():
        return "Lütfen geçerli bir Telegram Chat ID veya e-posta adresi giriniz."

    criteria_parts = []
    if filter_skills:
        criteria_parts.append(f"Yetenekler: {', '.join(filter_skills)}")
    if filter_job_types:
        criteria_parts.append(f"Çalışma Tipi: {', '.join(filter_job_types)}")
    if filter_levels:
        criteria_parts.append(f"Kıdem: {', '.join(filter_levels)}")
    filter_summary = " | ".join(criteria_parts) if criteria_parts else "Tüm ilanlar"

    # Persist rule to SQLite DB
    try:
        from database import save_alert_rule
        rule_id = save_alert_rule(channel, address.strip(), filter_skills, filter_job_types, filter_levels, [])
    except Exception as e:
        print(f"[DB Rule Save Warning] {e}")

    rule = {
        "channel": channel,
        "address": address.strip(),
        "skills": filter_skills,
        "job_types": filter_job_types,
        "levels": filter_levels,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "summary": filter_summary
    }
    st.session_state.saved_alarms.append(rule)

    if channel == "Telegram":
        notifier.send_rule_confirmation("Telegram", address.strip(), filter_summary)
    else:
        subject = "Bildirim Alarmınız Kuruldu — Akıllı Piyasa Takipçisi"
        body = (
            f"Merhaba!\n\n"
            f"Aşağıdaki kriterlere uyan yeni iş ilanları e-posta ile bildirilecektir:\n\n"
            f"{filter_summary}\n\n"
            f"Akıllı Piyasa & Yetenek Analiz Platformu"
        )
        send_email_simulation(address.strip(), subject, body)

    return f"Alarm kuruldu! Kanal: {channel} | Kriterler: {filter_summary}"

@st.cache_data(ttl=10)
def load_data():
    db = SessionLocal()
    try:
        jobs = db.query(JobListing).order_by(JobListing.created_at.desc()).all()
        data = []
        for j in jobs:
            try:
                skills_list = json.loads(j.extracted_skills) if j.extracted_skills else []
            except:
                skills_list = []
            
            desc_tr = ai_analyzer.translate_summary_to_turkish(j.title, j.description or "")
            loc_clean = (j.location or "").strip()
            if not loc_clean:
                loc_clean = "Uzaktan (Küresel)"

            data.append({
                "ID": j.id,
                "Başlık": j.title,
                "Şirket": j.company,
                "Lokasyon": loc_clean,
                "Çalışma Tipi": j.job_type,
                "Kıdem": j.experience_level,
                "Maaş": j.salary,
                "Kaynak": j.source,
                "Açıklama": desc_tr,
                "URL": j.url,
                "Yetenekler": skills_list,
                "RawDate": j.created_at,
                "Tarih": j.created_at.strftime("%Y-%m-%d %H:%M")
            })
        df = pd.DataFrame(data)
        logs = db.query(ScrapeLog).order_by(ScrapeLog.timestamp.desc()).limit(10).all()
        log_data = [{
            "Zaman": l.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "Tarana Sayı": l.total_scraped,
            "Yeni Eklenen": l.new_added,
            "Durum": l.status,
            "Mesaj": l.message
        } for l in logs]
        return df, pd.DataFrame(log_data)
    finally:
        db.close()

def check_skill_in_text(skill_name, text_lower):
    sk_low = skill_name.lower().strip()
    if sk_low == 'c':
        return bool(re.search(r'(?i)(?<![a-zA-Z0-9#+])c(?![a-zA-Z0-9#+])', text_lower))
    elif sk_low == 'r':
        return bool(re.search(r'(?i)\br\b', text_lower))
    elif sk_low == 'c#':
        return 'c#' in text_lower or 'csharp' in text_lower
    elif sk_low == 'c++':
        return 'c++' in text_lower or 'cpp' in text_lower
    elif sk_low == '.net':
        return '.net' in text_lower or 'dotnet' in text_lower
    else:
        pattern = rf'\b{re.escape(sk_low)}\b'
        return bool(re.search(pattern, text_lower))

def calculate_match_score(job_skills, user_selected_skills, job_title, job_desc=""):
    """Calculates percentage AI Career Match Score between user skills and job requirements."""
    if not user_selected_skills:
        return 100, "", "", []
    
    job_skills_lower = [s.lower().strip() for s in job_skills]
    full_text_lower = f"{job_title} {job_desc}".lower()

    matched = set()
    for us in user_selected_skills:
        us_low = us.lower().strip()
        if us_low in job_skills_lower:
            matched.add(us)
        elif check_skill_in_text(us, full_text_lower):
            matched.add(us)

    matched_list = list(matched)
    if not matched_list:
        score = 0
        badge = ""
        color = ""
    else:
        ratio = len(matched_list) / max(1, len(user_selected_skills))
        score = int(ratio * 100)
        if any(s.lower() in job_title.lower() for s in user_selected_skills):
            score = min(100, score + 15)
        
        if score >= 70:
            badge = f"[ %{score} YÜKSEK UYUM ]"
            color = "#15803D"
        elif score >= 40:
            badge = f"[ %{score} ORTA UYUM ]"
            color = "#B45309"
        else:
            badge = f"[ %{score} DÜŞÜK UYUM ]"
            color = "#1E40AF"

    return score, badge, color, matched_list

def render_job_card(row, selected_user_skills, is_fav=False, key_prefix="card"):
    """Renders an individual job card with Apply and Favorite options."""
    score, badge, color, matched_skills = calculate_match_score(
        row['Yetenekler'],
        selected_user_skills,
        row['Başlık'],
        row['Açıklama']
    )
    fav_star = "★ " if is_fav else ""
    expander_title = f"{fav_star}{badge}  {row['Başlık']} — {row['Şirket']} ({row['Çalışma Tipi']})" if badge else f"{fav_star}{row['Başlık']} — {row['Şirket']} ({row['Çalışma Tipi']})"
    with st.expander(expander_title):
        if badge:
            st.markdown(f"**AI Kariyer Uyum Skoru:** <span style='background-color:{color}; color:#FFFFFF; padding:4px 12px; border-radius:12px; font-weight:700; font-size:0.85rem;'>{badge}</span>", unsafe_allow_html=True)
        if selected_user_skills:
            if matched_skills:
                st.write(f"**Eşleşen Yetenekleriniz:** {', '.join([f'`{m}`' for m in matched_skills])}")
            else:
                st.write("*Seçtiğiniz diller bu ilanda doğrudan istenmemiş olsa da başvurabilirsiniz.*")
            st.markdown("<br>", unsafe_allow_html=True)
        st.write(f"**Lokasyon:** {row['Lokasyon']}")
        st.write(f"**Maaş / Skala:** {row['Maaş']}")
        st.write(f"**Kıdem:** {row['Kıdem']}")
        st.write(f"**Veri Kaynağı:** {row['Kaynak']}")
        st.write(f"**İlan Özeti (Türkçe):** {row['Açıklama']}")
        st.write("**Aranan Yetenekler & Araçlar:**")
        if row['Yetenekler']:
            st.write(", ".join([f"`{s}`" for s in row['Yetenekler']]))
        else:
            st.write("Belirtilmedi")
        
        st.markdown("<br>", unsafe_allow_html=True)
        col_act1, col_act2 = st.columns([2, 1])
        with col_act1:
            st.markdown(f"<a href='{row['URL']}' target='_blank' class='apply-btn'><span style='color:#FFFFFF !important; font-weight:700;'>İlana Başvur (Orijinal Site)</span></a>", unsafe_allow_html=True)
        with col_act2:
            fav_label = "★ Favorilerde" if is_fav else "☆ Favorilere Ekle"
            if st.button(fav_label, key=f"{key_prefix}_fav_btn_{row['ID']}", use_container_width=True):
                if st.session_state.user:
                    _, fav_msg = toggle_user_favorite(st.session_state.user["id"], row["ID"])
                    st.toast(fav_msg)
                else:
                    if row["ID"] in st.session_state.guest_favorites:
                        st.session_state.guest_favorites.remove(row["ID"])
                        st.toast("Favorilerden çıkarıldı.")
                    else:
                        st.session_state.guest_favorites.add(row["ID"])
                        st.toast("Favorilere eklendi!")
                st.rerun()

# Header Section
col_head1, col_head2 = st.columns([2, 1])
with col_head1:
    st.title("Akıllı Piyasa & Yetenek Analiz Platformu")
    st.caption("Yapay Zeka Destekli Canlı Piyasa, Yetenek ve Kariyer Takip Otomasyonu")
with col_head2:
    st.markdown("<div style='text-align: right;'><span class='status-badge'>SİSTEM ÇALIŞIYOR</span></div>", unsafe_allow_html=True)
    st.markdown("<div style='margin-top: 8px;'></div>", unsafe_allow_html=True)
    if st.session_state.user:
        u_name = st.session_state.user['username']
        col_u_info, col_u_out = st.columns([2, 1])
        with col_u_info:
            st.markdown(f"<div style='text-align: right; padding-top: 6px;'><b>Kullanıcı:</b> {u_name}</div>", unsafe_allow_html=True)
        with col_u_out:
            if st.button("Çıkış Yap", key="btn_logout", use_container_width=True):
                st.session_state.user = None
                st.session_state.auth_mode = None
                st.rerun()
    else:
        c_login, c_reg = st.columns(2)
        with c_login:
            if st.button("Giriş Yap", key="btn_open_login", use_container_width=True):
                st.session_state.auth_mode = "login" if st.session_state.auth_mode != "login" else None
                st.rerun()
        with c_reg:
            if st.button("Kayıt Ol", key="btn_open_register", use_container_width=True):
                st.session_state.auth_mode = "register" if st.session_state.auth_mode != "register" else None
                st.rerun()

# Auth Forms Container
if st.session_state.auth_mode == "login" and not st.session_state.user:
    with st.expander("🔑 Giriş Yap", expanded=True):
        col_u, col_p, col_b = st.columns([2, 2, 1])
        with col_u:
            l_username = st.text_input("Kullanıcı Adı veya E-Posta", key="login_username_input")
        with col_p:
            l_password = st.text_input("Şifre", type="password", key="login_password_input")
        with col_b:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            if st.button("Giriş Yap", key="login_submit_btn", use_container_width=True):
                if l_username and l_password:
                    ok, res = authenticate_user(l_username, l_password)
                    if ok:
                        st.session_state.user = res
                        st.session_state.auth_mode = None
                        st.success(f"Hoş geldiniz, {res['username']}!")
                        st.rerun()
                    else:
                        st.error(res)
                else:
                    st.warning("Lütfen tüm alanları doldurunuz.")

elif st.session_state.auth_mode == "register" and not st.session_state.user:
    with st.expander("📝 Yeni Kullanıcı Kaydı", expanded=True):
        col_r1, col_r2, col_r3, col_r4 = st.columns([2, 2, 2, 1])
        with col_r1:
            r_username = st.text_input("Kullanıcı Adı", key="reg_username_input")
        with col_r2:
            r_email = st.text_input("E-Posta Adresi", key="reg_email_input")
        with col_r3:
            r_password = st.text_input("Şifre", type="password", key="reg_password_input")
        with col_r4:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            if st.button("Kayıt Ol", key="reg_submit_btn", use_container_width=True):
                if r_username and r_email and r_password:
                    ok, msg = register_user(r_username, r_email, r_password)
                    if ok:
                        st.success(msg)
                        st.session_state.auth_mode = "login"
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.warning("Lütfen tüm alanları doldurunuz.")

st.divider()

# Load Data
df, log_df = load_data()

# Dynamic Active Location and Skill Collection
available_skills = set()
available_locations = set()

if not df.empty:
    if "Yetenekler" in df.columns:
        for sublist in df["Yetenekler"]:
            for item in sublist:
                if item and isinstance(item, str) and len(item.strip()) > 1:
                    available_skills.add(item.strip())
                    
    if "Lokasyon" in df.columns:
        loc_counts = df["Lokasyon"].value_counts()
        for loc_name, count in loc_counts.items():
            if count >= 1 and isinstance(loc_name, str) and len(loc_name.strip()) > 1:
                available_locations.add(loc_name.strip())

sorted_skills = sorted(list(available_skills))
if "Python" not in sorted_skills:
    sorted_skills.insert(0, "Python")
if "Microsoft Office" not in sorted_skills:
    sorted_skills.insert(1, "Microsoft Office")

sorted_locations = sorted(list(available_locations))

# Sidebar Filters & Controls
st.sidebar.header("İlan & Yetenek Filtreleme")

# PDF CV Upload Section
st.sidebar.subheader("PDF CV ile Otomatik Eşleşme")
cv_file = st.sidebar.file_uploader(
    "CV'nizi Yükleyin (PDF / TXT)",
    type=["pdf", "txt"],
    help="CV'nizdeki tüm yetenekler yapay zeka ile taranıp ilanlarla otomatik % Uyum Skoru ile eşleştirilir."
)

cv_skills = []
if cv_file:
    with st.spinner("CV analiz ediliyor..."):
        try:
            file_bytes = cv_file.getvalue() if hasattr(cv_file, "getvalue") else cv_file.read()
            fresh_analyzer = AIAnalyzer()
            extracted_cv_text = fresh_analyzer.parse_cv_file(file_bytes, cv_file.name)
            cv_res = fresh_analyzer.analyze_cv_skills(extracted_cv_text)
            cv_skills = cv_res.get("skills", [])
            if cv_skills:
                st.sidebar.success(f"CV Analiz Edildi! Tespit edilen yetenekler: {', '.join(cv_skills)}")
            else:
                st.sidebar.info("CV metni okundu. Belirgin bir yazılım/araç etiketine rastlanmadı.")
        except Exception as err:
            st.sidebar.error(f"CV dosyası okuma hatası: {err}")

# 1. User skill & app selection filter
all_options_skills = sorted(list(set(sorted_skills).union(set(cv_skills)))) if cv_skills else sorted_skills
default_skills = cv_skills if cv_skills else []

selected_user_skills = st.sidebar.multiselect(
    "Bildiğiniz Yazılım Dilleri & Uygulamalar",
    options=all_options_skills,
    default=default_skills,
    placeholder="Seçim yapınız veya yukarıdan CV yükleyiniz...",
    help="Örnek: Python, Microsoft Office, SQL, Docker, React vb. seçerek size en uygun ilanları görün."
)

# 2. Work Type filter
job_type_filter = st.sidebar.multiselect(
    "Çalışma Tipi",
    options=["Uzaktan", "Ofis / Hibrit"],
    default=["Uzaktan", "Ofis / Hibrit"],
    placeholder="Seçim yapınız..."
)

# 3. Experience Level filter
experience_filter = st.sidebar.multiselect(
    "Kıdem Seviyesi",
    options=["Başlangıç (Junior)", "Orta Seviye (Mid)", "Kıdemli (Senior)"],
    default=["Başlangıç (Junior)", "Orta Seviye (Mid)", "Kıdemli (Senior)"],
    placeholder="Seçim yapınız..."
)

# 4. Dynamic Location Filter
location_filter = st.sidebar.multiselect(
    "Lokasyon / Bölge",
    options=sorted_locations,
    default=[],
    placeholder="Seçim yapınız...",
    help="Sadece aktif ilan bulunan gerçek lokasyonlar listelenir."
)

# 5. Job Freshness / Date Filter
freshness_filter = st.sidebar.selectbox(
    "İlan Tazeliği",
    options=["Tüm Zamanlar", "Son 24 Saat", "Son 3 Gün", "Son 7 Gün"],
    index=0,
    help="İlanların yayınlanma tarihine göre filtrelenmesi."
)

# 6. Text Search query
search_query = st.sidebar.text_input("Arama (İlan Başlığı veya Şirket)", "", placeholder="Metin yazarak arayınız...")

st.sidebar.divider()

# Bildirim Alarmı Butonu
st.sidebar.subheader("Bildirim Alarmı")

alarm_btn_label = "Bildirim Alarmı Kur" if not st.session_state.show_alarm_panel else "Bildirim Panelini Kapat"
if st.sidebar.button(alarm_btn_label, use_container_width=True):
    st.session_state.show_alarm_panel = not st.session_state.show_alarm_panel
    st.session_state.alarm_success_msg = ""

if st.session_state.show_alarm_panel:
    with st.sidebar.container(border=True):
        st.markdown("**Bildirim Kanalı Seçin**")
        alarm_channel = st.radio(
            "Kanal",
            options=["Telegram", "E-Posta"],
            index=0,
            label_visibility="collapsed",
            key="alarm_channel_radio"
        )

        if alarm_channel == "Telegram":
            alarm_address = st.text_input(
                "Telegram Chat ID",
                placeholder="Örnek: 123456789",
                help="Telegram botunuzun Chat ID'sini giriniz. @userinfobot ile öğrenebilirsiniz.",
                key="alarm_tg_address"
            )
        else:
            alarm_address = st.text_input(
                "E-Posta Adresi",
                placeholder="ornek@mail.com",
                key="alarm_email_address"
            )

        st.markdown("**Alarm Kriterleri**")
        alarm_skills = st.multiselect(
            "Yetenek / Dil Filtresi",
            options=sorted_skills,
            default=selected_user_skills if selected_user_skills else [],
            placeholder="Seçim yapınız...",
            key="alarm_skills"
        )
        alarm_job_types = st.multiselect(
            "Çalışma Tipi",
            options=["Uzaktan", "Ofis / Hibrit"],
            default=[],
            placeholder="Seçim yapınız...",
            key="alarm_job_types"
        )
        alarm_levels = st.multiselect(
            "Kıdem Seviyesi",
            options=["Başlangıç (Junior)", "Orta Seviye (Mid)", "Kıdemli (Senior)"],
            default=[],
            placeholder="Seçim yapınız...",
            key="alarm_levels"
        )

        col_save, col_cancel = st.columns(2)
        with col_save:
            st.markdown('<div class="alarm-save-btn">', unsafe_allow_html=True)
            if st.button("Kaydet", key="alarm_save_btn", use_container_width=True):
                msg = save_alarm_rule(
                    alarm_channel,
                    alarm_address,
                    alarm_skills,
                    alarm_job_types,
                    alarm_levels
                )
                st.session_state.alarm_success_msg = msg
                if "Alarm kuruldu" in msg:
                    st.session_state.show_alarm_panel = False
            st.markdown('</div>', unsafe_allow_html=True)
        with col_cancel:
            st.markdown('<div class="alarm-cancel-btn">', unsafe_allow_html=True)
            if st.button("İptal", key="alarm_cancel_btn", use_container_width=True):
                st.session_state.show_alarm_panel = False
                st.session_state.alarm_success_msg = ""
            st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.alarm_success_msg:
    if "Alarm kuruldu" in st.session_state.alarm_success_msg:
        st.sidebar.success(st.session_state.alarm_success_msg)
    else:
        st.sidebar.error(st.session_state.alarm_success_msg)

# Kayıtlı alarmları göster
if st.session_state.saved_alarms:
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Aktif Alarmlar ({len(st.session_state.saved_alarms)})**")
    for i, alarm in enumerate(st.session_state.saved_alarms):
        icon = "[Telegram]" if alarm['channel'] == 'Telegram' else "[E-Posta]"
        st.sidebar.caption(f"{icon} {alarm['channel']} | {alarm['summary'][:40]}..." if len(alarm['summary']) > 40 else f"{icon} {alarm['channel']} | {alarm['summary']}")

st.sidebar.divider()

# Section title & button
st.sidebar.subheader("İlan Akışı & Sistem Güncelleme")

if st.sidebar.button("Canlı Verileri Güncelle (RemoteOK & Arbeitnow)", use_container_width=True):
    with st.spinner("Gerçek canlı API kaynaklarından veriler çekiliyor ve Türkçe'ye çevriliyor..."):
        scraper = WebScraper()
        res = scraper.run_pipeline()
        st.sidebar.success(res.get("message", "İşlem tamamlandı!"))
        st.cache_data.clear()
        st.rerun()

# Apply Filtering Logic
filtered_df = df.copy() if not df.empty else pd.DataFrame()

if not filtered_df.empty:
    if selected_user_skills:
        scores = []
        matching_indices = []
        for idx, r in filtered_df.iterrows():
            sc, _, _, matched_skills = calculate_match_score(r['Yetenekler'], selected_user_skills, r['Başlık'], r['Açıklama'])
            if len(matched_skills) > 0:
                scores.append(sc)
                matching_indices.append(idx)
        
        filtered_df = filtered_df.loc[matching_indices].copy()
        if not filtered_df.empty:
            filtered_df["MatchScore"] = scores
            filtered_df = filtered_df.sort_values(by="MatchScore", ascending=False)
    
    if job_type_filter:
        filtered_df = filtered_df[filtered_df["Çalışma Tipi"].isin(job_type_filter)]
        
    if experience_filter:
        filtered_df = filtered_df[filtered_df["Kıdem"].isin(experience_filter)]

    if location_filter:
        filtered_df = filtered_df[filtered_df["Lokasyon"].isin(location_filter)]

    if freshness_filter != "Tüm Zamanlar" and "RawDate" in filtered_df.columns:
        now = datetime.utcnow()
        if freshness_filter == "Son 24 Saat":
            cutoff = now - timedelta(days=1)
        elif freshness_filter == "Son 3 Gün":
            cutoff = now - timedelta(days=3)
        elif freshness_filter == "Son 7 Gün":
            cutoff = now - timedelta(days=7)
        else:
            cutoff = None

        if cutoff:
            filtered_df = filtered_df[filtered_df["RawDate"] >= cutoff]

    if search_query:
        query_lower = search_query.lower()
        filtered_df = filtered_df[
            filtered_df["Başlık"].str.lower().str.contains(query_lower) |
            filtered_df["Şirket"].str.lower().str.contains(query_lower)
        ]

# Dashboard KPIs
if not filtered_df.empty:
    total_jobs = len(filtered_df)
    remote_jobs_count = len(filtered_df[filtered_df["Çalışma Tipi"] == "Uzaktan"])
    remote_ratio = round((remote_jobs_count / total_jobs) * 100, 1) if total_jobs > 0 else 0
    unique_companies = filtered_df["Şirket"].nunique()
    
    all_skills = [skill for sublist in filtered_df["Yetenekler"] for skill in sublist]
    top_skill = Counter(all_skills).most_common(1)[0][0] if all_skills else "N/A"

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric("Eşleşen İlan Sayısı", total_jobs)
    with kpi2:
        st.metric("Uzaktan Çalışma Oranı", f"%{remote_ratio}")
    with kpi3:
        st.metric("Aktif Şirket Sayısı", unique_companies)
    with kpi4:
        st.metric("En Çok İstenen Yetenek", top_skill)

    st.divider()

    # Visualizations
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.subheader("En Çok Aranan Yazılım Dilleri & Uygulamalar")
        if all_skills:
            skill_counts = pd.DataFrame(Counter(all_skills).most_common(10), columns=["Teknoloji / Araç", "İlan Sayısı"])
            fig_skills = px.bar(
                skill_counts,
                x="İlan Sayısı",
                y="Teknoloji / Araç",
                orientation="h",
                color="İlan Sayısı",
                color_continuous_scale="Purples",
                template="plotly_white"
            )
            fig_skills.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False, margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig_skills, use_container_width=True)
        else:
            st.write("Beceri verisi bulunamadı.")

    with col_chart2:
        st.subheader("Çalışma Tipi Dağılımı")
        job_type_counts = filtered_df["Çalışma Tipi"].value_counts().reset_index()
        job_type_counts.columns = ["Çalışma Tipi", "Sayı"]
        fig_donut = px.pie(
            job_type_counts,
            names="Çalışma Tipi",
            values="Sayı",
            hole=0.5,
            color_discrete_sequence=["#334155", "#64748B", "#94A3B8"],
            template="plotly_white"
        )
        fig_donut.update_layout(margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_donut, use_container_width=True)

    st.divider()

    # Data Export & Tabs
    col_tab_head, col_export = st.columns([3, 1])
    with col_export:
        csv_data = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Filtrelenen Verileri CSV Olarak İndir",
            data=csv_data,
            file_name="filtrelenmis_is_ilanlari.csv",
            mime="text/csv",
            use_container_width=True
        )

    # Retrieve current user/guest favorite IDs
    if st.session_state.user:
        fav_job_ids = get_user_favorite_job_ids(st.session_state.user["id"])
    else:
        fav_job_ids = st.session_state.guest_favorites

    tab_listings, tab_favorites, tab_roadmap, tab_logs = st.tabs([
        "Canlı İlan Detayları",
        f"Favori İlanlarım ({len(fav_job_ids)})",
        "🎓 Yetenek Açığı & Yol Haritası",
        "Otomasyon Logları"
    ])

    with tab_listings:
        st.subheader("Detaylı İlan Kartları & AI Kariyer Uyum Skoru")
        for _, row in filtered_df.iterrows():
            render_job_card(row, selected_user_skills, is_fav=(row['ID'] in fav_job_ids), key_prefix="list")

    with tab_favorites:
        st.subheader("Favorilere Eklediğiniz İlanlar")
        fav_df = df[df["ID"].isin(fav_job_ids)].copy() if not df.empty and fav_job_ids else pd.DataFrame()
        if not fav_df.empty:
            for _, row in fav_df.iterrows():
                render_job_card(row, selected_user_skills, is_fav=True, key_prefix="fav")
        else:
            st.info("Henüz favorilere eklediğiniz bir ilan bulunmuyor. İlan kartlarındaki '☆ Favorilere Ekle' butonuna basarak ilanları buraya kaydedebilirsiniz.")

    with tab_roadmap:
        st.subheader("🎓 Yetenek Açığı & Kişiselleştirilmiş Gelişim Yol Haritası")
        st.caption("Mevcut teknolojileriniz ile canlı piyasadaki iş ilanlarının aradığı becerilerin yapay zeka ile kıyaslanması.")

        active_user_skills = selected_user_skills if selected_user_skills else cv_skills
        roadmap_data = ai_analyzer.generate_skill_gap_roadmap(active_user_skills, df.to_dict('records') if not df.empty else [])

        r_col1, r_col2 = st.columns([2, 1])
        with r_col1:
            st.markdown("**Mevcut Yetenek Kümeniz:**")
            if active_user_skills:
                st.write(", ".join([f"`{s}`" for s in active_user_skills]))
            else:
                st.info("Henüz yetenek seçilmedi veya CV yüklenmedi. Yan menüden yetenek seçebilir ya da PDF CV'nizi yükleyebilirsiniz.")

        with r_col2:
            boost = roadmap_data.get("boost_potential_pct", 0)
            st.metric("Eşleşme Artış Potansiyeli", f"+ %{boost}")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### 🎯 Piyasadaki En Kritik Eksik Teknolojileriniz (Skill Gap)")
        
        top_missing = roadmap_data.get("top_missing_skills", [])
        if top_missing:
            m_cols = st.columns(min(len(top_missing), 5))
            for idx, item in enumerate(top_missing):
                with m_cols[idx]:
                    st.markdown(f"""
                    <div style="background-color:#F8FAFC; border:1px solid #CBD5E1; border-radius:10px; padding:12px; text-align:center;">
                        <div style="font-weight:800; font-size:1.05rem; color:#0F172A;">{item['skill']}</div>
                        <div style="color:#2563EB; font-weight:700; font-size:0.85rem; margin-top:4px;">%{item['demand_percentage']} Piyasa Talebi</div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("#### 💡 Kişiselleştirilmiş Öğrenme & Gelişim Tavsiyeleri")
            for rec in roadmap_data.get("recommendations", []):
                with st.expander(f"📌 {rec['skill']} — {rec['demand']}"):
                    st.write(rec["tip"])
        else:
            st.success("Tebrikler! Mevcut yetenek kümeniz canlı piyasadaki en popüler tüm teknolojileri kapsıyor.")

    with tab_logs:
        st.subheader("Son Otomasyon Çalıştırma Kayıtları")
        if not log_df.empty:
            st.dataframe(log_df, use_container_width=True)
        else:
            st.write("Henüz log kaydı bulunmuyor.")

else:
    st.warning("Seçtiğiniz yetenek ve filtrelere uyan ilan bulunamadı. Yan menüden 'Canlı Verileri Güncelle' butonuna basabilir veya filtrelerinizi genişletebilirsiniz.")

# ─── Floating AI Assistant Chat Bot Widget (Fixed Bottom-Right Corner) ───
if not st.session_state.show_ai_chat_modal:
    st.markdown('<div class="floating-ai-fab-btn">', unsafe_allow_html=True)
    if st.button("🤖 AI Asistanı", key="open_ai_chat_fab"):
        st.session_state.show_ai_chat_modal = True
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="floating-chat-modal-wrapper">', unsafe_allow_html=True)
    with st.container(border=True):
        col_c_head, col_c_close = st.columns([4, 1])
        with col_c_head:
            st.markdown("<h5 style='margin:0; padding:0; color:#0F172A;'>🤖 AI Asistanı</h5>", unsafe_allow_html=True)
            st.caption("Site kullanımı ve canlı destek.")
        with col_c_close:
            if st.button("✕", key="close_ai_chat_fab"):
                st.session_state.show_ai_chat_modal = False
                st.rerun()
        
        st.divider()

        # Context data for statistics
        context_data = {
            "total_jobs": len(filtered_df) if not filtered_df.empty else (len(df) if not df.empty else 0),
            "remote_ratio": round((len(df[df["Çalışma Tipi"] == "Uzaktan"]) / max(1, len(df))) * 100, 1) if not df.empty else 0,
            "unique_companies": df["Şirket"].nunique() if not df.empty else 0,
            "top_skill": Counter([s for sub in df["Yetenekler"] for s in sub]).most_common(1)[0][0] if not df.empty and "Yetenekler" in df.columns else "Python"
        }

        # Hızlı Soru Butonları
        st.markdown("<small><b>Hızlı Konular:</b></small>", unsafe_allow_html=True)
        cq1, cq2 = st.columns(2)
        with cq1:
            if st.button("📄 CV Yükleme", key="chat_quick_cv", use_container_width=True):
                st.session_state.chat_history.append({"role": "user", "content": "CV nasıl yüklenir ve Uyum Skoru nasıl hesaplanır?"})
                ans = ai_analyzer.ask_platform_agent("CV nasıl yüklenir ve Uyum Skoru nasıl hesaplanır?", context_data)
                st.session_state.chat_history.append({"role": "assistant", "content": ans})
                st.rerun()
            if st.button("🔔 Alarm Kurma", key="chat_quick_alarm", use_container_width=True):
                st.session_state.chat_history.append({"role": "user", "content": "Bildirim alarmı nasıl kurulur?"})
                ans = ai_analyzer.ask_platform_agent("Bildirim alarmı nasıl kurulur?", context_data)
                st.session_state.chat_history.append({"role": "assistant", "content": ans})
                st.rerun()
        with cq2:
            if st.button("⭐ Favoriler", key="chat_quick_fav", use_container_width=True):
                st.session_state.chat_history.append({"role": "user", "content": "Favori ilanlarıma nereden bakabilirim?"})
                ans = ai_analyzer.ask_platform_agent("Favori ilanlarıma nereden bakabilirim?", context_data)
                st.session_state.chat_history.append({"role": "assistant", "content": ans})
                st.rerun()
            if st.button("📊 İstatistikler", key="chat_quick_stats", use_container_width=True):
                st.session_state.chat_history.append({"role": "user", "content": "Günün piyasa istatistikleri nelerdir?"})
                ans = ai_analyzer.ask_platform_agent("Günün piyasa istatistikleri nelerdir?", context_data)
                st.session_state.chat_history.append({"role": "assistant", "content": ans})
                st.rerun()

        # Render chat history
        chat_container = st.container(height=180)
        with chat_container:
            for msg in st.session_state.chat_history:
                if msg["role"] == "user":
                    st.markdown(f"<div class='chat-bubble-user'><b>Siz:</b> {msg['content']}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='chat-bubble-assistant'>{msg['content']}</div>", unsafe_allow_html=True)

        # Chat Input Box
        user_input = st.text_input("Sorunuz...", key="chat_user_input_field", placeholder="Örn: CV nasıl yüklenir?", label_visibility="collapsed")
        if st.button("Gönder", key="chat_send_btn", use_container_width=True):
            if user_input.strip():
                st.session_state.chat_history.append({"role": "user", "content": user_input.strip()})
                ans = ai_analyzer.ask_platform_agent(user_input.strip(), context_data)
                st.session_state.chat_history.append({"role": "assistant", "content": ans})
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
