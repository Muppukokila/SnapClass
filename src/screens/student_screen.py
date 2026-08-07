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

    # Header
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

    # Enrolled subjects header
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

    # Load subjects and attendance
    with st.spinner("Loading your enrolled subjects..."):
        subjects = get_student_subjects(student_id)
        logs = get_student_attendance(student_id)

    # Calculate attendance statistics
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

    # No subjects
    if not subjects:
        st.info("You are not enrolled in any subjects yet.")
        footer_dashboard()
        return

    # Display subjects
    cols = st.columns(2)

    for i, sub_node in enumerate(subjects):

        sub = sub_node.get("subjects")

        # Protect against missing related subject
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

        def unenroll_button(
            student_id=student_id,
            subject_id=sid,
            subject_name=sub["name"],
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
                name=sub["name"],
                code=sub["subject_code"],
                section=sub["section"],
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


def student_screen():

    # Page styling
    style_background_dashboard()
    style_base_layout()

    # If already logged in
    if "student_data" in st.session_state:
        student_dashboard()
        return

    # Header
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

    # Login title
    st.header(
        "Login using FaceID",
        text_alignment="center",
    )

    st.space()
    st.space()

    show_registration = False

    # Camera
    photo_source = st.camera_input(
        "Position your face in the center"
    )

    if photo_source:

        img = np.array(
            Image.open(photo_source).convert("RGB")
        )

        with st.spinner("AI is scanning..."):

            try:
                detected, all_ids, num_faces = predict_attendance(
                    img
                )

            except Exception as e:
                st.error(
                    f"Face recognition failed: {e}"
                )
                return

            # No face
            if num_faces == 0:
                st.warning(
                    "Face not found! Please position your face clearly."
                )

            # Multiple faces
            elif num_faces > 1:
                st.warning(
                    "Multiple faces found. Please make sure only one person is visible."
                )

            # Exactly one face
            else:

                if detected:

                    student_id = list(detected.keys())[0]

                    # Convert ID safely
                    try:
                        student_id = int(student_id)
                    except (ValueError, TypeError):
                        st.error(
                            "Invalid student ID detected."
                        )
                        return

                    # Get students
                    try:
                        all_students = get_all_students()
                    except Exception as e:
                        st.error(
                            f"Unable to load student records: {e}"
                        )
                        return

                    # Find matching student
                    student = next(
                        (
                            s
                            for s in all_students
                            if int(s["student_id"]) == student_id
                        ),
                        None,
                    )

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
                        st.info(
                            "Face recognized, but no matching student record was found."
                        )

                else:

                    st.info(
                        "Face not recognized! You might be a new student."
                    )

                    show_registration = True

    # --------------------------------------------------
    # STUDENT REGISTRATION
    # --------------------------------------------------

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
                "Enroll your voice if you want to use voice-only attendance."
            )

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

            # Create account
            if st.button(
                "Create Account",
                type="primary",
                width="stretch",
            ):

                if not new_name.strip():

                    st.warning(
                        "Please enter your name!"
                    )

                else:

                    with st.spinner(
                        "Creating profile..."
                    ):

                        try:

                            # Convert captured image
                            img = np.array(
                                Image.open(
                                    photo_source
                                ).convert("RGB")
                            )

                            # Extract face embedding
                            encodings = get_face_embeddings(
                                img
                            )

                            if not encodings:

                                st.error(
                                    "Couldn't capture your facial features. "
                                    "Please try again with better lighting."
                                )

                            else:

                                # Face embedding
                                face_emb = encodings[0].tolist()

                                # Voice embedding
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
                                            f"Voice enrollment failed. "
                                            f"Continuing with face registration. "
                                            f"Details: {e}"
                                        )

                                # Create student
                                response_data = create_student(
                                    new_name.strip(),
                                    face_embedding=face_emb,
                                    voice_embedding=voice_emb,
                                )

                                if response_data:

                                    # Retrain classifier
                                    try:
                                        train_classifier()
                                    except Exception as e:
                                        st.warning(
                                            f"Profile created, but face classifier "
                                            f"could not be retrained: {e}"
                                        )

                                    # Login student
                                    st.session_state.is_logged_in = True
                                    st.session_state.user_role = "student"
                                    st.session_state.student_data = response_data[0]

                                    st.toast(
                                        f"Profile Created! Hi {new_name.strip()}!"
                                    )

                                    time.sleep(1)
                                    st.rerun()

                                else:

                                    st.error(
                                        "Student profile could not be created."
                                    )

                        except Exception as e:

                            st.error(
                                f"Unable to create student profile: {e}"
                            )

    footer_dashboard()
