

import streamlit as st

from src.screens.home\_screen import home\_screen
from src.screens.teacher\_screen import teacher\_screen
from src.screens.student\_screen import student\_screen

from src.components.dialog\_auto\_enroll import auto\_enroll\_dialog

def main():
st.set\_page\_config(
page\_title='SnapClass - Making Attendance faster using AI',
page\_icon= "[https://i.ibb.co/YTYGn5qV/logo.png](https://i.ibb.co/YTYGn5qV/logo.png)"
)
if 'login\_type' not in st.session\_state:
st.session\_state['login\_type'] = None

```
match st.session_state['login_type']:
    case 'teacher':
        teacher_screen()

    case 'student':
        student_screen()
    
    case None:
        home_screen()


join_code = st.query_params.get("join-code")

if join_code:
    st.write("DEBUG - Join code:", join_code)
    st.write("DEBUG - Session state:", dict(st.session_state))

    if st.session_state.get("login_type") != "student":
        st.session_state["login_type"] = "student"
        st.rerun()

    if (
        st.session_state.get("is_logged_in")
        and st.session_state.get("user_role") == "student"
    ):
        auto_enroll_dialog(join_code)
```

main()
