import streamlit as st
import pandas as pd
import time
import re
from datetime import datetime

# 💫 PAGE SETUP
st.set_page_config(
    page_title="PMTA",
    page_icon="🎈",
    layout="wide"
)


st.markdown("""
<style>
body {
    font-family: "Comic Sans MS", "Comic Neue", cursive;
    background: linear-gradient(135deg, #ffecd2, #fcb69f);
    color: #2b2b2b;
}
h1, h2, h3, .stMarkdown p, .stMarkdown span {
    color: #000000 !important;  /* 🔥 Force all headings and motto text to black */
}
.stApp { background: transparent; }
section[data-testid="stSidebar"] {
    background: rgba(255, 255, 255, 0.6);
    backdrop-filter: blur(15px);
    border-radius: 15px;
}
.stFileUploader label, .stDownloadButton button, .stButton button {
    background: linear-gradient(135deg, #89f7fe, #66a6ff);
    color: #1b1b1b !important;
    border: none;
    border-radius: 10px;
    padding: 0.6em 1.5em;
    transition: all 0.3s ease;
    font-weight: bold;
    font-family: "Comic Neue", cursive;
    box-shadow: 2px 3px 6px rgba(0,0,0,0.2);
}
.stFileUploader label:hover, .stDownloadButton button:hover, .stButton button:hover {
    transform: rotate(-2deg) scale(1.05);
    box-shadow: 0 0 20px rgba(102, 166, 255, 0.6);
}
.stProgress > div > div > div {
    background: linear-gradient(90deg, #ff758c, #ff7eb3);
}
div[data-testid="stAlert"] {
    background: rgba(255, 255, 255, 0.5);
    border-left: 6px solid #ff7eb3;
    border-radius: 12px;
}
footer { visibility: hidden; }

/* 🎯 Force specific sections (title, motto, step text) to black */
h1, h2, h3, p, label {
    color: #000000 !important;
}
</style>
""", unsafe_allow_html=True)


# 🎈 HEADER SECTION
st.title("PMTA Smart IP Fetcher — Developed by Jayanth")
st.markdown("""
**Motto:** “If it works, don’t ask how.”
""")
st.divider()

# 📂 FILE UPLOAD
st.subheader("Step 1: Drop your Excel mess here 🍪")
uploaded_files = st.file_uploader(
    "Drop exactly TWO Excel files — one detailed (with IP, PMTA, rDNS, fDNS) and one PMTA-only.",
    type=["xlsx"],
    accept_multiple_files=True
)

# 🧠 LOGIC
if len(uploaded_files) == 2:
    st.info("🦄 Nice! Two files received. Let’s see what nonsense they hold...")

    df1 = pd.read_excel(uploaded_files[0])
    df2 = pd.read_excel(uploaded_files[1])

    def is_detailed(df):
        return {"IP", "rDNS", "fDNS", "PMTA"}.issubset(df.columns)

    if is_detailed(df1):
        ex1, ex2 = df1, df2
    elif is_detailed(df2):
        ex1, ex2 = df2, df1
    else:
        st.error("😡 Both files are missing IP, rDNS, fDNS, PMTA. Even my goldfish can do better.")
        st.stop()

    st.success(f"""
    🧩 Smart Detector says:
    - **Detailed file:** `{uploaded_files[0].name if is_detailed(df1) else uploaded_files[1].name}`
    - **PMTA list file:** `{uploaded_files[1].name if is_detailed(df1) else uploaded_files[0].name}`
    """)

    with st.expander("👀 Peek at the detailed file"):
        st.dataframe(ex1.head(10))
    with st.expander("👀 Peek at the PMTA-only file"):
        st.dataframe(ex2.head(10))

    ex2 = ex2.drop_duplicates(subset=["PMTA"], keep="first")
    ex1 = ex1[ex1["IP"] != ex1["PMTA"]]

    st.subheader("Abracadabra, IPs sorted! 🧙‍♂️🔮")
    progress = st.progress(0)
    status = st.empty()

    for i in range(101):
        time.sleep(0.015)
        progress.progress(i)
        if i < 40:
            status.text("🤓 Calculating random numbers that make me look smart...")
        elif i < 70:
            status.text("🔮 Summoning DNS spirits...")
        elif i < 90:
            status.text("🦾 Crunching data like a pro...")
        else:
            status.text("🎁 Wrapping your results with glitter...")

    # 🧩 PRIORITY MAGIC
    def is_priority1_rDNS(value):
        if not isinstance(value, str) or value in {"No_rDNS", ""} or ":" in value:
            return False
        digits = sum(c.isdigit() for c in value)
        return digits >= 7 or digits == 0

    def get_priority_ips(group):
        p1 = group[group["rDNS"].apply(is_priority1_rDNS)]["IP"].astype(str).tolist()
        if len(p1) < 4:
            no_rdns = group[group["rDNS"] == "No_rDNS"]["IP"].astype(str).tolist()
            for ip in no_rdns:
                if ip not in p1:
                    p1.append(ip)
                if len(p1) == 4:
                    break
        p2 = group[(group["fDNS"] == "No_fDNS") & (~group["IP"].isin(p1))]["IP"].astype(str).tolist()
        combined = list(dict.fromkeys(p1 + p2))[:4]
        return pd.Series({
            "Priority1_rDNS": ",".join(ip for ip in combined if ip in p1),
            "Priority2_No_fDNS": ",".join(ip for ip in combined if ip in p2)
        })

    grouped_df = ex1.groupby("PMTA").apply(get_priority_ips).reset_index()
    result = ex2.merge(grouped_df, on="PMTA", how="left").fillna("")

    # 🧹 CLEANUP: keep only valid IPv4, remove IPv6 / domains / junk
    ipv4_pattern = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
    def clean_ip_list(cell):
        if not isinstance(cell, str):
            return ""
        ips = ipv4_pattern.findall(cell)
        return ",".join(sorted(set(ips)))

    result["Priority1_rDNS"] = result["Priority1_rDNS"].apply(clean_ip_list)
    result["Priority2_No_fDNS"] = result["Priority2_No_fDNS"].apply(clean_ip_list)

    output_filename = f"Jayanth_PMTA_Output_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx"
    result.to_excel(output_filename, index=False)

    st.balloons()
    st.success("🎉 Done! your Excel is now shiny, clean, and IPv6-free 💫")

    st.download_button(
        label="🎁 Click to Download My Awesome Excel",
        data=open(output_filename, "rb").read(),
        file_name=output_filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

elif len(uploaded_files) > 2:
    st.warning("😤 Woah there, too many files! I have two hands, not eight.")
else:
    st.info("👆 Upload two Excel files to begin the magic show 🎩✨")


