import re

path = "themes.py"
with open(path, "r") as f:
    lines = f.readlines()

new_lines = []
skip = False

for line in lines:
    # Jab hume @media (min-width: 1024px) dikhe, to skip mode on kar do
    if "@media (min-width: 1024px)" in line:
        skip = True
        continue
    
    # Jab tak skip mode on hai, tab tak lines ko ignore karo
    if skip:
        # Jab block ka closing bracket '}' aa jaye, to skip mode off kar do
        if "}" in line:
            skip = False
        continue
    
    # Agar line mein padding-left 3rem wala error bacha ho to usay bhi hata do
    if "padding-left: 3rem" in line or "padding-right: 3rem" in line:
        continue
        
    new_lines.append(line)

with open(path, "w") as f:
    f.writelines(new_lines)

print("✅ themes.py se kharab code successfully delete ho gaya!")
print("Ab aap app ko Stop karke Run karein.")
