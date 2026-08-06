import streamlit as st


def footer_home():
    st.markdown("""
        <div style="
            margin-top:2rem;
            text-align:center;
            font-weight:bold;
            color:white;
            font-size:16px;
        ">
            Created with ❤️ by Kokila
        </div>
    """, unsafe_allow_html=True)


def footer_dashboard():
    st.markdown("""
        <div style="
            margin-top:2rem;
            text-align:center;
            font-weight:bold;
            color:black;
            font-size:16px;
        ">
            Created with ❤️ by Kokila
        </div>
    """, unsafe_allow_html=True)