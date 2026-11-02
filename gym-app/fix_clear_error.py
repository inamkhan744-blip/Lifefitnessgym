import re

path = "app.py"
with open(path, "r") as f:
    content = f.read()

# Remove all instances of _cached_theme_settings.clear()
content = content.replace("            _cached_theme_settings.clear()\n", "")
content = content.replace("        _cached_theme_settings.clear()\n", "")
content = content.replace("    _cached_theme_settings.clear()\n", "")
content = content.replace("_cached_theme_settings.clear()", "")

# Also check for any st.cache_data.clear() that might be causing issues and replace with standard
# (Actually we want st.cache_data.clear() to remain where applicable, but we just remove the broken one)

with open(path, "w") as f:
    f.write(content)
print("✅ Removed broken _cached_theme_settings.clear() from app.py!")
