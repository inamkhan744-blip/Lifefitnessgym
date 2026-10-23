import os
import re

# 1. database.py mein caching add karein
path_db = "database.py"
if os.path.exists(path_db):
    with open(path_db, "r") as f:
        db_content = f.read()
    
    if "def get_user_by_username" in db_content and "@st.cache_data" not in db_content:
        # Streamlit import karein agar nahi hai
        if "import streamlit as st" not in db_content:
            db_content = "import streamlit as st\n" + db_content
        
        # Cache laga dein (60 seconds ke liye)
        db_content = db_content.replace(
            "def get_user_by_username(username):",
            "@st.cache_data(ttl=60, show_spinner=False)\ndef get_user_by_username(username):"
        )
        with open(path_db, "w") as f:
            f.write(db_content)
        print("✅ database.py optimized with caching!")

# 2. auth.py mein Spinner add karein
path_auth = "auth.py"
if os.path.exists(path_auth):
    with open(path_auth, "r") as f:
        auth_content = f.read()
    
    # Form submit button ke andar spinner lagayein
    if "with st.spinner(\"Verifying details..." not in auth_content:
        # Dhoondein ke form submit kahan ho raha hai
        if "if st.form_submit_button" in auth_content:
            # Ek simple trick: button ko disable karein aur spinner dikhayein
            auth_content = auth_content.replace(
                "if st.form_submit_button(\"Sign In\")",
                "if st.form_submit_button(\"Sign In\"):\n        with st.spinner(\"Verifying details... ⏳\"):"
            )
            print("✅ auth.py updated with loading spinner!")
        else:
            print("ℹ️ auth.py mein form_submit_button nahi mila, manual check karein.")
    
    with open(path_auth, "w") as f:
        f.write(auth_content)

print("⚠️ Note: Pehli baar app kholne mein 5-10 second lag sakte hain kyunki Replit app ko 'wake up' karna hota hai. Uske baad ye fast chalega.")
