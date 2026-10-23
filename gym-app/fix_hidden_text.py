import os

count = 0
for root, dirs, files in os.walk("."):
    if "__pycache__" in root or ".git" in root or "venv" in root:
        continue
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            with open(path, "r") as f:
                content = f.read()

            new_content = content
            
            # Fix hardcoded white/light text in inline styles
            new_content = new_content.replace("color:var(--gp-text)", "color:var(--gp-text)")
            new_content = new_content.replace("color:var(--gp-text)", "color:var(--gp-text)")
            new_content = new_content.replace("color:var(--gp-text)", "color:var(--gp-text)")
            new_content = new_content.replace("color:var(--gp-text)", "color:var(--gp-text)")
            
            # Fix hardcoded dark borders
            new_content = new_content.replace("border-bottom:1px solid var(--gp-border);", "border-bottom:1px solid var(--gp-border);")
            new_content = new_content.replace("border-bottom:1px solid var(--gp-border);", "border-bottom:1px solid var(--gp-border);")
            
            if new_content != content:
                with open(path, "w") as f:
                    f.write(new_content)
                print(f"✅ Fixed hidden text in {path}")
                count += 1

if count == 0:
    print("ℹ️ Koi hardcoded color nahi mila. Shayed masla kisi aur file mein hai.")
else:
    print(f"🎉 Total {count} files fix ho gayi hain!")
