import re

path = "gym_pages/ai_assistant.py"
with open(path, "r") as f:
    content = f.read()

new_func = """def show_loading_overlay(message="Loading GymPro..."):
    import random
    import time
    
    quotes = [
        "Sweat is just fat crying. 💦",
        "The body achieves what the mind believes. 🧠",
        "Push harder than yesterday if you want a different tomorrow. 🔥",
        "Success starts with self-discipline. 🏆",
        "Don't limit your challenges. Challenge your limits. 💪",
        "Your only limit is you. 🚀"
    ]
    quote = random.choice(quotes)

    placeholder = st.empty()

    particles = "".join([
        f"<div style='position: absolute; bottom: -50px; left: {random.randint(0,100)}%; width: {random.randint(2,6)}px; height: {random.randint(2,6)}px; border-radius: 50%; background: white; box-shadow: 0 0 15px #3b82f6; animation: floatUp {random.randint(4,10)}s linear infinite; animation-delay: -{random.randint(1,5)}s;'></div>"
        for _ in range(30)
    ])

    loader_html = f'''<style>
    @keyframes floatUp {{0% {{transform: translateY(0) scale(1); opacity: 0;}} 50% {{opacity: 0.8;}} 100% {{transform: translateY(-1000px) scale(1.5); opacity: 0;}}}}
    @keyframes pulseRing {{0% {{transform: translate(-50%, -50%) scale(0.8); opacity: 1; border-width: 4px;}} 100% {{transform: translate(-50%, -50%) scale(2.5); opacity: 0; border-width: 1px;}}}}
    @keyframes pulseLogo {{0%, 100% {{transform: translateY(0) scale(1); filter: drop-shadow(0 0 20px #8b5cf6);}} 50% {{transform: translateY(-10px) scale(1.1); filter: drop-shadow(0 0 60px #3b82f6);}}}}
    @keyframes shineText {{to {{background-position: 200% center;}}}}
    @keyframes loadBar {{0% {{left: -30%;}} 100% {{left: 100%;}}}}
    </style>
    <div style='position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: radial-gradient(circle at center, #1e1b4b 0%, #0b0f19 100%); display: flex; flex-direction: column; align-items: center; justify-content: center; z-index: 9999999; font-family: "Inter", sans-serif; overflow: hidden;'>
        {particles}
        <div style='position: absolute; top: 50%; left: 50%; width: 150px; height: 150px; border-radius: 50%; border: 4px solid #8b5cf6; box-shadow: 0 0 30px #8b5cf6, inset 0 0 20px #8b5cf6; animation: pulseRing 3s cubic-bezier(0.1, 0.8, 0.2, 1) infinite; animation-delay: 0s;'></div>
        <div style='position: absolute; top: 50%; left: 50%; width: 150px; height: 150px; border-radius: 50%; border: 4px solid #8b5cf6; box-shadow: 0 0 30px #8b5cf6, inset 0 0 20px #8b5cf6; animation: pulseRing 3s cubic-bezier(0.1, 0.8, 0.2, 1) infinite; animation-delay: 1s;'></div>
        <div style='position: absolute; top: 50%; left: 50%; width: 150px; height: 150px; border-radius: 50%; border: 4px solid #8b5cf6; box-shadow: 0 0 30px #8b5cf6, inset 0 0 20px #8b5cf6; animation: pulseRing 3s cubic-bezier(0.1, 0.8, 0.2, 1) infinite; animation-delay: 2s;'></div>
        <div style='width: 130px; height: 130px; border-radius: 35px; background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.15); box-shadow: inset 0 0 30px rgba(255, 255, 255, 0.1), 0 20px 40px rgba(0,0,0,0.6); backdrop-filter: blur(15px); display: flex; align-items: center; justify-content: center; z-index: 10; margin-bottom: 30px;'>
            <div style='font-size: 4.5rem; animation: pulseLogo 3s ease-in-out infinite; z-index: 10;'>🏋️‍♂️</div>
        </div>
        <div style='font-size: 3rem; font-weight: 900; letter-spacing: 10px; background: linear-gradient(90deg, #60a5fa, #a78bfa, #60a5fa); background-size: 200% auto; -webkit-background-clip: text; -webkit-text-fill-color: transparent; animation: shineText 3s linear infinite; z-index: 10; margin-bottom: 20px; text-shadow: 0 0 40px rgba(96, 165, 250, 0.6);'>
            GYMPRO
        </div>
        <div style='color: #38bdf8; font-size: 1.1rem; font-weight: 800; letter-spacing: 3px; text-transform: uppercase; z-index: 10; margin-bottom: 25px; text-shadow: 0 0 15px #38bdf8;'>
            {message}
        </div>
        <div style='width: 300px; height: 6px; background: rgba(255, 255, 255, 0.1); border-radius: 10px; overflow: hidden; position: relative; z-index: 10; box-shadow: inset 0 2px 5px rgba(0,0,0,0.5);'>
            <div style='position: absolute; height: 100%; width: 40%; background: linear-gradient(90deg, transparent, #38bdf8, #a78bfa, transparent); animation: loadBar 1.5s ease-in-out infinite; border-radius: 10px; box-shadow: 0 0 15px #38bdf8;'></div>
        </div>
        <div style='position: absolute; bottom: 50px; color: #e2e8f0; font-size: 1rem; font-style: italic; z-index: 10; text-align: center; width: 85%; letter-spacing: 1px; font-weight: 500; text-shadow: 0 0 10px rgba(255,255,255,0.3);'>
            "{quote}"
        </div>
    </div>'''

    with placeholder:
        st.markdown(loader_html, unsafe_allow_html=True)
    
    time.sleep(2.5)
    placeholder.empty()
"""

pattern = re.compile(r"def show_loading_overlay\(.*?(?=\ndef |\Z)", re.DOTALL)
if pattern.search(content):
    content = pattern.sub(new_func + "\n\n", content)
    with open(path, "w") as f:
        f.write(content)
    print("✅ Loading screen fixed and syntax error resolved!")
else:
    print("❌ Could not find function")
