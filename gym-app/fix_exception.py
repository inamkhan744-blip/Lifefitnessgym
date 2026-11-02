path = "gym_pages/settings.py"
with open(path, "r") as f:
    content = f.read()

# Us line ko dhoond kar delete karein jo error de rahi hai
bad_line = '                        st.session_state["theme_picker"] = spec[\'emoji\'] + " " + spec[\'name\'] # Force sidebar match\n'
if bad_line in content:
    content = content.replace(bad_line, "")
    with open(path, "w") as f:
        f.write(content)
    print("✅ Fixed StreamlitAPIException! Removed the conflicting line.")
else:
    # Fallback: Search for the line and remove it
    import re
    content = re.sub(r'\s*st\.session_state\["theme_picker"\] = .*?\n', '\n', content)
    with open(path, "w") as f:
        f.write(content)
    print("✅ Applied fallback fix to remove the conflicting line.")
