```python
import streamlit as st

from src.screens.home_screen import home_screen
from src.screens.teacher_screen import teacher_screen
from src.screens.student_screen import student_screen
from src.components.dialog_auto_enroll import auto_enroll_dialog


def main():
    st.set_page_config(
        page_title="SnapClass - Making Attendance faster using AI",
        page_icon="https://i.ibb.co/YTYGn5qV/logo.png",
    )

    # Initialize session state
    if "login_type" not in st.session_state:
        st.session_state["login_type"] = None

    # --------------------------------------------------
    # HANDLE JOIN CODE FROM URL
    # Example:
    # https://snapclass-main.streamlit.app/?join-code=cs102
    # --------------------------------------------------

    join_code = st.query_params.get("join-code")

    if join_code:
        join_code = join_code.strip().lower()

        # Save join code for use throughout the app
        st.session_state["join_code"] = join_code

        # Automatically switch to student mode
        if st.session_state["login_type"] != "student":
            st.session_state["login_type"] = "student"
            st.rerun()

    # --------------------------------------------------
    # SCREEN NAVIGATION
    # --------------------------------------------------

    match st.session_state["login_type"]:

        case "teacher":
            teacher_screen()

        case "student":
            student_screen()

        case None:
            home_screen()

    # --------------------------------------------------
    # AUTO ENROLL
    # --------------------------------------------------

    if (
        join_code
        and st.session_state.get("is_logged_in")
        and st.session_state.get("user_role") == "student"
    ):
        auto_enroll_dialog(join_code)


if __name__ == "__main__":
    main()
```
