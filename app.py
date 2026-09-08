from pathlib import Path
import io
import hashlib
import os
import re
import tempfile
import requests
from groq import Groq

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit.components.v1 as components
from html import escape

from database.connection import get_connection, is_cloud_database
from api.crickbuzz_client import CrickbuzzClient

try:
    from streamlit_mic_recorder import mic_recorder
except ImportError:
    mic_recorder = None


# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Cricbuzz LiveStats",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================
# SINGLE-FILE NAVIGATION
# =========================================================
if "current_page" not in st.session_state:
    st.session_state.current_page = "Landing"

def go_to(page_name):
    st.session_state.current_page = page_name
    st.rerun()


@st.cache_data(ttl=180, show_spinner=False)
def fetch_match_data(category):
    """Cache RapidAPI match responses for 3 minutes to reduce 429 errors."""
    client = CrickbuzzClient()
    if category == "live":
        return client.get_live_matches()
    if category == "upcoming":
        return client.get_upcoming_matches()
    if category == "recent":
        return client.get_recent_matches()
    return {}


# =========================================================
# PATH
# =========================================================
BASE_DIR = Path(__file__).parent
LANDING_VIDEO = BASE_DIR / "assets" / "landing_video.mp4"


# =========================================================
# DATABASE COUNTS
# =========================================================
def get_dashboard_counts():

    default_values = {
        "matches": 89,
        "players": 1090,
        "teams": 95,
        "series": 19,
    }

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM matches")
        matches = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM players")
        players = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM teams")
        teams = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM series")
        series = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        return {
            "matches": matches,
            "players": players,
            "teams": teams,
            "series": series,
        }

    except Exception:
        return default_values


counts = get_dashboard_counts()


# =========================================================
# GLOBAL CSS
# =========================================================
st.markdown(
    """
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');


/* =========================================================
   GLOBAL
========================================================= */

html {
    scroll-behavior: smooth;
}

body {
    margin: 0;
    padding: 0;
    background: #05070c;
}

html,
body,
.stApp {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background:
        radial-gradient(
            circle at 82% 36%,
            rgba(128, 47, 225, 0.055),
            transparent 30%
        ),
        #05070c;

    color: white;
}


header[data-testid="stHeader"] {
    background: transparent;
}

[data-testid="stToolbar"] {
    display: none;
}

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

.block-container {
    padding: 0 !important;
    max-width: 100% !important;
}


/* =========================================================
   LANDING VIDEO
========================================================= */

[data-testid="stVideo"] {
    width: 100% !important;
    max-width: 100% !important;

    margin: 0 !important;
    padding: 0 !important;

    overflow: hidden !important;

    border-radius: 0 !important;

    background: #000 !important;
}


[data-testid="stVideo"] video {
    width: 100% !important;
    height: 100vh !important;

    display: block !important;

    object-fit: cover !important;

    background: #000 !important;

    pointer-events: none !important;

    border-radius: 0 !important;
}


/* REMOVE VIDEO CONTROLS */

[data-testid="stVideo"] video::-webkit-media-controls {
    display: none !important;
}

[data-testid="stVideo"] video::-webkit-media-controls-enclosure {
    display: none !important;
}

[data-testid="stVideo"] video::-webkit-media-controls-panel {
    display: none !important;
}

[data-testid="stVideo"] video::-webkit-media-controls-play-button {
    display: none !important;
}

[data-testid="stVideo"] video::-webkit-media-controls-timeline {
    display: none !important;
}

[data-testid="stVideo"] video::-webkit-media-controls-current-time-display {
    display: none !important;
}

[data-testid="stVideo"] video::-webkit-media-controls-time-remaining-display {
    display: none !important;
}

[data-testid="stVideo"] video::-webkit-media-controls-mute-button {
    display: none !important;
}

[data-testid="stVideo"] video::-webkit-media-controls-volume-slider {
    display: none !important;
}

[data-testid="stVideo"] video::-webkit-media-controls-fullscreen-button {
    display: none !important;
}


/* VIDEO BOTTOM FADE */

.hero-fade {
    position: relative;

    z-index: 3;

    height: 145px;

    margin-top: -145px;

    pointer-events: none;

    background:
        linear-gradient(
            to bottom,
            transparent,
            rgba(5,7,12,0.75),
            #05070c
        );
}


/* SCROLL INDICATOR */

.scroll-area {
    position: relative;

    z-index: 5;

    margin-top: -78px;

    padding-bottom: 38px;

    text-align: center;
}

.scroll-area span {
    color: rgba(255,255,255,0.82);

    font-family: 'Space Grotesk', sans-serif;

    font-size: 10px;

    font-weight: 600;

    letter-spacing: 5px;

    text-transform: uppercase;
}

.scroll-arrow {
    margin-top: 8px;

    font-size: 29px;

    color: #a652ff;

    text-shadow:
        0 0 10px #aa58ff,
        0 0 28px #7928ff,
        0 0 50px rgba(122,40,255,0.60);

    animation:
        bounce 1.6s
        ease-in-out
        infinite;
}

@keyframes bounce {

    0%, 100% {
        transform: translateY(0);
    }

    50% {
        transform: translateY(9px);
    }

}


/* =========================================================
   INTRO
========================================================= */

.intro-section {
    position: relative;

    max-width: 1180px;

    margin: auto;

    padding:
        130px
        55px
        120px;

    overflow: hidden;
}

.intro-content {
    position: relative;

    z-index: 3;

    max-width: 1050px;
}

.intro-tag {
    color: #aa67ff;

    font-family:
        'Space Grotesk',
        sans-serif;

    font-size: 11px;

    font-weight: 600;

    letter-spacing: 5px;

    text-transform: uppercase;
}

.intro-title {
    margin-top: 25px;

    font-family:
        'Space Grotesk',
        sans-serif;

    font-size:
        clamp(
            52px,
            6vw,
            80px
        );

    font-weight: 600;

    letter-spacing: -3px;

    line-height: 1.07;
}

.intro-title .purple {
    display: inline-block;

    margin-top: 10px;

    color: #a051ff;

    text-shadow:
        0 0 30px
        rgba(158, 67, 255, 0.18);
}

.intro-description {
    max-width: 760px;

    margin-top: 28px;

    color: #9298a8;

    font-size: 15px;

    line-height: 1.9;
}


/* =========================================================
   GLOWING ORB
========================================================= */

.glow-orb {
    position: absolute;

    width: 340px;
    height: 340px;

    right: 0;
    top: 40px;

    border-radius: 50%;

    background:
        radial-gradient(
            circle,
            rgba(161,72,255,0.17),
            rgba(102,35,190,0.04) 47%,
            transparent 72%
        );

    animation:
        glowPulse
        4s
        ease-in-out
        infinite;
}


.glow-orb::after {
    content: "";

    position: absolute;

    left: 50%;
    top: 50%;

    width: 8px;
    height: 8px;

    transform:
        translate(-50%, -50%);

    border-radius: 50%;

    background: #c58aff;

    box-shadow:
        0 0 15px #ba70ff,
        0 0 45px #9441ff,
        0 0 100px #7422e5;
}


@keyframes glowPulse {

    0%, 100% {
        transform: scale(1);
        opacity: 0.65;
    }

    50% {
        transform: scale(1.11);
        opacity: 1;
    }

}


.glow-line {
    width: 190px;
    height: 2px;

    margin-top: 44px;

    background:
        linear-gradient(
            90deg,
            #a654ff,
            rgba(166,84,255,0.24),
            transparent
        );

    box-shadow:
        0 0 17px
        rgba(161,74,255,0.72);
}


/* =========================================================
   KPI
========================================================= */

.kpi-section {
    padding:
        100px
        7%
        125px;

    background:
        linear-gradient(
            180deg,
            transparent,
            rgba(95,29,172,0.038),
            transparent
        );
}


.kpi-heading-row {
    max-width: 1180px;

    margin:
        0 auto
        50px;

    display: flex;

    justify-content: space-between;

    align-items: flex-end;

    gap: 40px;
}


.kpi-heading {
    font-family:
        'Space Grotesk',
        sans-serif;

    font-size: 44px;

    font-weight: 600;

    letter-spacing: -2px;
}


.kpi-heading span {
    color: #a55fff;
}


.kpi-description {
    max-width: 410px;

    color: #7f8595;

    font-size: 14px;

    line-height: 1.7;
}


.kpi-grid {
    max-width: 1180px;

    margin: auto;

    display: grid;

    grid-template-columns:
        repeat(4, 1fr);

    gap: 18px;
}


.kpi-card {
    position: relative;

    min-height: 155px;

    padding:
        30px
        27px;

    border-radius: 19px;

    background:
        linear-gradient(
            145deg,
            rgba(18,19,30,0.97),
            rgba(10,11,18,0.97)
        );

    border:
        1px solid
        rgba(153,86,255,0.20);

    transition:
        transform 0.3s ease,
        border-color 0.3s ease,
        box-shadow 0.3s ease;
}


.kpi-card:hover {
    transform: translateY(-7px);

    border-color:
        rgba(167,98,255,0.70);

    box-shadow:
        0 17px 48px
        rgba(92,32,176,0.16);
}


.kpi-index {
    position: absolute;

    top: 18px;
    right: 22px;

    color: #4b5160;

    font-size: 10px;

    letter-spacing: 2px;
}


.kpi-number {
    margin-top: 30px;

    font-family:
        'Space Grotesk',
        sans-serif;

    font-size: 43px;

    font-weight: 600;

    color: #d3b5ff;
}


.kpi-label {
    margin-top: 7px;

    color: #777d8d;

    font-size: 11px;

    letter-spacing: 2.5px;

    text-transform: uppercase;
}


/* =========================================================
   FEATURES
========================================================= */

.features {
    max-width: 1180px;

    margin: auto;

    padding:
        100px
        40px
        125px;
}


.features-header {
    text-align: center;

    margin-bottom: 52px;
}


.features-header .small {
    color: #a45fff;

    font-size: 10px;

    font-weight: 600;

    letter-spacing: 5px;

    text-transform: uppercase;
}


.features-header h2 {
    margin:
        15px
        0
        0;

    font-family:
        'Space Grotesk',
        sans-serif;

    font-size: 44px;

    font-weight: 600;

    letter-spacing: -1.8px;
}


.features-header p {
    margin-top: 14px;

    color: #7d8393;

    font-size: 14px;
}


.feature-grid {
    display: grid;

    grid-template-columns:
        repeat(3, 1fr);

    gap: 18px;
}


.feature-card {
    min-height: 205px;

    padding: 31px;

    border-radius: 19px;

    background:
        rgba(13,14,23,0.92);

    border:
        1px solid
        rgba(150,82,255,0.18);

    transition:
        transform 0.3s ease,
        border-color 0.3s ease,
        box-shadow 0.3s ease;
}


.feature-card:hover {
    transform: translateY(-6px);

    border-color:
        rgba(164,95,255,0.66);

    box-shadow:
        0 17px 45px
        rgba(92,30,170,0.13);
}


.feature-tag {
    display: flex;

    align-items: center;

    justify-content: center;

    width: fit-content;

    min-width: 42px;

    height: 38px;

    padding:
        0
        11px;

    border-radius: 9px;

    border:
        1px solid
        rgba(164,94,255,0.31);

    background:
        rgba(113,43,213,0.08);

    color: #b87bff;

    font-family:
        'Space Grotesk',
        sans-serif;

    font-size: 10px;

    font-weight: 700;

    letter-spacing: 1px;
}


.feature-title {
    margin-top: 25px;

    font-family:
        'Space Grotesk',
        sans-serif;

    font-size: 19px;

    font-weight: 600;
}


.feature-description {
    margin-top: 12px;

    color: #858b9a;

    font-size: 13px;

    line-height: 1.75;
}


/* =========================================================
   CTA
========================================================= */

.cta {
    position: relative;

    max-width: 1000px;

    margin: auto;

    padding:
        110px
        30px
        35px;

    text-align: center;
}


.cta::before {
    content: "";

    position: absolute;

    width: 420px;
    height: 220px;

    left: 50%;
    top: 45%;

    transform:
        translate(-50%, -50%);

    background:
        radial-gradient(
            ellipse,
            rgba(137,55,255,0.12),
            transparent 70%
        );

    pointer-events: none;
}


.cta-mini {
    position: relative;

    z-index: 2;

    color: #a45fff;

    font-size: 10px;

    font-weight: 600;

    letter-spacing: 5px;

    text-transform: uppercase;
}


.cta h2 {
    position: relative;

    z-index: 2;

    margin:
        16px
        0
        13px;

    font-family:
        'Space Grotesk',
        sans-serif;

    font-size:
        clamp(
            52px,
            6vw,
            72px
        );

    font-weight: 600;

    letter-spacing: -3px;
}


.cta h2 span {
    color: #a85fff;

    text-shadow:
        0 0 30px
        rgba(150,68,255,0.20);
}


.cta p {
    position: relative;

    z-index: 2;

    color: #858b9a;

    font-size: 15px;

    line-height: 1.7;
}


/* =========================================================
   DASHBOARD BUTTON
========================================================= */

div.stButton {
    width: 100%;
}


div.stButton > button {
    width: 100% !important;

    min-height: 70px !important;

    border-radius: 100px !important;

    border:
        1px solid
        rgba(211,169,255,0.96) !important;

    background:
        linear-gradient(
            110deg,
            #5d20cc 0%,
            #8536ee 48%,
            #a94eff 100%
        ) !important;

    color: #ffffff !important;

    font-family:
        'Space Grotesk',
        sans-serif !important;

    font-size: 19px !important;

    font-weight: 600 !important;

    letter-spacing: 0.2px !important;

    box-shadow:
        0 0 18px
        rgba(157,75,255,0.55),
        0 0 48px
        rgba(119,44,220,0.34),
        inset 0 1px 0
        rgba(255,255,255,0.20) !important;

    transition:
        all 0.30s ease !important;

    animation:
        buttonGlow
        2.5s
        ease-in-out
        infinite;
}


div.stButton > button:hover {
    transform:
        translateY(-4px)
        scale(1.025) !important;

    border-color:
        #f0e0ff !important;

    color: white !important;

    box-shadow:
        0 0 28px
        rgba(183,102,255,0.88),
        0 0 70px
        rgba(128,44,238,0.55),
        inset 0 1px 0
        rgba(255,255,255,0.28) !important;
}


@keyframes buttonGlow {

    0%, 100% {
        box-shadow:
            0 0 18px
            rgba(157,75,255,0.48),
            0 0 42px
            rgba(119,44,220,0.26);
    }

    50% {
        box-shadow:
            0 0 28px
            rgba(172,88,255,0.74),
            0 0 64px
            rgba(121,44,229,0.44);
    }

}


/* =========================================================
   FOOTER
========================================================= */

.custom-footer {
    margin-top: 80px;

    padding:
        34px
        20px;

    text-align: center;

    border-top:
        1px solid
        rgba(255,255,255,0.05);

    color: #505563;

    font-size: 10px;

    letter-spacing: 3px;
}


/* =========================================================
   MOBILE
========================================================= */

@media(max-width: 900px) {

    [data-testid="stVideo"] video {
        height: auto !important;
        min-height: 55vh;
    }

    .intro-section {
        padding:
            85px
            25px;
    }

    .glow-orb {
        right: -140px;
        opacity: 0.45;
    }

    .kpi-heading-row {
        display: block;
    }

    .kpi-description {
        margin-top: 15px;
    }

    .kpi-grid {
        grid-template-columns:
            repeat(2, 1fr);
    }

    .feature-grid {
        grid-template-columns: 1fr;
    }

}

</style>
""",
    unsafe_allow_html=True,
)


if st.session_state.current_page == "Landing":
    # =========================================================
    # 1. LANDING VIDEO
    # =========================================================
    if LANDING_VIDEO.exists():

        st.video(
            str(LANDING_VIDEO),
            format="video/mp4",
            autoplay=True,
            muted=True,
            loop=False,
        )

        st.markdown(
            """
    <div class="hero-fade"></div>

    <div class="scroll-area">

    <span>
    Scroll to Explore
    </span>

    <div class="scroll-arrow">
    ↓
    </div>

    </div>
    """,
            unsafe_allow_html=True,
        )

    else:

        st.error(
            "assets/landing_video.mp4 not found."
        )


    # =========================================================
    # 2. INTRO
    # =========================================================
    st.markdown(
        """
    <div class="intro-section">

    <div class="glow-orb"></div>

    <div class="intro-content">

    <div class="intro-tag">
    Where Cricket Meets Intelligence
    </div>

    <div class="intro-title">

    THE GAME MOVES FAST.<br>

    <span class="purple">
    THE DATA MOVES FASTER.
    </span>

    </div>

    <div class="intro-description">

    Every ball creates information. Every performance creates a pattern.
    Cricbuzz LiveStats transforms that raw match data into meaningful,
    interactive cricket intelligence.

    </div>

    <div class="glow-line"></div>

    </div>

    </div>
    """,
        unsafe_allow_html=True,
    )


    # =========================================================
    # 3. KPI
    # =========================================================
    st.markdown(
        f"""
    <div class="kpi-section">

    <div class="kpi-heading-row">

    <div class="kpi-heading">

    Data at a
    <span>
    Glance.
    </span>

    </div>

    <div class="kpi-description">

    A quick look at the real cricket records
    currently powering the analytics platform.

    </div>

    </div>


    <div class="kpi-grid">


    <div class="kpi-card">

    <div class="kpi-index">
    01
    </div>

    <div class="kpi-number">
    {counts["matches"]:,}
    </div>

    <div class="kpi-label">
    Matches
    </div>

    </div>


    <div class="kpi-card">

    <div class="kpi-index">
    02
    </div>

    <div class="kpi-number">
    {counts["players"]:,}
    </div>

    <div class="kpi-label">
    Players
    </div>

    </div>


    <div class="kpi-card">

    <div class="kpi-index">
    03
    </div>

    <div class="kpi-number">
    {counts["teams"]:,}
    </div>

    <div class="kpi-label">
    Teams
    </div>

    </div>


    <div class="kpi-card">

    <div class="kpi-index">
    04
    </div>

    <div class="kpi-number">
    {counts["series"]:,}
    </div>

    <div class="kpi-label">
    Series
    </div>

    </div>


    </div>

    </div>
    """,
        unsafe_allow_html=True,
    )


    # =========================================================
    # 4. FEATURES
    # =========================================================
    st.markdown(
        """
    <div class="features">

    <div class="features-header">

    <div class="small">
    Inside Cricbuzz LiveStats
    </div>

    <h2>
    Complete Cricket Intelligence.
    </h2>

    <p>
    Everything you need to explore modern cricket data.
    </p>

    </div>


    <div class="feature-grid">


    <div class="feature-card">

    <div class="feature-tag">
    LIVE
    </div>

    <div class="feature-title">
    Live Match Center
    </div>

    <div class="feature-description">

    Explore live, upcoming and recent cricket matches
    through real-time cricket API integration.

    </div>

    </div>


    <div class="feature-card">

    <div class="feature-tag">
    BAT
    </div>

    <div class="feature-title">
    Player Analytics
    </div>

    <div class="feature-description">

    Analyze top run scorers, wicket takers,
    strike rates and match performances.

    </div>

    </div>


    <div class="feature-card">

    <div class="feature-tag">
    SQL
    </div>

    <div class="feature-title">
    SQL Intelligence
    </div>

    <div class="feature-description">

    Explore cricket insights through
    25 structured analytical SQL queries.

    </div>

    </div>


    <div class="feature-card">

    <div class="feature-tag">
    API
    </div>

    <div class="feature-title">
    Real-Time Data
    </div>

    <div class="feature-description">

    Connect with the Crickbuzz API
    to retrieve current match information.

    </div>

    </div>


    <div class="feature-card">

    <div class="feature-tag">
    DB
    </div>

    <div class="feature-title">
    Database Management
    </div>

    <div class="feature-description">

    Perform Create, Read, Update and Delete
    operations through the dashboard.

    </div>

    </div>


    <div class="feature-card">

    <div class="feature-tag">
    AI
    </div>

    <div class="feature-title">
    AI Voice Assistant
    </div>

    <div class="feature-description">

    Ask cricket database questions or general
    questions using text and voice.

    </div>

    </div>


    </div>

    </div>
    """,
        unsafe_allow_html=True,
    )


    # =========================================================
    # 5. CTA
    # =========================================================
    st.markdown(
        """
    <div class="cta">

    <div class="cta-mini">
    Your Cricket Intelligence Hub
    </div>

    <h2>

    Enter the
    <span>
    Arena.
    </span>

    </h2>

    <p>

    Explore live matches, player performance,
    SQL analytics and AI-powered cricket intelligence.

    </p>

    </div>
    """,
        unsafe_allow_html=True,
    )


    # =========================================================
    # CENTERED GLOWING BUTTON
    # =========================================================
    left_space, button_column, right_space = st.columns(
        [1.05, 0.90, 1.05]
    )

    with button_column:

        if st.button(
            "Explore Dashboard  →",
            use_container_width=True,
        ):

            go_to("Dashboard")


    # =========================================================
    # FOOTER
    # =========================================================
    st.markdown(
        """
    <div class="custom-footer">

    CRICBUZZ LIVESTATS
    &nbsp;&nbsp;•&nbsp;&nbsp;
    REAL-TIME CRICKET ANALYTICS

    </div>
    """,
        unsafe_allow_html=True,
    )

else:
    st.markdown(
        """
<style>
.block-container{max-width:1500px!important;padding:2.1rem 3rem 4rem!important;}
section[data-testid="stSidebar"]{
    display:flex!important;
    visibility:visible!important;
    opacity:1!important;
    transform:none!important;

    width:340px!important;
    min-width:340px!important;
    max-width:340px!important;

    position:relative!important;
    left:0!important;
    right:auto!important;

    order:0!important;

    background:linear-gradient(180deg,#090b14,#06070d)!important;
    border-left:none!important;
    border-right:1px solid rgba(169,99,255,.16)!important;
    box-shadow:16px 0 42px rgba(0,0,0,.18)!important;
}

section[data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div{
    background:linear-gradient(145deg,#111321,#0c0e18)!important;
    border:1px solid rgba(166,95,255,.22)!important;
    border-radius:12px!important;
}
section[data-testid="stSidebar"] [data-testid="stTextInput"] input,
section[data-testid="stSidebar"] [data-testid="stNumberInput"] input{
    background:#0d0f18!important;
    border:1px solid rgba(157,89,255,.22)!important;
    border-radius:10px!important;
}

[data-testid="stAppViewContainer"] > .main{
    order:1!important;
}
[data-testid="stAppViewContainer"]{
    display:flex!important;
    flex-direction:row!important;
}
section[data-testid="stSidebar"] > div,
section[data-testid="stSidebar"] [data-testid="stSidebarContent"]{
    display:block!important;
    visibility:visible!important;
    opacity:1!important;
    width:340px!important;
    min-width:340px!important;
}
[data-testid="stSidebarCollapsedControl"]{display:none!important;}
section[data-testid="stSidebar"]>div{padding-top:.8rem!important;}
section[data-testid="stSidebar"] .stButton>button{min-height:39px!important;height:39px!important;border-radius:10px!important;margin:2px 0!important;padding:0 12px!important;border:1px solid rgba(173,102,255,.18)!important;background:rgba(120,54,210,.055)!important;color:#b9bdc9!important;font-family:'Inter',sans-serif!important;font-size:12px!important;font-weight:600!important;box-shadow:none!important;animation:none!important;transition:.2s ease!important;}
section[data-testid="stSidebar"] .stButton>button:hover{transform:translateX(3px)!important;border-color:rgba(183,112,255,.55)!important;background:linear-gradient(90deg,rgba(109,43,205,.19),rgba(156,71,255,.12))!important;color:#fff!important;box-shadow:0 0 18px rgba(140,58,235,.10)!important;}

/* =========================================================
   DARK THEMED SELECTBOX DROPDOWNS
   BaseWeb renders menus in a portal outside the sidebar,
   so these selectors must be global.
========================================================= */
div[role="listbox"]{
    background:linear-gradient(180deg,#11131f,#0a0c14)!important;
    border:1px solid rgba(169,99,255,.30)!important;
    border-radius:13px!important;
    box-shadow:0 18px 45px rgba(0,0,0,.48),0 0 24px rgba(126,63,215,.10)!important;
    padding:6px!important;
    color:#d8d2e4!important;
}

div[role="option"],
li[role="option"]{
    background:transparent!important;
    color:#c5c2cf!important;
    border-radius:9px!important;
    min-height:42px!important;
    padding:10px 12px!important;
    font-family:'Inter',sans-serif!important;
    font-size:13px!important;
}

div[role="option"]:hover,
li[role="option"]:hover{
    background:linear-gradient(90deg,rgba(121,54,220,.20),rgba(160,86,255,.10))!important;
    color:#ffffff!important;
}

div[role="option"][aria-selected="true"],
li[role="option"][aria-selected="true"]{
    background:linear-gradient(90deg,rgba(127,57,226,.28),rgba(160,86,255,.14))!important;
    color:#d9baff!important;
}

/* BaseWeb popover/menu wrappers */
[data-baseweb="popover"],
[data-baseweb="menu"]{
    background:#0b0d15!important;
    color:#d8d2e4!important;
    border-radius:13px!important;
}

[data-baseweb="menu"] ul{
    background:#0b0d15!important;
}

[data-baseweb="menu"] li{
    background:transparent!important;
    color:#c5c2cf!important;
    min-height:42px!important;
    border-radius:9px!important;
}

[data-baseweb="menu"] li:hover{
    background:rgba(137,66,234,.18)!important;
    color:#fff!important;
}

/* Slightly larger select controls */
section[data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div{
    min-height:48px!important;
    font-size:13.5px!important;
    padding-left:4px!important;
}

main .stButton>button{min-height:42px!important;height:auto!important;border-radius:11px!important;padding:0 18px!important;font-size:13px!important;animation:none!important;box-shadow:0 8px 24px rgba(109,42,205,.12)!important;}
.dash-kicker{color:#a96aff;font-family:'Space Grotesk',sans-serif;font-size:10px;font-weight:700;letter-spacing:4.2px;text-transform:uppercase;margin-bottom:10px;}
.dash-title{color:#f5f3fb;font-family:'Space Grotesk',sans-serif;font-size:clamp(36px,4vw,52px);font-weight:600;letter-spacing:-2.1px;line-height:1.05;margin-bottom:12px;}
.dash-title span{color:#a65fff;text-shadow:0 0 30px rgba(166,95,255,.15);}
.dash-sub{max-width:790px;color:#858b99;font-size:14px;line-height:1.75;margin-bottom:30px;}
[data-testid="stMetric"]{background:linear-gradient(145deg,rgba(17,19,30,.98),rgba(9,10,17,.98));border:1px solid rgba(158,89,255,.16);border-radius:17px;padding:20px 22px;box-shadow:0 14px 40px rgba(0,0,0,.18);}
[data-testid="stMetricLabel"]{color:#777e8e!important;font-size:12px!important;}
[data-testid="stMetricValue"]{color:#d4baff!important;font-family:'Space Grotesk',sans-serif!important;font-weight:600!important;}
.section-title{font-family:'Space Grotesk',sans-serif;color:#f0edf6;font-size:22px;font-weight:600;letter-spacing:-.5px;margin:22px 0 3px;}
.section-note{color:#747b8b;font-size:12px;margin-bottom:14px;}
.table-wrap{overflow-x:auto;border-radius:15px;border:1px solid rgba(162,93,255,.16);background:linear-gradient(145deg,rgba(14,16,25,.98),rgba(8,9,15,.99));box-shadow:0 16px 42px rgba(0,0,0,.16);}
.premium-table{width:100%;border-collapse:collapse;font-size:12px;}
.premium-table thead th{background:linear-gradient(180deg,#17142a,#12101e);color:#caa8ff;text-align:left;font-weight:700;padding:13px 14px;border-bottom:1px solid rgba(170,101,255,.22);white-space:nowrap;}
.premium-table tbody td{color:#c4c8d2;padding:12px 14px;border-bottom:1px solid rgba(255,255,255,.045);white-space:nowrap;}
.premium-table tbody tr:nth-child(even) td{background:rgba(255,255,255,.012);}
.premium-table tbody tr:hover td{background:rgba(145,73,241,.065);color:#fff;}
.match-card{min-height:190px;padding:20px;border-radius:18px;background:linear-gradient(145deg,rgba(18,19,31,.98),rgba(9,10,17,.99));border:1px solid rgba(164,92,255,.17);box-shadow:0 16px 42px rgba(0,0,0,.17);margin-bottom:14px;}
.match-top{display:flex;align-items:center;justify-content:space-between;gap:10px;}
.match-badge{display:inline-flex;padding:5px 9px;border-radius:999px;background:rgba(155,72,255,.10);border:1px solid rgba(177,106,255,.25);color:#bc87ff;font-size:9px;font-weight:800;letter-spacing:1.3px;}
.match-series{color:#676e7d;font-size:10px;max-width:70%;text-align:right;}
.match-teams{font-family:'Space Grotesk',sans-serif;font-size:19px;font-weight:600;color:#f0edf6;margin-top:18px;line-height:1.45;}
.match-vs{color:#8f57d9;font-size:11px;margin:0 7px;}.match-status{color:#9aa0ae;font-size:12px;line-height:1.55;margin-top:13px;}.match-meta{color:#626978;font-size:10px;margin-top:12px;}
.stTextInput input,.stNumberInput input,.stTextArea textarea,div[data-baseweb="select"]>div{background:#0d0f18!important;color:#e8e8ef!important;border-color:rgba(157,89,255,.22)!important;border-radius:10px!important;}
button[data-baseweb="tab"]{color:#7f8696!important;font-family:'Space Grotesk',sans-serif!important;font-size:12px!important;font-weight:600!important;}
button[data-baseweb="tab"][aria-selected="true"]{color:#b778ff!important;}
[data-testid="stCodeBlock"]{border:1px solid rgba(161,91,255,.15);border-radius:14px;overflow:hidden;}
@media(max-width:900px){.block-container{padding:1.4rem 1rem 3rem!important;}}
</style>
        """,
        unsafe_allow_html=True,
    )

    PLOT_BG = "rgba(0,0,0,0)"
    PURPLE = "#9b5cff"
    PURPLE_2 = "#c084fc"
    CYAN = "#54d6ff"
    PINK = "#ff78c8"
    GRID = "rgba(255,255,255,0.07)"
    TEXT = "#c4c8d2"
    MUTED = "#777e8d"

    def style_plot(fig, height=390, legend=True):
        fig.update_layout(
            height=height,
            margin=dict(l=28, r=20, t=55, b=35),
            paper_bgcolor=PLOT_BG,
            plot_bgcolor=PLOT_BG,
            font=dict(family="Inter", color=TEXT, size=11),
            title_font=dict(family="Space Grotesk", color="#f1eef7", size=15),
            showlegend=legend,
            legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#9198a8", size=10), orientation="h", y=1.02, x=1, xanchor="right"),
            hoverlabel=dict(bgcolor="#14111f", bordercolor="#7d45c9", font_color="#ffffff"),
        )
        fig.update_xaxes(showgrid=False, zeroline=False, color=MUTED, tickfont=dict(color="#808696"), title_font=dict(color="#747b89"))
        fig.update_yaxes(gridcolor=GRID, zeroline=False, color=MUTED, tickfont=dict(color="#808696"), title_font=dict(color="#747b89"))
        return fig

    def dark_table(df, max_rows=100):
        if df is None or df.empty:
            st.info("No data available.")
            return
        view = df.head(max_rows).copy()
        html = view.to_html(index=False, escape=True, classes="premium-table", border=0)
        st.markdown(f'<div class="table-wrap">{html}</div>', unsafe_allow_html=True)
        if len(df) > max_rows:
            st.caption(f"Showing first {max_rows:,} of {len(df):,} rows.")

    def section_title(title, note=""):
        st.markdown(f'<div class="section-title">{escape(title)}</div><div class="section-note">{escape(note)}</div>', unsafe_allow_html=True)

    def page_heading(kicker, title, accent, subtitle):
        st.markdown(f'<div class="dash-kicker">{escape(kicker)}</div><div class="dash-title">{escape(title)} <span>{escape(accent)}</span></div><div class="dash-sub">{escape(subtitle)}</div>', unsafe_allow_html=True)

    def _cloud_sql(query):
        """Translate the small T-SQL subset used by this app to SQLite on Streamlit Cloud."""
        q = str(query).strip()
        top_match = re.search(r"(?is)^\s*SELECT\s+TOP\s+(\d+)\s+", q)
        limit = None
        if top_match:
            limit = int(top_match.group(1))
            q = re.sub(r"(?is)^\s*SELECT\s+TOP\s+\d+\s+", "SELECT ", q, count=1)

        # SQLite accepts most of the remaining queries. Normalize SQL Server-only pieces.
        q = re.sub(r"(?i)GETDATE\(\)", "CURRENT_TIMESTAMP", q)
        q = re.sub(
            r"(?i)CAST\(([^()]+)\s+AS\s+DATE\)",
            r"date(\1)",
            q,
        )

        if limit is not None:
            q = q.rstrip().rstrip(";") + f" LIMIT {limit};"
        return q

    def read_sql(query, params=None):
        conn = get_connection()
        try:
            sql = _cloud_sql(query) if is_cloud_database() else query
            return pd.read_sql_query(sql, conn, params=params)
        finally:
            conn.close()

    def safe_int(value):
        try:
            return int(value or 0)
        except Exception:
            return 0

    # =========================================================
    # AI ASSISTANT HELPERS
    # =========================================================
    AI_DEFAULT_QUESTIONS = [
        "Who Is Shivani Mam?",
        "Who is the top run scorer?",
        "Who is the top wicket taker?",
        "Who has the best strike rate?",
        "Give me a database summary",
        "What is LBW in cricket?",
        "Who is the best all-rounder in the database?",
    ]

    def normalize_ai_question(question):
        return re.sub(r"[^a-z0-9]+", " ", str(question).lower()).strip()

    def is_shivani_mam_question(question):
        # Route every Shivani Mam/Ma'am/Madam voice or text variant to the
        # fixed mentor response BEFORE Ollama/SQL. Whisper may hear "Mam" as "Man".
        normalized = normalize_ai_question(question)
        if "shivani" not in normalized:
            return False
        mentor_words = ("mam", "maam", "madam", "man", "ma'am")
        return any(word in normalized.split() for word in mentor_words) or normalized.startswith("who is shivani")

    def remember_ai_question(question):
        if "ai_question_counts" not in st.session_state:
            st.session_state.ai_question_counts = {}
        clean = str(question).strip()
        key = normalize_ai_question(clean)
        if not key:
            return
        current = st.session_state.ai_question_counts.get(key, {"question": clean, "count": 0})
        current["question"] = clean
        current["count"] += 1
        st.session_state.ai_question_counts[key] = current

    def get_top_ai_questions():
        counts_map = st.session_state.get("ai_question_counts", {})
        ranked = sorted(
            counts_map.values(),
            key=lambda item: (-item["count"], item["question"].lower()),
        )
        questions = [item["question"] for item in ranked[:7]]
        for default in AI_DEFAULT_QUESTIONS:
            if normalize_ai_question(default) not in {
                normalize_ai_question(q) for q in questions
            }:
                questions.append(default)
            if len(questions) == 7:
                break
        return questions[:7]

    def ai_db_answer(question):
        """Return a database-grounded answer for supported read-only intents."""
        q = normalize_ai_question(question)

        try:
            if any(phrase in q for phrase in ["database summary", "db summary", "database overview"]):
                row = read_sql("""
                    SELECT
                        (SELECT COUNT(*) FROM matches) AS Matches,
                        (SELECT COUNT(*) FROM players) AS Players,
                        (SELECT COUNT(*) FROM teams) AS Teams,
                        (SELECT COUNT(*) FROM series) AS Series,
                        (SELECT COUNT(*) FROM venues) AS Venues,
                        (SELECT COUNT(*) FROM player_match_stats) AS PlayerStats
                """).iloc[0]
                return (
                    f"Your SQL database currently contains **{safe_int(row['Matches']):,} matches**, "
                    f"**{safe_int(row['Players']):,} players**, **{safe_int(row['Teams']):,} teams**, "
                    f"**{safe_int(row['Series']):,} series**, **{safe_int(row['Venues']):,} venues**, and "
                    f"**{safe_int(row['PlayerStats']):,} player-match stat records**."
                )

            if "total" in q and "player" in q:
                value = read_sql("SELECT COUNT(*) AS Total FROM players").iloc[0]["Total"]
                return f"There are **{safe_int(value):,} players** stored in the SQL database."

            if "total" in q and "team" in q:
                value = read_sql("SELECT COUNT(*) AS Total FROM teams").iloc[0]["Total"]
                return f"There are **{safe_int(value):,} teams** stored in the SQL database."

            if "total" in q and "match" in q:
                value = read_sql("SELECT COUNT(*) AS Total FROM matches").iloc[0]["Total"]
                return f"There are **{safe_int(value):,} matches** stored in the SQL database."

            if "total" in q and "series" in q:
                value = read_sql("SELECT COUNT(*) AS Total FROM series").iloc[0]["Total"]
                return f"There are **{safe_int(value):,} series** stored in the SQL database."

            if "total" in q and "venue" in q:
                value = read_sql("SELECT COUNT(*) AS Total FROM venues").iloc[0]["Total"]
                return f"There are **{safe_int(value):,} venues** stored in the SQL database."

            if ("top" in q or "highest" in q or "most" in q) and "run" in q and "team" not in q:
                df = read_sql("""
                    SELECT TOP 5 p.player_name AS Player, SUM(s.runs) AS Runs
                    FROM player_match_stats s
                    JOIN players p ON s.player_id = p.player_id
                    GROUP BY p.player_name
                    ORDER BY Runs DESC
                """)
                if df.empty:
                    return "No batting records are available in the database yet."
                rows = [f"**{i+1}. {r.Player}** — {safe_int(r.Runs):,} runs" for i, r in enumerate(df.itertuples())]
                return "Top run scorers in your stored data:\n\n" + "\n".join(rows)

            if ("top" in q or "highest" in q or "most" in q) and "wicket" in q and "team" not in q:
                df = read_sql("""
                    SELECT TOP 5 p.player_name AS Player, SUM(s.wickets) AS Wickets
                    FROM player_match_stats s
                    JOIN players p ON s.player_id = p.player_id
                    GROUP BY p.player_name
                    ORDER BY Wickets DESC
                """)
                if df.empty:
                    return "No bowling records are available in the database yet."
                rows = [f"**{i+1}. {r.Player}** — {safe_int(r.Wickets):,} wickets" for i, r in enumerate(df.itertuples())]
                return "Top wicket takers in your stored data:\n\n" + "\n".join(rows)

            if "strike rate" in q or "strike-rate" in q:
                df = read_sql("""
                    SELECT TOP 5
                        p.player_name AS Player,
                        SUM(s.runs) AS Runs,
                        SUM(s.balls_faced) AS Balls,
                        CAST(SUM(s.runs) * 100.0 / NULLIF(SUM(s.balls_faced), 0) AS DECIMAL(10,2)) AS StrikeRate
                    FROM player_match_stats s
                    JOIN players p ON s.player_id = p.player_id
                    GROUP BY p.player_name
                    HAVING SUM(s.balls_faced) >= 50
                    ORDER BY StrikeRate DESC
                """)
                if df.empty:
                    return "There is not enough batting data to calculate a qualified strike-rate leaderboard."
                rows = [f"**{i+1}. {r.Player}** — SR {r.StrikeRate} ({safe_int(r.Runs)} runs)" for i, r in enumerate(df.itertuples())]
                return "Best qualified strike rates in your stored data:\n\n" + "\n".join(rows)

            if "six" in q:
                df = read_sql("""
                    SELECT TOP 5 p.player_name AS Player, SUM(s.sixes) AS Sixes
                    FROM player_match_stats s
                    JOIN players p ON s.player_id = p.player_id
                    GROUP BY p.player_name
                    ORDER BY Sixes DESC
                """)
                if df.empty:
                    return "No six-hitting data is available yet."
                return "Most sixes in your stored data:\n\n" + "\n".join(
                    f"**{i+1}. {r.Player}** — {safe_int(r.Sixes)} sixes" for i, r in enumerate(df.itertuples())
                )

            if "four" in q or "boundary" in q:
                df = read_sql("""
                    SELECT TOP 5 p.player_name AS Player, SUM(s.fours) AS Fours
                    FROM player_match_stats s
                    JOIN players p ON s.player_id = p.player_id
                    GROUP BY p.player_name
                    ORDER BY Fours DESC
                """)
                if df.empty:
                    return "No boundary data is available yet."
                return "Most fours in your stored data:\n\n" + "\n".join(
                    f"**{i+1}. {r.Player}** — {safe_int(r.Fours)} fours" for i, r in enumerate(df.itertuples())
                )

            if "all round" in q or "allround" in q or "all-round" in q:
                df = read_sql("""
                    SELECT TOP 5 p.player_name AS Player,
                           SUM(s.runs) AS Runs,
                           SUM(s.wickets) AS Wickets
                    FROM player_match_stats s
                    JOIN players p ON s.player_id = p.player_id
                    GROUP BY p.player_name
                    HAVING SUM(s.runs) > 0 AND SUM(s.wickets) > 0
                    ORDER BY (SUM(s.runs) + SUM(s.wickets) * 25) DESC
                """)
                if df.empty:
                    return "No combined batting and bowling records are available yet."
                return "Top all-round impact from your stored data:\n\n" + "\n".join(
                    f"**{i+1}. {r.Player}** — {safe_int(r.Runs)} runs, {safe_int(r.Wickets)} wickets"
                    for i, r in enumerate(df.itertuples())
                )

            if "format" in q and ("distribution" in q or "most" in q or "matches" in q):
                df = read_sql("""
                    SELECT COALESCE(match_format, 'Unknown') AS Format, COUNT(*) AS Matches
                    FROM matches
                    GROUP BY match_format
                    ORDER BY Matches DESC
                """)
                if df.empty:
                    return "No match-format records are available yet."
                return "Match format distribution:\n\n" + "\n".join(
                    f"**{r.Format}** — {safe_int(r.Matches)} matches" for r in df.itertuples()
                )

            if "series" in q and ("most" in q or "top" in q or "active" in q):
                df = read_sql("""
                    SELECT TOP 5 s.series_name AS Series, COUNT(m.match_id) AS Matches
                    FROM series s
                    LEFT JOIN matches m ON s.series_id = m.series_id
                    GROUP BY s.series_name
                    ORDER BY Matches DESC
                """)
                if df.empty:
                    return "No series data is available yet."
                return "Most active series in your stored data:\n\n" + "\n".join(
                    f"**{i+1}. {r.Series}** — {safe_int(r.Matches)} matches" for i, r in enumerate(df.itertuples())
                )

            if "team" in q and "run" in q:
                df = read_sql("""
                    SELECT TOP 5 t.team_name AS Team, SUM(s.runs) AS Runs
                    FROM player_match_stats s
                    JOIN teams t ON s.team_id = t.team_id
                    GROUP BY t.team_name
                    ORDER BY Runs DESC
                """)
                if df.empty:
                    return "No team run data is available yet."
                return "Top teams by player runs in your stored data:\n\n" + "\n".join(
                    f"**{i+1}. {r.Team}** — {safe_int(r.Runs):,} runs" for i, r in enumerate(df.itertuples())
                )

        except Exception as error:
            return f"I could not read that metric from SQL Server right now: {error}"

        return None

    def get_ai_database_context():
        try:
            overview = read_sql("""
                SELECT
                    (SELECT COUNT(*) FROM matches) AS Matches,
                    (SELECT COUNT(*) FROM players) AS Players,
                    (SELECT COUNT(*) FROM teams) AS Teams,
                    (SELECT COUNT(*) FROM series) AS Series,
                    (SELECT COUNT(*) FROM venues) AS Venues
            """).iloc[0]
            return (
                f"Current app database summary: {safe_int(overview['Matches'])} matches, "
                f"{safe_int(overview['Players'])} players, {safe_int(overview['Teams'])} teams, "
                f"{safe_int(overview['Series'])} series, {safe_int(overview['Venues'])} venues."
            )
        except Exception:
            return "Database summary is currently unavailable."

    def ask_general_ai(question):
        """Use Ollama locally and Groq SDK on Streamlit Cloud."""
        system_prompt = (
            "You are Cricbuzz AI, a concise and helpful cricket intelligence assistant. "
            "Answer cricket questions accurately and clearly. You may also answer normal "
            "general-knowledge questions. Do not invent database statistics; database-specific "
            "questions are handled separately by the application."
        )

        if is_cloud_database():
            try:
                groq_key = st.secrets.get("GROQ_API_KEY", "")
            except Exception:
                groq_key = ""

            if not groq_key:
                return "Cloud AI is not configured yet. Add GROQ_API_KEY to Streamlit Secrets."

            try:
                client = Groq(api_key=groq_key)
                completion = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": str(question)},
                    ],
                    temperature=0.35,
                    max_tokens=700,
                )
                answer = completion.choices[0].message.content
                return (answer or "").strip() or "Cloud AI returned an empty response."

            except Exception as error:
                message = str(error)
                if "429" in message or "rate limit" in message.lower():
                    return "Groq free-tier rate limit reached temporarily. Please try again shortly."
                return f"Cloud AI is temporarily unavailable: {message}"

        try:
            response = requests.post(
                "http://localhost:11434/api/chat",
                json={
                    "model": os.getenv("OLLAMA_MODEL", "llama3.2:3b"),
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": str(question)},
                    ],
                    "stream": False,
                },
                timeout=120,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("message", {}).get("content", "").strip() or (
                "The local AI returned an empty response."
            )
        except requests.RequestException as error:
            return f"The local Ollama AI is unavailable. Make sure Ollama is running. ({error})"
        except (KeyError, TypeError, ValueError):
            return "The local AI returned an unexpected response. Please try again."


    def get_whisper_model():
        from faster_whisper import WhisperModel
        return WhisperModel(
            os.getenv("WHISPER_MODEL", "base"),
            device="cpu",
            compute_type="int8",
        )

    def get_recorded_audio_bytes(audio_value):
        """Return raw WAV bytes from streamlit-mic-recorder or an UploadedFile-like object."""
        if audio_value is None:
            return b""
        if isinstance(audio_value, (bytes, bytearray)):
            return bytes(audio_value)
        if isinstance(audio_value, dict):
            return bytes(audio_value.get("bytes") or b"")
        if hasattr(audio_value, "getvalue"):
            return audio_value.getvalue()
        return b""

    def transcribe_voice_question(audio_value):
        """Transcribe microphone audio locally with Faster-Whisper; no paid API required."""
        audio_bytes = get_recorded_audio_bytes(audio_value)
        if not audio_bytes:
            raise RuntimeError("No microphone audio was captured. Please record again.")

        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                temp_file.write(audio_bytes)
                temp_path = temp_file.name

            model = get_whisper_model()
            segments, _ = model.transcribe(
                temp_path,
                beam_size=5,
                vad_filter=True,
            )
            return " ".join(segment.text.strip() for segment in segments).strip()
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

    def plain_text_for_voice(markdown_text):
        clean = re.sub(r"```.*?```", " ", str(markdown_text), flags=re.S)
        clean = re.sub(r"[`*_#>-]", " ", clean)
        clean = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", clean)
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean[:1800]

    def speak_ai_text(text_to_speak):
        """Automatic browser TTS with one consistent soft female English voice."""
        safe_js_text = (
            plain_text_for_voice(text_to_speak)
            .replace("\\", "\\\\")
            .replace("`", "\\`")
            .replace("${", "\\${")
        )
        components.html(
            f"""
            <script>
            (() => {{
                const text = `{safe_js_text}`;
                if (!text || !('speechSynthesis' in window)) return;

                const synth = window.speechSynthesis;
                let spoken = false;

                const speakOnce = () => {{
                    if (spoken) return;
                    const voices = synth.getVoices();
                    if (!voices.length) return;

                    spoken = true;
                    synth.onvoiceschanged = null;
                    synth.cancel();

                    const utter = new SpeechSynthesisUtterance(text);
                    utter.rate = 0.97;
                    utter.pitch = 1.14;
                    utter.volume = 1.0;

                    const preferredNames = [
                        'Microsoft Neerja', 'Microsoft Heera', 'Microsoft Aria',
                        'Microsoft Jenny', 'Zira', 'Ava', 'Samantha', 'Sonia',
                        'Hazel', 'Google UK English Female', 'Female'
                    ];

                    let voice = voices.find(v =>
                        preferredNames.some(name =>
                            v.name.toLowerCase().includes(name.toLowerCase())
                        ) && (v.lang || '').toLowerCase() === 'en-in'
                    );

                    if (!voice) {{
                        voice = voices.find(v =>
                            preferredNames.some(name =>
                                v.name.toLowerCase().includes(name.toLowerCase())
                            ) && (v.lang || '').toLowerCase().startsWith('en')
                        );
                    }}

                    if (!voice) {{
                        voice = voices.find(v =>
                            (v.lang || '').toLowerCase() === 'en-in' &&
                            !/ravi|david|mark|guy|daniel|aaron|male/i.test(v.name)
                        );
                    }}

                    if (!voice) {{
                        voice = voices.find(v =>
                            (v.lang || '').toLowerCase().startsWith('en') &&
                            !/ravi|david|mark|guy|daniel|aaron|male/i.test(v.name)
                        );
                    }}

                    if (voice) utter.voice = voice;
                    synth.speak(utter);
                }};

                if (synth.getVoices().length) {{
                    speakOnce();
                }} else {{
                    synth.onvoiceschanged = speakOnce;
                    setTimeout(speakOnce, 700);
                }}
            }})();
            </script>
            """,
            height=0,
        )

    def generate_ai_answer(question):
        if is_shivani_mam_question(question):
            return "Shivani Ma'am is our mentor at Labmentix for the internship. She is the best mentor ever. She explains everything so calmly and solves every doubt perfectly. Learning from her is the best feeling.", True

        db_answer = ai_db_answer(question)
        if db_answer:
            return db_answer, False

        return ask_general_ai(question), False

    def process_ai_question(question):
        question = str(question).strip()
        if not question:
            return

        remember_ai_question(question)
        if "ai_messages" not in st.session_state:
            st.session_state.ai_messages = []

        next_id = int(st.session_state.get("ai_message_seq", 0)) + 1
        st.session_state.ai_message_seq = next_id
        st.session_state.ai_messages.append({
            "id": next_id,
            "role": "user",
            "content": question,
            "special": False,
        })

        answer, special = generate_ai_answer(question)
        next_id += 1
        st.session_state.ai_message_seq = next_id
        st.session_state.ai_messages.append({
            "id": next_id,
            "role": "assistant",
            "content": answer,
            "special": special,
        })
        st.session_state.ai_last_answer_id = next_id

    with st.sidebar:
        st.markdown(
            """
            <div style="padding:7px 2px 12px 2px;">
                <div style="
                    font-family:'Space Grotesk',sans-serif;
                    font-size:19px;
                    font-weight:700;
                    color:#f2eef8;
                    letter-spacing:-.5px;">
                    CRICBUZZ <span style="color:#a65fff;">LIVESTATS</span>
                </div>
                <div style="
                    font-size:8px;
                    letter-spacing:2.6px;
                    color:#505766;
                    margin-top:5px;">
                    CRICKET INTELLIGENCE
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div style="
                color:#7d8393;
                font-size:9px;
                font-weight:700;
                letter-spacing:2.2px;
                margin:2px 0 7px 0;">
                NAVIGATION
            </div>
            """,
            unsafe_allow_html=True,
        )

        nav_pages = [
            "Dashboard",
            "Live Matches",
            "Player Analytics",
            "World Cricket Map",
            "AI Assistant",
            "SQL Analytics",
            "CRUD",
        ]

        current_nav_index = (
            nav_pages.index(st.session_state.current_page)
            if st.session_state.current_page in nav_pages
            else 0
        )

        selected_nav_page = st.selectbox(
            "Go to page",
            nav_pages,
            index=current_nav_index,
            key="compact_right_navigation",
            label_visibility="collapsed",
        )

        if selected_nav_page != st.session_state.current_page:
            go_to(selected_nav_page)

        if st.button(
            "← Landing Page",
            key="compact_landing_nav",
            use_container_width=True,
        ):
            go_to("Landing")

        st.caption("SQL SERVER • CRICKBUZZ API")


    if st.session_state.current_page == "Dashboard":
        page_heading("CRICKET INTELLIGENCE DASHBOARD", "Analytics built for", "every ball.", "Team performance, match activity, formats, series and player records from your SQL Server database.")
        try:
            overview = read_sql("""SELECT (SELECT COUNT(*) FROM matches) AS Matches,(SELECT COUNT(*) FROM players) AS Players,(SELECT COUNT(*) FROM teams) AS Teams,(SELECT COUNT(*) FROM player_match_stats) AS PlayerStats""").iloc[0]
            c1,c2,c3,c4 = st.columns(4)
            c1.metric("Matches", f"{safe_int(overview['Matches']):,}")
            c2.metric("Players", f"{safe_int(overview['Players']):,}")
            c3.metric("Teams", f"{safe_int(overview['Teams']):,}")
            c4.metric("Player Stats", f"{safe_int(overview['PlayerStats']):,}")

            runs_team = read_sql("""SELECT TOP 10 t.team_name AS Team,SUM(s.runs) AS Runs FROM player_match_stats s JOIN teams t ON s.team_id=t.team_id GROUP BY t.team_name HAVING SUM(s.runs)>0 ORDER BY Runs DESC""")
            wickets_team = read_sql("""SELECT TOP 10 t.team_name AS Team,SUM(s.wickets) AS Wickets FROM player_match_stats s JOIN teams t ON s.team_id=t.team_id GROUP BY t.team_name HAVING SUM(s.wickets)>0 ORDER BY Wickets DESC""")
            section_title("Team Performance", "Actual batting and bowling output aggregated from player match statistics.")
            left,right = st.columns(2)
            with left:
                if not runs_team.empty:
                    d = runs_team.sort_values("Runs")
                    fig = px.bar(d, x="Runs", y="Team", orientation="h", title="Top Teams by Runs", color="Runs", color_continuous_scale=["#45207f","#8850ed","#c084fc"])
                    fig.update_traces(hovertemplate="<b>%{y}</b><br>Runs: %{x:,}<extra></extra>")
                    fig.update_layout(coloraxis_showscale=False)
                    st.plotly_chart(style_plot(fig,410,False), use_container_width=True, config={"displayModeBar":False})
            with right:
                if not wickets_team.empty:
                    d = wickets_team.sort_values("Wickets")
                    fig = px.bar(d, x="Wickets", y="Team", orientation="h", title="Top Teams by Wickets", color="Wickets", color_continuous_scale=["#2a2458","#7957d8","#54d6ff"])
                    fig.update_traces(hovertemplate="<b>%{y}</b><br>Wickets: %{x:,}<extra></extra>")
                    fig.update_layout(coloraxis_showscale=False)
                    st.plotly_chart(style_plot(fig,410,False), use_container_width=True, config={"displayModeBar":False})

            formats = read_sql("""SELECT COALESCE(match_format,'Unknown') AS Format,COUNT(*) AS Matches FROM matches GROUP BY match_format ORDER BY Matches DESC""")
            series_df = read_sql("""SELECT TOP 8 s.series_name AS Series,COUNT(m.match_id) AS Matches FROM series s LEFT JOIN matches m ON s.series_id=m.series_id GROUP BY s.series_name HAVING COUNT(m.match_id)>0 ORDER BY Matches DESC""")
            section_title("Competition Mix", "Stored matches split by format and most active series.")
            left,right = st.columns([.9,1.1])
            with left:
                if not formats.empty:
                    fig = go.Figure(data=[go.Pie(labels=formats["Format"], values=formats["Matches"], hole=.67, marker=dict(colors=[PURPLE,CYAN,PINK,"#6d5dfc","#d286ff","#41a7ff"]), textinfo="percent", textfont=dict(color="#d6d9e1",size=10), hovertemplate="<b>%{label}</b><br>%{value} matches<br>%{percent}<extra></extra>")])
                    fig.update_layout(title="Match Format Distribution", annotations=[dict(text="FORMAT",x=.5,y=.5,showarrow=False,font=dict(color="#9a76cf",size=11))])
                    st.plotly_chart(style_plot(fig,395,True), use_container_width=True, config={"displayModeBar":False})
            with right:
                if not series_df.empty:
                    fig = px.bar(series_df, x="Series", y="Matches", title="Most Active Series")
                    fig.update_traces(marker=dict(color=series_df["Matches"], colorscale=[[0,"#47247c"],[.5,"#8f4ded"],[1,"#c084fc"]]), hovertemplate="<b>%{x}</b><br>Matches: %{y}<extra></extra>")
                    fig.update_xaxes(tickangle=-25)
                    st.plotly_chart(style_plot(fig,395,False), use_container_width=True, config={"displayModeBar":False})

            timeline = read_sql("""SELECT CAST(match_date AS DATE) AS MatchDate,COUNT(*) AS Matches FROM matches WHERE match_date IS NOT NULL GROUP BY CAST(match_date AS DATE) ORDER BY MatchDate""")
            section_title("Match Activity Timeline", "Daily match volume — a real trend rather than match IDs on a line.")
            if not timeline.empty:
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=timeline["MatchDate"],y=timeline["Matches"],mode="lines+markers",line=dict(color=PURPLE,width=3),marker=dict(size=7,color=CYAN,line=dict(color="#10131d",width=2)),fill="tozeroy",fillcolor="rgba(155,92,255,.10)",hovertemplate="<b>%{x|%d %b %Y}</b><br>Matches: %{y}<extra></extra>"))
                st.plotly_chart(style_plot(fig,360,False), use_container_width=True, config={"displayModeBar":False})

            recent = read_sql("""SELECT TOP 12 m.match_id AS [Match ID],t1.team_name AS [Team 1],t2.team_name AS [Team 2],m.match_format AS Format,m.status AS Status,m.match_date AS [Match Date] FROM matches m LEFT JOIN teams t1 ON m.team1_id=t1.team_id LEFT JOIN teams t2 ON m.team2_id=t2.team_id ORDER BY m.match_date DESC""")
            section_title("Recent Match Records", "Theme-matched SQL data table.")
            dark_table(recent,20)
        except Exception as error:
            st.error(f"Dashboard data could not be loaded: {error}")

    elif st.session_state.current_page == "Live Matches":
        page_heading("REAL-TIME CRICKET", "Live", "Match Center.", "Live, upcoming and recent fixtures from the Crickbuzz API presented as premium cards instead of white tables.")
        client = CrickbuzzClient()

        def parse_match_cards(data):
            records=[]
            for type_match in data.get("typeMatches",[]):
                match_type=type_match.get("matchType","")
                for series_item in type_match.get("seriesMatches",[]):
                    wrapper=series_item.get("seriesAdWrapper")
                    if not wrapper:
                        continue
                    series_name=wrapper.get("seriesName","")
                    for match in wrapper.get("matches",[]):
                        info=match.get("matchInfo",{}) or {}
                        score=match.get("matchScore",{}) or {}
                        t1=info.get("team1",{}) or {}; t2=info.get("team2",{}) or {}; venue=info.get("venueInfo",{}) or {}
                        def innings_score(team_key):
                            team_score=score.get(team_key,{}) or {}
                            innings=team_score.get("inngs1") or team_score.get("inngs2") or {}
                            if not innings: return ""
                            runs=innings.get("runs"); wkts=innings.get("wickets")
                            if runs is None: return ""
                            return f"{runs}/{wkts}" if wkts is not None else str(runs)
                        records.append({"Match ID":info.get("matchId"),"Series":series_name,"Team 1":t1.get("teamName") or "Team 1","Team 2":t2.get("teamName") or "Team 2","Team 1 Score":innings_score("team1Score"),"Team 2 Score":innings_score("team2Score"),"Format":info.get("matchFormat") or match_type,"Status":info.get("status") or "Status unavailable","Venue":venue.get("ground") or "","City":venue.get("city") or ""})
            return records

        def render_match_cards(records):
            if not records:
                st.info("No matches available in this category right now.")
                return
            cols=st.columns(2)
            for idx,match in enumerate(records[:30]):
                with cols[idx%2]:
                    score1=f" • {escape(match['Team 1 Score'])}" if match.get("Team 1 Score") else ""
                    score2=f" • {escape(match['Team 2 Score'])}" if match.get("Team 2 Score") else ""
                    place=" · ".join([x for x in [match.get("Venue"),match.get("City")] if x])
                    match_id=escape(str(match.get("Match ID") or "-"))
                    st.markdown(f'''<div class="match-card"><div class="match-top"><span class="match-badge">{escape(str(match.get("Format") or "MATCH"))}</span><span class="match-series">{escape(str(match.get("Series") or ""))}</span></div><div class="match-teams">{escape(str(match["Team 1"]))}<span style="color:#b987ff;font-size:13px;">{score1}</span><br><span class="match-vs">VS</span><br>{escape(str(match["Team 2"]))}<span style="color:#78d8ff;font-size:13px;">{score2}</span></div><div class="match-status">{escape(str(match.get("Status") or ""))}</div><div class="match-meta">{escape(place)} &nbsp;•&nbsp; Match ID {match_id}</div></div>''', unsafe_allow_html=True)

        if st.button("Refresh Data"):
            fetch_match_data.clear()
            st.rerun()
        live_tab,upcoming_tab,recent_tab=st.tabs(["Live","Upcoming","Recent"])
        for tab,label,category in [(live_tab,"Live","live"),(upcoming_tab,"Upcoming","upcoming"),(recent_tab,"Recent","recent")]:
            with tab:
                try:
                    records=parse_match_cards(fetch_match_data(category))
                    st.metric(f"{label} Matches",len(records))
                    if records:
                        fmt=pd.DataFrame(records)["Format"].fillna("Unknown").value_counts().reset_index(); fmt.columns=["Format","Matches"]
                        fig=px.bar(fmt,x="Format",y="Matches",title=f"{label} Match Format Mix")
                        fig.update_traces(marker_color=PURPLE,hovertemplate="<b>%{x}</b><br>%{y} matches<extra></extra>")
                        st.plotly_chart(style_plot(fig,240,False),use_container_width=True,config={"displayModeBar":False})
                    render_match_cards(records)
                except Exception as error:
                    st.error(f"Unable to load {label.lower()} matches: {error}")

    elif st.session_state.current_page == "Player Analytics":
        page_heading("PERFORMANCE INTELLIGENCE", "Player", "Analytics.", "Batting, bowling, boundary and all-round performance from your stored player match statistics.")
        try:
            totals=read_sql("""SELECT COALESCE(SUM(runs),0) AS Runs,COALESCE(SUM(wickets),0) AS Wickets,COALESCE(SUM(fours),0) AS Fours,COALESCE(SUM(sixes),0) AS Sixes FROM player_match_stats""").iloc[0]
            c1,c2,c3,c4=st.columns(4)
            c1.metric("Total Runs",f"{safe_int(totals['Runs']):,}"); c2.metric("Total Wickets",f"{safe_int(totals['Wickets']):,}"); c3.metric("Fours",f"{safe_int(totals['Fours']):,}"); c4.metric("Sixes",f"{safe_int(totals['Sixes']):,}")
            runs=read_sql("""SELECT TOP 12 p.player_name AS Player,SUM(s.runs) AS Runs FROM player_match_stats s JOIN players p ON s.player_id=p.player_id GROUP BY p.player_name ORDER BY Runs DESC""")
            wickets=read_sql("""SELECT TOP 12 p.player_name AS Player,SUM(s.wickets) AS Wickets FROM player_match_stats s JOIN players p ON s.player_id=p.player_id GROUP BY p.player_name ORDER BY Wickets DESC""")
            left,right=st.columns(2)
            with left:
                d=runs.sort_values("Runs"); fig=px.bar(d,x="Runs",y="Player",orientation="h",title="Top Run Scorers"); fig.update_traces(marker=dict(color=d["Runs"],colorscale=[[0,"#4b287e"],[1,"#c084fc"]])); st.plotly_chart(style_plot(fig,440,False),use_container_width=True,config={"displayModeBar":False})
            with right:
                d=wickets.sort_values("Wickets"); fig=px.bar(d,x="Wickets",y="Player",orientation="h",title="Top Wicket Takers"); fig.update_traces(marker=dict(color=d["Wickets"],colorscale=[[0,"#27345f"],[1,"#54d6ff"]])); st.plotly_chart(style_plot(fig,440,False),use_container_width=True,config={"displayModeBar":False})
            strike=read_sql("""SELECT TOP 40 p.player_name AS Player,SUM(s.runs) AS Runs,SUM(s.balls_faced) AS Balls,CAST(SUM(s.runs)*100.0/NULLIF(SUM(s.balls_faced),0) AS DECIMAL(10,2)) AS StrikeRate,SUM(s.sixes) AS Sixes FROM player_match_stats s JOIN players p ON s.player_id=p.player_id GROUP BY p.player_name HAVING SUM(s.balls_faced)>=25 ORDER BY Runs DESC""")
            boundaries=read_sql("""SELECT TOP 12 p.player_name AS Player,SUM(s.fours) AS Fours,SUM(s.sixes) AS Sixes FROM player_match_stats s JOIN players p ON s.player_id=p.player_id GROUP BY p.player_name ORDER BY SUM(s.fours)+SUM(s.sixes) DESC""")
            section_title("Batting Quality", "Strike-rate relationship and boundary impact.")
            left,right=st.columns([1.1,.9])
            with left:
                if not strike.empty:
                    fig=px.scatter(strike,x="StrikeRate",y="Runs",size="Sixes",hover_name="Player",title="Runs vs Strike Rate",size_max=28); fig.update_traces(marker=dict(color=PURPLE,opacity=.78,line=dict(color=CYAN,width=.6))); st.plotly_chart(style_plot(fig,400,False),use_container_width=True,config={"displayModeBar":False})
            with right:
                fig=go.Figure(); fig.add_bar(x=boundaries["Player"],y=boundaries["Fours"],name="Fours",marker_color=PURPLE); fig.add_bar(x=boundaries["Player"],y=boundaries["Sixes"],name="Sixes",marker_color=CYAN); fig.update_layout(barmode="group",title="Boundary Leaders"); fig.update_xaxes(tickangle=-35); st.plotly_chart(style_plot(fig,400,True),use_container_width=True,config={"displayModeBar":False})
            allround=read_sql("""SELECT TOP 30 p.player_name AS Player,SUM(s.runs) AS Runs,SUM(s.wickets) AS Wickets,COUNT(DISTINCT s.match_id) AS Matches FROM player_match_stats s JOIN players p ON s.player_id=p.player_id GROUP BY p.player_name HAVING SUM(s.runs)>0 AND SUM(s.wickets)>0 ORDER BY Runs DESC,Wickets DESC""")
            section_title("All-Round Impact", "Players contributing with both bat and ball.")
            if not allround.empty:
                fig=px.scatter(allround,x="Runs",y="Wickets",size="Matches",hover_name="Player",title="Runs vs Wickets • Bubble size = matches",size_max=34); fig.update_traces(marker=dict(color=PINK,opacity=.70,line=dict(color=PURPLE_2,width=.8))); st.plotly_chart(style_plot(fig,430,False),use_container_width=True,config={"displayModeBar":False}); dark_table(allround.head(15))
        except Exception as error:
            st.error(f"Player analytics could not be loaded: {error}")


    elif st.session_state.current_page == "World Cricket Map":
        page_heading(
            "GLOBAL CRICKET INTELLIGENCE",
            "World Cricket",
            "Map.",
            "Explore the countries represented in your cricket database. Hover over a country to see player coverage and use the supporting charts to compare national representation."
        )

        try:
            player_countries = read_sql("""
                SELECT
                    LTRIM(RTRIM(country)) AS Country,
                    COUNT(*) AS Players
                FROM players
                WHERE country IS NOT NULL
                  AND LTRIM(RTRIM(country)) <> ''
                GROUP BY LTRIM(RTRIM(country))
                ORDER BY Players DESC
            """)

            team_countries = read_sql("""
                SELECT
                    LTRIM(RTRIM(country)) AS Country,
                    COUNT(*) AS Teams
                FROM teams
                WHERE country IS NOT NULL
                  AND LTRIM(RTRIM(country)) <> ''
                GROUP BY LTRIM(RTRIM(country))
                ORDER BY Teams DESC
            """)

            total_player_countries = len(player_countries)
            total_team_countries = len(team_countries)
            players_with_country = safe_int(player_countries["Players"].sum()) if not player_countries.empty else 0
            teams_with_country = safe_int(team_countries["Teams"].sum()) if not team_countries.empty else 0

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Player Countries", f"{total_player_countries:,}")
            c2.metric("Players Mapped", f"{players_with_country:,}")
            c3.metric("Team Countries", f"{total_team_countries:,}")
            c4.metric("Teams Mapped", f"{teams_with_country:,}")

            st.write("")
            section_title(
                "Global Player Coverage",
                "Country-wise player representation using the country values currently stored in the players table."
            )

            if player_countries.empty:
                st.info(
                    "No player-country data is stored yet. The map will populate after player profiles are enriched with country information."
                )
            else:
                world_fig = go.Figure(
                    data=go.Choropleth(
                        locations=player_countries["Country"],
                        z=player_countries["Players"],
                        locationmode="country names",
                        text=player_countries["Country"],
                        colorscale=[
                            [0.00, "#211333"],
                            [0.20, "#4a237d"],
                            [0.45, "#7138c7"],
                            [0.70, "#9b5cf5"],
                            [1.00, "#69dcff"],
                        ],
                        marker_line_color="rgba(198,160,255,.32)",
                        marker_line_width=0.55,
                        colorbar=dict(
                            title=dict(text="Players", font=dict(color="#aeb4c3", size=11)),
                            tickfont=dict(color="#8e95a5", size=10),
                            thickness=10,
                            len=0.62,
                            outlinewidth=0,
                            bgcolor="rgba(0,0,0,0)",
                        ),
                        hovertemplate="<b>%{text}</b><br>Players: %{z:,}<extra></extra>",
                    )
                )

                world_fig.update_geos(
                    projection_type="natural earth",
                    showframe=False,
                    showcoastlines=True,
                    coastlinecolor="rgba(150,158,178,.28)",
                    coastlinewidth=0.6,
                    showcountries=True,
                    countrycolor="rgba(174,134,236,.18)",
                    countrywidth=0.45,
                    showland=True,
                    landcolor="#11131d",
                    showocean=True,
                    oceancolor="#070910",
                    showlakes=True,
                    lakecolor="#070910",
                    bgcolor="rgba(0,0,0,0)",
                )

                world_fig.update_layout(
                    height=560,
                    margin=dict(l=0, r=0, t=20, b=0),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Inter", color="#d8dae2"),
                    geo=dict(bgcolor="rgba(0,0,0,0)"),
                )

                st.plotly_chart(
                    world_fig,
                    use_container_width=True,
                    config={"displayModeBar": False},
                )

                st.caption(
                    "Only countries already stored in your database are highlighted. Unmapped/blank player-country records are intentionally excluded."
                )

                left, right = st.columns([1.05, 0.95])

                with left:
                    section_title(
                        "Top Countries by Players",
                        "Highest player representation in the current SQL dataset."
                    )
                    top_players = player_countries.head(12).sort_values("Players")
                    player_fig = px.bar(
                        top_players,
                        x="Players",
                        y="Country",
                        orientation="h",
                        title="Player Representation",
                    )
                    player_fig.update_traces(
                        marker=dict(
                            color=top_players["Players"],
                            colorscale=[
                                [0, "#3d216d"],
                                [0.55, "#8950e9"],
                                [1, "#65d9ff"],
                            ],
                            line=dict(color="rgba(213,181,255,.25)", width=0.5),
                        ),
                        hovertemplate="<b>%{y}</b><br>Players: %{x:,}<extra></extra>",
                    )
                    st.plotly_chart(
                        style_plot(player_fig, 420, False),
                        use_container_width=True,
                        config={"displayModeBar": False},
                    )

                with right:
                    section_title(
                        "Team Representation",
                        "Countries recorded against teams in the teams table."
                    )
                    if team_countries.empty:
                        st.info("No team-country data is stored yet.")
                    else:
                        top_teams = team_countries.head(12).sort_values("Teams")
                        team_fig = px.bar(
                            top_teams,
                            x="Teams",
                            y="Country",
                            orientation="h",
                            title="Teams by Country",
                        )
                        team_fig.update_traces(
                            marker=dict(
                                color=top_teams["Teams"],
                                colorscale=[
                                    [0, "#252b59"],
                                    [0.55, "#6352c9"],
                                    [1, "#c17cff"],
                                ],
                                line=dict(color="rgba(213,181,255,.22)", width=0.5),
                            ),
                            hovertemplate="<b>%{y}</b><br>Teams: %{x:,}<extra></extra>",
                        )
                        st.plotly_chart(
                            style_plot(team_fig, 420, False),
                            use_container_width=True,
                            config={"displayModeBar": False},
                        )

                combined = player_countries.merge(
                    team_countries,
                    on="Country",
                    how="outer",
                ).fillna(0)

                combined["Players"] = combined["Players"].astype(int)
                combined["Teams"] = combined["Teams"].astype(int)
                combined = combined.sort_values(
                    ["Players", "Teams"],
                    ascending=False,
                )

                section_title(
                    "Country Directory",
                    "Theme-matched summary of player and team representation."
                )
                dark_table(combined, 100)

        except Exception as error:
            st.error(f"World map data could not be loaded: {error}")


    elif st.session_state.current_page == "AI Assistant":
        page_heading(
            "CONVERSATIONAL CRICKET INTELLIGENCE",
            "Meet",
            "Cricbuzz AI.",
            "Ask by text or voice. Database questions use your SQL Server records; general questions use the AI model. Every answer is shown as text and spoken automatically.",
        )

        st.markdown(
            """
            <style>
            .ai-shell{position:relative;padding:18px 0 5px;}
            .ai-status{display:inline-flex;align-items:center;gap:8px;padding:7px 11px;border-radius:999px;border:1px solid rgba(176,105,255,.22);background:rgba(146,69,237,.08);color:#b991f3;font-size:10px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;margin-bottom:18px;}
            .ai-dot{width:7px;height:7px;border-radius:50%;background:#b66cff;box-shadow:0 0 14px #a252ff;animation:aiPulse 1.7s ease-in-out infinite;}
            @keyframes aiPulse{0%,100%{opacity:.55;transform:scale(.9)}50%{opacity:1;transform:scale(1.2)}}
            .ai-panel{padding:22px;border:1px solid rgba(161,92,255,.15);border-radius:20px;background:linear-gradient(145deg,rgba(14,16,26,.98),rgba(8,9,15,.99));box-shadow:0 18px 55px rgba(0,0,0,.22);}
            .ai-panel-title{font-family:'Space Grotesk',sans-serif;font-size:18px;font-weight:600;color:#f0edf7;margin-bottom:4px;}
            .ai-panel-sub{font-size:11px;color:#6f7685;line-height:1.6;margin-bottom:18px;}
            .ai-msg{padding:15px 17px;border-radius:16px;margin:10px 0;line-height:1.7;font-size:13px;}
            .ai-user{margin-left:10%;background:linear-gradient(135deg,rgba(116,53,198,.22),rgba(57,31,94,.18));border:1px solid rgba(179,106,255,.20);color:#e8e3f2;}
            .ai-bot{margin-right:6%;background:linear-gradient(145deg,rgba(18,20,31,.96),rgba(11,12,19,.98));border:1px solid rgba(112,201,255,.12);color:#c8ccd6;}
            .ai-label{font-size:8px;letter-spacing:2.2px;text-transform:uppercase;font-weight:800;margin-bottom:6px;color:#8d5fd1;}
            .ai-bot .ai-label{color:#65c9f1;}
            .goat-card{margin:12px 0;padding:28px 22px;text-align:center;border-radius:20px;border:1px solid rgba(194,126,255,.35);background:radial-gradient(circle at 50% 15%,rgba(159,75,255,.17),transparent 56%),linear-gradient(145deg,#11101b,#08090f);box-shadow:0 0 34px rgba(145,57,234,.15),inset 0 0 24px rgba(152,78,235,.04);}
            .goat-main{font-family:'Space Grotesk',sans-serif;font-size:clamp(38px,5vw,62px);font-weight:700;letter-spacing:8px;color:#d3a7ff;text-shadow:0 0 18px rgba(181,105,255,.42),0 0 44px rgba(129,53,219,.25);}
            .goat-sub{margin-top:7px;font-family:'Space Grotesk',sans-serif;font-size:12px;font-weight:600;letter-spacing:4px;text-transform:uppercase;color:#8f75ae;}
            .topq-number{font-family:'Space Grotesk',sans-serif;color:#7f46c3;font-size:10px;font-weight:700;letter-spacing:1px;margin-top:8px;}
            .voice-orb{width:54px;height:54px;border-radius:50%;display:flex;align-items:center;justify-content:center;margin:4px auto 10px;background:radial-gradient(circle,#b062ff 0%,#7433c5 42%,#211132 72%);box-shadow:0 0 22px rgba(173,84,255,.48),0 0 55px rgba(111,44,194,.22);font-size:22px;animation:voiceGlow 2.2s ease-in-out infinite;}
            @keyframes voiceGlow{0%,100%{transform:scale(1);box-shadow:0 0 18px rgba(173,84,255,.34),0 0 42px rgba(111,44,194,.18)}50%{transform:scale(1.05);box-shadow:0 0 30px rgba(190,110,255,.58),0 0 70px rgba(111,44,194,.28)}}
            </style>
            <div class="ai-shell"><div class="ai-status"><span class="ai-dot"></span> AI Assistant Online</div></div>
            """,
            unsafe_allow_html=True,
        )

        if "ai_messages" not in st.session_state:
            st.session_state.ai_messages = []
        if "ai_message_seq" not in st.session_state:
            st.session_state.ai_message_seq = 0
        if "ai_last_spoken_id" not in st.session_state:
            st.session_state.ai_last_spoken_id = None
        if "ai_pending_question" not in st.session_state:
            st.session_state.ai_pending_question = None
        if "ai_last_audio_hash" not in st.session_state:
            st.session_state.ai_last_audio_hash = None

        left, right = st.columns([1.9, 0.85], gap="large")

        with left:
            st.markdown(
                '<div class="ai-panel-title">Conversation</div><div class="ai-panel-sub">SQL-aware cricket analytics + general intelligence. Voice replies play automatically.</div>',
                unsafe_allow_html=True,
            )

            if not st.session_state.ai_messages:
                st.markdown(
                    """
                    <div class="ai-panel">
                        <div style="text-align:center;padding:34px 12px 26px;">
                            <div class="voice-orb">🎙️</div>
                            <div style="font-family:'Space Grotesk',sans-serif;font-size:22px;color:#eee9f7;font-weight:600;">Ask Cricbuzz AI</div>
                            <div style="max-width:520px;margin:10px auto 0;color:#737a89;font-size:12px;line-height:1.7;">Ask about your cricket database, cricket concepts, comparisons, or a normal general question.</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown('<div class="ai-panel">', unsafe_allow_html=True)
                for msg in st.session_state.ai_messages:
                    if msg["role"] == "user":
                        st.markdown(
                            f'<div class="ai-msg ai-user"><div class="ai-label">YOU</div>{escape(str(msg["content"]))}</div>',
                            unsafe_allow_html=True,
                        )
                    elif msg.get("special"):
                        st.markdown(
                            """
                            <div class="ai-msg ai-bot"><div class="ai-label">CRICBUZZ AI</div></div>
                            <div class="goat-card">
                                <div class="goat-main" style="font-size:clamp(24px,3vw,38px);letter-spacing:1px;">BEST MENTOR EVER</div>
                                <div class="goat-sub" style="max-width:760px;margin:14px auto 0;letter-spacing:.4px;line-height:1.8;text-transform:none;font-size:13px;">Shivani Ma'am is our mentor at Labmentix for the internship. She is the best mentor ever. She explains everything so calmly and solves every doubt perfectly. Learning from her is the best feeling.</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown('<div class="ai-msg ai-bot"><div class="ai-label">CRICBUZZ AI</div>', unsafe_allow_html=True)
                        st.markdown(msg["content"])
                        st.markdown('</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            latest_assistant = next(
                (m for m in reversed(st.session_state.ai_messages) if m.get("role") == "assistant"),
                None,
            )
            if latest_assistant and latest_assistant.get("id") != st.session_state.ai_last_spoken_id:
                speak_ai_text(latest_assistant.get("content", ""))
                st.session_state.ai_last_spoken_id = latest_assistant.get("id")

            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

            st.markdown(
                '<div style="color:#8d94a3;font-size:11px;margin:2px 0 8px;">🎙️ Voice question — press Start, speak, then press Stop.</div>',
                unsafe_allow_html=True,
            )

            if mic_recorder is None:
                st.error("Voice recorder package is missing. Run: pip install streamlit-mic-recorder")
            else:
                audio_value = mic_recorder(
                    start_prompt="🎙️ Start Recording",
                    stop_prompt="⏹️ Stop Recording",
                    just_once=True,
                    use_container_width=True,
                    key="cricbuzz_voice_recorder",
                )

                audio_bytes = get_recorded_audio_bytes(audio_value)
                if audio_bytes:
                    audio_hash = hashlib.md5(audio_bytes).hexdigest()
                    if audio_hash != st.session_state.ai_last_audio_hash:
                        st.session_state.ai_last_audio_hash = audio_hash
                        with st.spinner("Transcribing your voice locally..."):
                            try:
                                transcript = transcribe_voice_question(audio_bytes)
                                if transcript:
                                    st.caption(f"Heard: {transcript}")
                                    st.session_state.ai_pending_question = transcript
                                    st.rerun()
                                else:
                                    st.warning("I could not detect a clear question. Please record again.")
                            except Exception as error:
                                st.error(f"Voice input unavailable: {error}")

            with st.form("ai_text_form", clear_on_submit=True):
                text_question = st.text_input(
                    "Ask a question",
                    placeholder="Ask about cricket, your SQL data, or anything else...",
                    label_visibility="collapsed",
                )
                submitted = st.form_submit_button("Ask Cricbuzz AI", use_container_width=True)
                if submitted and text_question.strip():
                    st.session_state.ai_pending_question = text_question.strip()
                    st.rerun()

            if st.session_state.ai_messages:
                if st.button("Clear Conversation", key="clear_ai_chat", use_container_width=True):
                    st.session_state.ai_messages = []
                    st.session_state.ai_last_spoken_id = None
                    st.session_state.ai_last_audio_hash = None
                    st.rerun()

        with right:
            st.markdown(
                '<div class="ai-panel-title">Top 7 Questions</div><div class="ai-panel-sub">Most-used questions rise automatically during the session.</div>',
                unsafe_allow_html=True,
            )
            for index, question in enumerate(get_top_ai_questions(), start=1):
                st.markdown(f'<div class="topq-number">0{index}</div>', unsafe_allow_html=True)
                if st.button(question, key=f"ai_top_q_{index}_{normalize_ai_question(question)}", use_container_width=True):
                    st.session_state.ai_pending_question = question
                    st.rerun()

            st.markdown("---")
            st.markdown(
                """
                <div style="padding:14px 4px 2px;">
                    <div style="font-family:'Space Grotesk',sans-serif;color:#d7c5eb;font-size:12px;font-weight:600;">VOICE PROFILE</div>
                    <div style="margin-top:8px;color:#777e8d;font-size:11px;line-height:1.7;">Soft • Clear • Friendly<br>Female assistant voice</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if st.session_state.ai_pending_question:
            pending = st.session_state.ai_pending_question
            st.session_state.ai_pending_question = None
            with st.spinner("Cricbuzz AI is thinking..."):
                process_ai_question(pending)
            st.rerun()

    elif st.session_state.current_page == "SQL Analytics":
        page_heading("SQL INTELLIGENCE", "25 analytical", "queries.", "Choose a cricket question, inspect the SQL, run it against SQL Server and view a premium dark result table with an automatic chart where appropriate.")
        QUERIES={
            "1. Total Teams":"SELECT COUNT(*) AS TotalTeams FROM teams;",
            "2. Total Players":"SELECT COUNT(*) AS TotalPlayers FROM players;",
            "3. Total Matches":"SELECT COUNT(*) AS TotalMatches FROM matches;",
            "4. Total Series":"SELECT COUNT(*) AS TotalSeries FROM series;",
            "5. Total Venues":"SELECT COUNT(*) AS TotalVenues FROM venues;",
            "6. Top 10 Run Scorers":"SELECT TOP 10 p.player_name AS Player,SUM(s.runs) AS TotalRuns FROM player_match_stats s JOIN players p ON s.player_id=p.player_id GROUP BY p.player_name ORDER BY TotalRuns DESC;",
            "7. Top 10 Wicket Takers":"SELECT TOP 10 p.player_name AS Player,SUM(s.wickets) AS TotalWickets FROM player_match_stats s JOIN players p ON s.player_id=p.player_id GROUP BY p.player_name ORDER BY TotalWickets DESC;",
            "8. Most Sixes":"SELECT TOP 10 p.player_name AS Player,SUM(s.sixes) AS TotalSixes FROM player_match_stats s JOIN players p ON s.player_id=p.player_id GROUP BY p.player_name ORDER BY TotalSixes DESC;",
            "9. Most Fours":"SELECT TOP 10 p.player_name AS Player,SUM(s.fours) AS TotalFours FROM player_match_stats s JOIN players p ON s.player_id=p.player_id GROUP BY p.player_name ORDER BY TotalFours DESC;",
            "10. Highest Individual Scores":"SELECT TOP 10 p.player_name AS Player,s.runs AS Runs,s.balls_faced AS Balls,s.match_id AS MatchID FROM player_match_stats s JOIN players p ON s.player_id=p.player_id ORDER BY s.runs DESC;",
            "11. Best Bowling Performances":"SELECT TOP 10 p.player_name AS Player,s.wickets AS Wickets,s.runs_conceded AS RunsConceded,s.overs AS Overs,s.match_id AS MatchID FROM player_match_stats s JOIN players p ON s.player_id=p.player_id WHERE s.overs>0 ORDER BY s.wickets DESC,s.runs_conceded ASC;",
            "12. Highest Strike Rates":"SELECT TOP 10 p.player_name AS Player,SUM(s.runs) AS Runs,SUM(s.balls_faced) AS Balls,CAST(SUM(s.runs)*100.0/NULLIF(SUM(s.balls_faced),0) AS DECIMAL(10,2)) AS StrikeRate FROM player_match_stats s JOIN players p ON s.player_id=p.player_id GROUP BY p.player_name HAVING SUM(s.balls_faced)>=50 ORDER BY StrikeRate DESC;",
            "13. Most Matches Recorded":"SELECT TOP 10 p.player_name AS Player,COUNT(DISTINCT s.match_id) AS MatchesPlayed FROM player_match_stats s JOIN players p ON s.player_id=p.player_id GROUP BY p.player_name ORDER BY MatchesPlayed DESC;",
            "14. Average Runs Per Match":"SELECT TOP 10 p.player_name AS Player,COUNT(DISTINCT s.match_id) AS MatchesPlayed,SUM(s.runs) AS TotalRuns,CAST(SUM(s.runs)*1.0/COUNT(DISTINCT s.match_id) AS DECIMAL(10,2)) AS AverageRunsPerMatch FROM player_match_stats s JOIN players p ON s.player_id=p.player_id GROUP BY p.player_name HAVING COUNT(DISTINCT s.match_id)>=5 ORDER BY AverageRunsPerMatch DESC;",
            "15. Top All-Rounders":"SELECT TOP 10 p.player_name AS Player,SUM(s.runs) AS TotalRuns,SUM(s.wickets) AS TotalWickets FROM player_match_stats s JOIN players p ON s.player_id=p.player_id GROUP BY p.player_name HAVING SUM(s.runs)>0 AND SUM(s.wickets)>0 ORDER BY TotalRuns DESC,TotalWickets DESC;",
            "16. Matches Per Team":"SELECT t.team_name AS Team,COUNT(*) AS MatchesPlayed FROM teams t JOIN matches m ON t.team_id=m.team1_id OR t.team_id=m.team2_id GROUP BY t.team_name ORDER BY MatchesPlayed DESC;",
            "17. Matches Per Venue":"SELECT v.venue_name AS Venue,v.city AS City,COUNT(m.match_id) AS TotalMatches FROM venues v LEFT JOIN matches m ON v.venue_id=m.venue_id GROUP BY v.venue_name,v.city ORDER BY TotalMatches DESC;",
            "18. Series With Most Matches":"SELECT s.series_name AS Series,COUNT(m.match_id) AS TotalMatches FROM series s LEFT JOIN matches m ON s.series_id=m.series_id GROUP BY s.series_name ORDER BY TotalMatches DESC;",
            "19. Match Format Distribution":"SELECT match_format AS Format,COUNT(*) AS TotalMatches FROM matches GROUP BY match_format ORDER BY TotalMatches DESC;",
            "20. Recent 20 Matches":"SELECT TOP 20 m.match_id AS MatchID,t1.team_name AS Team1,t2.team_name AS Team2,m.match_date AS MatchDate,m.match_format AS Format,m.status AS Status FROM matches m LEFT JOIN teams t1 ON m.team1_id=t1.team_id LEFT JOIN teams t2 ON m.team2_id=t2.team_id ORDER BY m.match_date DESC;",
            "21. Matches With Scores":"SELECT TOP 20 m.match_id AS MatchID,t1.team_name AS Team1,m.team1_score AS Team1Score,t2.team_name AS Team2,m.team2_score AS Team2Score,m.status AS Status FROM matches m LEFT JOIN teams t1 ON m.team1_id=t1.team_id LEFT JOIN teams t2 ON m.team2_id=t2.team_id WHERE m.team1_score IS NOT NULL OR m.team2_score IS NOT NULL ORDER BY m.match_date DESC;",
            "22. Team-Wise Total Runs":"SELECT t.team_name AS Team,SUM(s.runs) AS TotalRuns FROM player_match_stats s JOIN teams t ON s.team_id=t.team_id GROUP BY t.team_name ORDER BY TotalRuns DESC;",
            "23. Team-Wise Total Wickets":"SELECT t.team_name AS Team,SUM(s.wickets) AS TotalWickets FROM player_match_stats s JOIN teams t ON s.team_id=t.team_id GROUP BY t.team_name ORDER BY TotalWickets DESC;",
            "24. Fifty Plus Scores":"SELECT p.player_name AS Player,s.runs AS Runs,s.balls_faced AS Balls,s.fours AS Fours,s.sixes AS Sixes,s.match_id AS MatchID FROM player_match_stats s JOIN players p ON s.player_id=p.player_id WHERE s.runs>=50 ORDER BY s.runs DESC;",
            "25. Single-Match All-Round Performances":"SELECT p.player_name AS Player,s.match_id AS MatchID,s.runs AS Runs,s.wickets AS Wickets,s.runs_conceded AS RunsConceded FROM player_match_stats s JOIN players p ON s.player_id=p.player_id WHERE s.runs>=30 AND s.wickets>=2 ORDER BY s.runs DESC,s.wickets DESC;"
        }
        selected=st.selectbox("Select analytical query",list(QUERIES.keys()))
        st.code(QUERIES[selected],language="sql")
        if st.button("Run Query",use_container_width=True):
            try:
                result=read_sql(QUERIES[selected]); st.success(f"{len(result):,} row(s) returned.")
                numeric_cols=result.select_dtypes(include="number").columns.tolist(); text_cols=[c for c in result.columns if c not in numeric_cols]
                if len(result)>1 and numeric_cols and text_cols:
                    chart_df=result.head(15); xcol=text_cols[0]; ycol=numeric_cols[0]
                    fig=px.bar(chart_df,x=xcol,y=ycol,title=selected.split('. ',1)[-1]); fig.update_traces(marker=dict(color=chart_df[ycol],colorscale=[[0,"#48257c"],[1,"#b86fff"]])); fig.update_xaxes(tickangle=-25); st.plotly_chart(style_plot(fig,360,False),use_container_width=True,config={"displayModeBar":False})
                dark_table(result,100)
                st.download_button("Download CSV",result.to_csv(index=False).encode("utf-8"),file_name="sql_result.csv",mime="text/csv")
            except Exception as error:
                st.error(f"Query failed: {error}")

    elif st.session_state.current_page == "CRUD":
        page_heading(
            "DATABASE MANAGEMENT",
            "Player",
            "CRUD Operations.",
            "Manage player records from the dedicated Database Console on the right. Results and confirmations appear here.",
        )

        if "crud_notice" not in st.session_state:
            st.session_state.crud_notice = None

        if st.session_state.crud_notice:
            notice_type, notice_text = st.session_state.crud_notice
            if notice_type == "success":
                st.success(notice_text)
            elif notice_type == "error":
                st.error(notice_text)
            elif notice_type == "warning":
                st.warning(notice_text)
            else:
                st.info(notice_text)
            st.session_state.crud_notice = None

        with st.sidebar:
            st.markdown(
                """
                <div style="
                    margin-top:16px;
                    padding:15px 16px 13px 16px;
                    border-radius:16px;
                    background:linear-gradient(145deg,rgba(32,24,52,.84),rgba(13,15,25,.96));
                    border:1px solid rgba(169,99,255,.22);
                    box-shadow:0 14px 36px rgba(0,0,0,.18);">
                    <div style="
                        color:#a96aff;
                        font-size:8px;
                        font-weight:800;
                        letter-spacing:2.5px;">
                        DATABASE CONSOLE
                    </div>
                    <div style="
                        margin-top:6px;
                        font-family:'Space Grotesk',sans-serif;
                        font-size:18px;
                        font-weight:700;
                        color:#f1edf8;">
                        Player Management
                    </div>
                    <div style="
                        margin-top:4px;
                        color:#747b8b;
                        font-size:10px;
                        line-height:1.5;">
                        Create, search, update and safely delete player records.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown(
                """
                <div style="
                    color:#7d8393;
                    font-size:9px;
                    font-weight:700;
                    letter-spacing:2px;
                    margin:16px 0 6px 0;">
                    CRUD OPERATION
                </div>
                """,
                unsafe_allow_html=True,
            )

            operation = st.selectbox(
                "CRUD Operation",
                ["Create", "Read", "Update", "Delete"],
                key="crud_right_operation",
                label_visibility="collapsed",
            )

            if operation == "Create":
                player_id = st.number_input(
                    "Player ID",
                    min_value=1,
                    step=1,
                    key="crud_right_create_id",
                )
                player_name = st.text_input(
                    "Player Name",
                    key="crud_right_create_name",
                )
                role = st.text_input(
                    "Role",
                    key="crud_right_create_role",
                )
                batting = st.text_input(
                    "Batting Style",
                    key="crud_right_create_batting",
                )
                bowling = st.text_input(
                    "Bowling Style",
                    key="crud_right_create_bowling",
                )
                country = st.text_input(
                    "Country",
                    key="crud_right_create_country",
                )

                if st.button(
                    "Create Player",
                    key="crud_right_create_button",
                    use_container_width=True,
                ):
                    if not player_name.strip():
                        st.session_state.crud_notice = (
                            "error",
                            "Player name is required.",
                        )
                    else:
                        conn = None
                        try:
                            conn = get_connection()
                            cur = conn.cursor()

                            cur.execute(
                                "SELECT COUNT(*) FROM players WHERE player_id=?",
                                int(player_id),
                            )

                            if cur.fetchone()[0] > 0:
                                st.session_state.crud_notice = (
                                    "error",
                                    "Player ID already exists.",
                                )
                            else:
                                cur.execute(
                                    """
                                    INSERT INTO players
                                    (player_id, player_name, role, batting_style, bowling_style, country)
                                    VALUES (?, ?, ?, ?, ?, ?)
                                    """,
                                    int(player_id),
                                    player_name.strip(),
                                    role.strip() or None,
                                    batting.strip() or None,
                                    bowling.strip() or None,
                                    country.strip() or None,
                                )
                                conn.commit()
                                st.session_state.crud_notice = (
                                    "success",
                                    "Player created successfully.",
                                )
                            cur.close()

                        except Exception as error:
                            if conn:
                                conn.rollback()
                            st.session_state.crud_notice = (
                                "error",
                                f"Create failed: {error}",
                            )
                        finally:
                            if conn:
                                conn.close()

                    st.rerun()

            elif operation == "Read":
                search = st.text_input(
                    "Search Player",
                    key="crud_right_read_search",
                )

            elif operation == "Update":
                update_id = st.number_input(
                    "Player ID to Update",
                    min_value=1,
                    step=1,
                    key="crud_right_update_id",
                )

                if st.button(
                    "Load Player",
                    key="crud_right_load_button",
                    use_container_width=True,
                ):
                    try:
                        df = read_sql(
                            """
                            SELECT
                                player_id,
                                player_name,
                                role,
                                batting_style,
                                bowling_style,
                                country
                            FROM players
                            WHERE player_id=?
                            """,
                            [int(update_id)],
                        )

                        if df.empty:
                            st.session_state.pop("crud_right_edit_player", None)
                            st.session_state.crud_notice = (
                                "error",
                                "Player not found.",
                            )
                        else:
                            st.session_state.crud_right_edit_player = (
                                df.iloc[0].to_dict()
                            )
                            st.session_state.crud_notice = (
                                "success",
                                "Player loaded successfully.",
                            )

                    except Exception as error:
                        st.session_state.crud_notice = (
                            "error",
                            f"Load failed: {error}",
                        )

                    st.rerun()

                if "crud_right_edit_player" in st.session_state:
                    p = st.session_state.crud_right_edit_player

                    update_name = st.text_input(
                        "Player Name",
                        value=str(p.get("player_name") or ""),
                        key="crud_right_update_name",
                    )
                    update_role = st.text_input(
                        "Role",
                        value=str(p.get("role") or ""),
                        key="crud_right_update_role",
                    )
                    update_batting = st.text_input(
                        "Batting Style",
                        value=str(p.get("batting_style") or ""),
                        key="crud_right_update_batting",
                    )
                    update_bowling = st.text_input(
                        "Bowling Style",
                        value=str(p.get("bowling_style") or ""),
                        key="crud_right_update_bowling",
                    )
                    update_country = st.text_input(
                        "Country",
                        value=str(p.get("country") or ""),
                        key="crud_right_update_country",
                    )

                    if st.button(
                        "Update Player",
                        key="crud_right_update_button",
                        use_container_width=True,
                    ):
                        conn = None
                        try:
                            conn = get_connection()
                            cur = conn.cursor()

                            cur.execute(
                                """
                                UPDATE players
                                SET
                                    player_name=?,
                                    role=?,
                                    batting_style=?,
                                    bowling_style=?,
                                    country=?,
                                    updated_at=CURRENT_TIMESTAMP
                                WHERE player_id=?
                                """,
                                update_name.strip(),
                                update_role.strip() or None,
                                update_batting.strip() or None,
                                update_bowling.strip() or None,
                                update_country.strip() or None,
                                int(update_id),
                            )

                            conn.commit()
                            cur.close()

                            st.session_state.crud_right_edit_player = {
                                "player_id": int(update_id),
                                "player_name": update_name.strip(),
                                "role": update_role.strip(),
                                "batting_style": update_batting.strip(),
                                "bowling_style": update_bowling.strip(),
                                "country": update_country.strip(),
                            }

                            st.session_state.crud_notice = (
                                "success",
                                "Player updated successfully.",
                            )

                        except Exception as error:
                            if conn:
                                conn.rollback()
                            st.session_state.crud_notice = (
                                "error",
                                f"Update failed: {error}",
                            )
                        finally:
                            if conn:
                                conn.close()

                        st.rerun()

            elif operation == "Delete":
                delete_id = st.number_input(
                    "Player ID to Delete",
                    min_value=1,
                    step=1,
                    key="crud_right_delete_id",
                )

                confirm = st.checkbox(
                    "Confirm deletion",
                    key="crud_right_delete_confirm",
                )

                if st.button(
                    "Delete Player",
                    key="crud_right_delete_button",
                    use_container_width=True,
                ):
                    if not confirm:
                        st.session_state.crud_notice = (
                            "error",
                            "Please confirm deletion first.",
                        )
                        st.rerun()

                    conn = None
                    try:
                        conn = get_connection()
                        cur = conn.cursor()

                        cur.execute(
                            """
                            SELECT COUNT(*)
                            FROM player_match_stats
                            WHERE player_id=?
                            """,
                            int(delete_id),
                        )

                        if cur.fetchone()[0] > 0:
                            st.session_state.crud_notice = (
                                "error",
                                "This player has match statistics and cannot be deleted safely.",
                            )
                        else:
                            cur.execute(
                                "DELETE FROM players WHERE player_id=?",
                                int(delete_id),
                            )

                            if cur.rowcount == 0:
                                st.session_state.crud_notice = (
                                    "error",
                                    "Player not found.",
                                )
                            else:
                                conn.commit()
                                st.session_state.crud_notice = (
                                    "success",
                                    "Player deleted successfully.",
                                )

                        cur.close()

                    except Exception as error:
                        if conn:
                            conn.rollback()
                        st.session_state.crud_notice = (
                            "error",
                            f"Delete failed: {error}",
                        )
                    finally:
                        if conn:
                            conn.close()

                    st.rerun()

        # Main CRUD display
        if operation == "Create":
            section_title(
                "Create Player",
                "Fill the fields in the right-side CRUD panel and click Create Player.",
            )
            st.info("Use the Database Console on the right to add a player. The confirmation will appear here.")

        elif operation == "Read":
            section_title(
                "Search Players",
                "Use the right-side search box. Results are displayed here.",
            )

            search_value = st.session_state.get(
                "crud_right_read_search",
                "",
            )

            try:
                if str(search_value).strip():
                    value = f"%{str(search_value).strip()}%"
                    df = read_sql(
                        """
                        SELECT TOP 200
                            player_id AS [Player ID],
                            player_name AS [Player Name],
                            role AS Role,
                            batting_style AS [Batting Style],
                            bowling_style AS [Bowling Style],
                            country AS Country,
                            team_id AS [Team ID]
                        FROM players
                        WHERE player_name LIKE ?
                           OR CAST(player_id AS VARCHAR(20)) LIKE ?
                        ORDER BY player_name
                        """,
                        [value, value],
                    )
                else:
                    df = read_sql(
                        """
                        SELECT TOP 200
                            player_id AS [Player ID],
                            player_name AS [Player Name],
                            role AS Role,
                            batting_style AS [Batting Style],
                            bowling_style AS [Bowling Style],
                            country AS Country,
                            team_id AS [Team ID]
                        FROM players
                        ORDER BY player_name
                        """
                    )

                dark_table(df, 200)

            except Exception as error:
                st.error(f"Players could not be loaded: {error}")

        elif operation == "Update":
            section_title(
                "Update Player",
                "Load and edit the player from the right-side CRUD panel.",
            )

            if "crud_right_edit_player" in st.session_state:
                p = st.session_state.crud_right_edit_player
                preview = pd.DataFrame(
                    [{
                        "Player ID": p.get("player_id"),
                        "Player Name": p.get("player_name"),
                        "Role": p.get("role"),
                        "Batting Style": p.get("batting_style"),
                        "Bowling Style": p.get("bowling_style"),
                        "Country": p.get("country"),
                    }]
                )
                dark_table(preview, 1)
            else:
                st.info("Enter a Player ID on the right and click Load Player.")

        elif operation == "Delete":
            section_title(
                "Delete Player",
                "Safe deletion controls are available in the right-side CRUD panel.",
            )
            st.warning(
                "Players linked to match statistics remain protected from deletion."
            )

