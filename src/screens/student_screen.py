import streamlit as st
from PIL import Image
import numpy as np
import time

from src.ui.base_layout import (
    style_background_dashboard,
    style_base_layout,
)

from src.components.header import header_dashboard
from src.components.footer import footer_dashboard
from src.components.subject_card import subject_card

from src.pipelines.face_pipeline import (
    predict_attendance,
    get_face_embeddings,
    train_classifier,
)

from src.pipelines.voice_pipeline import get_voice_embedding

from src.database.db import (
    get_all_students,
    create_student,
    get_student_subjects,
    get_student_attendance,
    unenroll_student_to_subject,
)

from src.components.dialog_enroll import enroll_dialog


def student_dashboard():

    student_data = st.session_state.student_data
    student_id = student_data["student_id"]

    # -----------------------------
    # HEADER
    # -----------------------------

    c1, c2 = st.columns(
        2,
        vertical_alignment="center",
        gap="xxlarge",
    )

    with c1:
        header_dashboard()

    with c2:
        st.subheader(f"Welcome, {student_data['name']}")

        if st.button(
            "Logout",
            type="secondary",
            key="student_logout_btn",
            shortcut="control+backspace",
        ):
            st.session_state["is_logged_in"] = False

            if "student_data" in st.session_state:
                del st.session_state.student_data

            st.rerun()

    st.space()

    # -----------------------------
    # SUBJECT HEADER
    # -----------------------------

    c1, c2 = st.columns(2)

    with c1:
        st.header("Your Enrolled Subjects")

    with c2:
        if st.button(
            "Enroll in Subject",
            type="primary",
            width="stretch",
        ):
            enroll_dialog()

    st.divider()

    # -----------------------------
    # LOAD DATA
    # -----------------------------

    with st.spinner("Loading your enrolled subjects..."):

        try:
            subjects = get_student_subjects(student_id)
            logs = get_student_attendance(student_id)

        except Exception as e:
            st.error(f"Unable to load your subjects: {e}")
            footer_dashboard()
            return

    # -----------------------------
    # ATTENDANCE STATISTICS
    # -----------------------------

    stats_map = {}

    for log in logs:

        sid = log["subject_id"]

        if sid not in stats_map:
            stats_map[sid] = {
                "total": 0,
                "attended": 0,
            }

        stats_map[sid]["total"] += 1

        if log.get("is_present"):
            stats_map[sid]["attended"] += 1

    # -----------------------------
    # NO SUBJECTS
    # -----------------------------

    if not subjects:

        st.info(
            "You are not enrolled in any subjects yet."
        )

        footer_dashboard()
        return

    # -----------------------------
    # DISPLAY SUBJECTS
    # -----------------------------

    cols = st.columns(2)

    for i, sub_node in enumerate(subjects):

        sub = sub_node.get("subjects")

        if not sub:
            continue

        sid = sub["subject_id"]

        stats = stats_map.get(
            sid,
            {
                "total": 0,
                "attended": 0,
            },
        )

        subject_name = sub["name"]
        subject_code = sub["subject_code"]
        subject_section = sub["section"]

        def unenroll_button(
            student_id=student_id,
            subject_id=sid,
            subject_name=subject_name,
        ):

            if st.button(
                "Unenroll from this course",
                type="tertiary",
                width="stretch",
                icon=":material/delete_forever:",
                key=f"unenroll_{student_id}_{subject_id}",
            ):

                try:

                    unenroll_student_to_subject(
                        student_id,
                        subject_id,
                    )

                    st.toast(
                        f"Unenrolled from {subject_name} successfully!"
                    )

                    time.sleep(0.5)
                    st.rerun()

                except Exception as e:

                    st.error(
                        f"Unable to unenroll from the course: {e}"
                    )

        with cols[i % 2]:

            subject_card(
                name=subject_name,
                code=subject_code,
                section=subject_section,
                stats=[
                    (
                        "📅",
                        "Total",
                        stats["total"],
                    ),
                    (
                        "✅",
                        "Attended",
                        stats["attended"],
                    ),
                ],
                footer_callback=unenroll_button,
            )

    footer_dashboard()


# ============================================================
# STUDENT SCREEN
# ============================================================

def student_screen():

    # -----------------------------
    # PAGE STYLING
    # -----------------------------

    style_background_dashboard()
    style_base_layout()

    # -----------------------------
    # ALREADY LOGGED IN
    # -----------------------------

    if "student_data" in st.session_state:

        student_dashboard()
        return

    # -----------------------------
    # HEADER
    # -----------------------------

    c1, c2 = st.columns(
        2,
        vertical_alignment="center",
        gap="xxlarge",
    )

    with c1:
        header_dashboard()

    with c2:

        if st.button(
            "Go back to Home",
            type="secondary",
            key="student_home_btn",
            shortcut="control+backspace",
        ):

            st.session_state["login_type"] = None
            st.rerun()

    # -----------------------------
    # LOGIN
    # -----------------------------

    st.header(
        "Login using FaceID",
        text_alignment="center",
    )

    st.space()
    st.space()

    show_registration = False

    # -----------------------------
    # CAMERA
    # -----------------------------

    photo_source = st.camera_input(
        "Position your face in the center"
    )

    if photo_source:

        img = np.array(
            Image.open(photo_source).convert("RGB")
        )

        with st.spinner("AI is scanning..."):

            try:

                detected, all_ids, num_faces = (
                    predict_attendance(img)
                )

            except Exception as e:

                st.error(
                    f"Face recognition failed: {e}"
                )

                return

            # -----------------------------
            # NO FACE
            # -----------------------------

            if num_faces == 0:

                st.warning(
                    "Face not found! Please position your face clearly."
                )

            # -----------------------------
            # MULTIPLE FACES
            # -----------------------------

            elif num_faces > 1:

                st.warning(
                    "Multiple faces found. "
                    "Please make sure only one person is visible."
                )

            # -----------------------------
            # ONE FACE
            # -----------------------------

            else:

                if detected:

                    student_id = list(
                        detected.keys()
                    )[0]

                    # -------------------------
                    # FIND STUDENT
                    # -------------------------

                    try:

                        all_students = get_all_students()

                    except Exception as e:

                        st.error(
                            f"Unable to load student records: {e}"
                        )

                        return

                    student = next(
                        (
                            s
                            for s in all_students
                            if str(s["student_id"])
                            == str(student_id)
                        ),
                        None,
                    )

                    # -------------------------
                    # LOGIN
                    # -------------------------

                    if student:

                        st.session_state.is_logged_in = True
                        st.session_state.user_role = "student"
                        st.session_state.student_data = student

                        st.toast(
                            f"Welcome Back {student['name']}"
                        )

                        time.sleep(1)
                        st.rerun()

                    else:

                        st.warning(
                            "Face recognized, but no matching "
                            "student record was found."
                        )

                # -------------------------
                # NEW STUDENT
                # -------------------------

                else:

                    st.info(
                        "Face not recognized! "
                        "You might be a new student."
                    )

                    show_registration = True

    # ========================================================
    # STUDENT REGISTRATION
    # ========================================================

    if show_registration:

        with st.container(border=True):

            st.header("Register New Profile")

            new_name = st.text_input(
                "Enter your name",
                placeholder="E.g. Hamza Rizvi",
            )

            st.subheader(
                "Optional: Voice Enrollment"
            )

            st.info(
                "Enroll your voice if you want to use "
                "voice-only attendance."
            )

            # -----------------------------
            # VOICE RECORDING
            # -----------------------------

            audio_data = None

            try:

                audio_data = st.audio_input(
                    "Record a short phrase like: "
                    "'I am present' or "
                    "'My name is Akash.'"
                )

            except Exception:

                st.warning(
                    "Voice recording is not available. "
                    "You can continue without voice enrollment."
                )

            # -----------------------------
            # CREATE ACCOUNT
            # -----------------------------

            if st.button(
                "Create Account",
                type="primary",
                width="stretch",
            ):

                if not new_name.strip():

                    st.warning(
                        "Please enter your name!"
                    )

                elif photo_source is None:

                    st.error(
                        "Please capture your face first."
                    )

                else:

                    with st.spinner(
                        "Creating profile..."
                    ):

                        try:

                            # -------------------------
                            # GET IMAGE
                            # -------------------------

                            img = np.array(
                                Image.open(
                                    photo_source
                                ).convert("RGB")
                            )

                            # -------------------------
                            # FACE EMBEDDING
                            # -------------------------

                            encodings = get_face_embeddings(
                                img
                            )

                            if not encodings:

                                st.error(
                                    "Couldn't capture your "
                                    "facial features. "
                                    "Please try again with "
                                    "better lighting."
                                )

                            else:

                                face_emb = (
                                    encodings[0].tolist()
                                )

                                # -------------------------
                                # VOICE EMBEDDING
                                # -------------------------

                                voice_emb = None

                                if audio_data:

                                    try:

                                        voice_emb = (
                                            get_voice_embedding(
                                                audio_data.read()
                                            )
                                        )

                                    except Exception as e:

                                        st.warning(
                                            "Voice enrollment failed. "
                                            "Continuing with face registration."
                                        )

                                # -------------------------
                                # CREATE STUDENT
                                # -------------------------

                                response_data = create_student(
                                    new_name.strip(),
                                    face_embedding=face_emb,
                                    voice_embedding=voice_emb,
                                )

                                # -------------------------
                                # SUCCESS
                                # -------------------------

                                if response_data:

                                    # Train classifier
                                    try:

                                        train_classifier()

                                    except Exception as e:

                                        st.warning(
                                            "Profile created, "
                                            "but face classifier "
                                            f"could not be retrained: {e}"
                                        )

                                    # Login
                                    st.session_state.is_logged_in = True
                                    st.session_state.user_role = "student"
                                    st.session_state.student_data = (
                                        response_data[0]
                                    )

                                    st.toast(
                                        f"Profile Created! "
                                        f"Hi {new_name.strip()}!"
                                    )

                                    time.sleep(1)
                                    st.rerun()

                                else:

                                    st.error(
                                        "Student profile "
                                        "could not be created."
                                    )

                        except Exception as e:

                            st.error(
                                f"Unable to create student profile: {e}"
                            )

    # -----------------------------
    # FOOTER
    # -----------------------------

    footer_dashboard()
