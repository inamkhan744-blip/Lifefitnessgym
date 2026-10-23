import re

path = "gym_pages/ai_assistant.py"
with open(path, "r") as f:
    content = f.read()

# Purana dynamic code dhoond kar usay static text se replace karein
old_logic = """    # 🚀 FETCH GYM NAME DYNAMICALLY
    gym_display_name = "Life Fitness Gym" # Default
    try:
        gym_id = st.session_state.get("selected_gym_id")
        if gym_id:
            gym = db.get_gym(gym_id)
            if gym: gym_display_name = gym.name
        else:
            gyms = db.get_all_gyms()
            if gyms: gym_display_name = gyms[0].name
    except Exception:
        pass"""

new_logic = """    # 🚀 STATIC GYM NAME FOR LOADING SCREEN
    gym_display_name = "LIFE FITNESS GYM\""""

if old_logic in content:
    content = content.replace(old_logic, new_logic)
    with open(path, "w") as f:
        f.write(content)
    print("✅ Loading screen name fixed to 'LIFE FITNESS GYM'!")
else:
    print("ℹ️ Pattern not found, but trying a broader fix...")
    # Fallback: replace the whole gym display name variable line
    content = re.sub(r'gym_display_name = .*?\n', 'gym_display_name = "LIFE FITNESS GYM"\n', content, count=1)
    with open(path, "w") as f:
        f.write(content)
    print("✅ Applied fallback fix!")
