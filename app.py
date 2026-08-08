import streamlit as st

from src.screens.home_screen import home_screen
from src.screens.teacher_screen import teacher_screen
from src.screens.student_screen import student_screen

from src.components.dialog_auto_enroll import auto_enroll_dialog


def main():

    # --------------------------------------------------
    # PAGE CONFIGURATION
    # --------------------------------------------------

    st.set_page_config(
        page_title="SnapClass - Making Attendance faster using AI",
        page_icon="https://i.ibb.co/YTYGn5qV/logo.png",
        layout="wide",
    )

    # --------------------------------------------------
    # INITIALIZE SESSION STATE
    # --------------------------------------------------

    if "login_type" not in st.session_state:
        st.session_state["login_type"] = None

    # --------------------------------------------------
    # GET QR JOIN CODE
    # --------------------------------------------------

    join_code = st.query_params.get("join-code")

    # --------------------------------------------------
    # QR CODE LOGIN FLOW
    # --------------------------------------------------

    if join_code:

        # QR links are only for students.
        # Send the user to the student login screen.
        if st.session_state.get("login_type") != "student":
            st.session_state["login_type"] = "student"
            st.rerun()

    # --------------------------------------------------
    # DISPLAY CURRENT SCREEN
    # --------------------------------------------------

    login_type = st.session_state.get("login_type")

    if login_type == "teacher":

        teacher_screen()

    elif login_type == "student":

        student_screen()

    else:

        home_screen()

    # --------------------------------------------------
    # AUTO ENROLLMENT AFTER STUDENT LOGIN
    # --------------------------------------------------

    if (
        join_code
        and st.session_state.get("is_logged_in") is True
        and st.session_state.get("user_role") == "student"
        and st.session_state.get("student_data")
    ):

        auto_enroll_dialog(join_code)


# --------------------------------------------------
# APPLICATION ENTRY POINT
# --------------------------------------------------

if __name__ == "__main__":
    main()
