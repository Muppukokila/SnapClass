import streamlit as st
import time

from src.database.db import enroll_student_to_subject
from src.database.config import supabase


@st.dialog("Quick Enrollment")
def auto_enroll_dialog(subject_code):

    # Get logged-in student
    student_data = st.session_state.get("student_data")

    if not student_data:
        st.error("Student session not found.")
        if st.button("Close"):
            st.query_params.clear()
            st.rerun()
        return

    student_id = student_data["student_id"]

    # Find subject using subject code
    try:
        res = (
            supabase
            .table("subjects")
            .select("subject_id, name, subject_code")
            .eq("subject_code", subject_code)
            .execute()
        )
    except Exception as e:
        st.error(f"Could not load subject: {str(e)}")
        return

    if not res.data:
        st.error("Subject Code not found!")

        if st.button("Close"):
            st.query_params.clear()
            st.rerun()

        return

    subject = res.data[0]
    subject_id = subject["subject_id"]
    subject_name = subject["name"]

    # Check whether student is already enrolled
    try:
        check = (
            supabase
            .table("subject_students")
            .select("*")
            .eq("subject_id", subject_id)
            .eq("student_id", student_id)
            .execute()
        )
    except Exception as e:
        st.error(f"Could not check enrollment: {str(e)}")
        return

    if check.data:
        st.info("You're already enrolled in this subject!")

        if st.button("Got it!", type="primary"):
            st.query_params.clear()
            st.rerun()

        return

    # Enrollment confirmation
    st.markdown(
        f"Would you like to enroll in **{subject_name}**?"
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("No thanks", width="stretch"):
            st.query_params.clear()
            st.rerun()

    with col2:
        if st.button(
            "Yes, enroll now!",
            type="primary",
            width="stretch"
        ):
            try:
                result = enroll_student_to_subject(
                    student_id,
                    subject_id
                )

                if result:
                    st.success("Joined successfully!")
                    time.sleep(1)
                    st.query_params.clear()
                    st.rerun()
                else:
                    st.error("Enrollment failed.")

            except Exception as e:
                st.error(f"Enrollment failed: {str(e)}")
