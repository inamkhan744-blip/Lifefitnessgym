# ai_coder_v12.py — V12 ULTIMATE 2.0
# BADE KAAM MODE · Multi-File · Deep Context · Task Planner
# Database 100% Safe · Replit-Level Capabilities

import os, re, json, ast, shutil, time, zipfile, difflib
import requests
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple, Any
from pathlib import Path

# ═══════════════════════════════════════════════════════════
# ⚙️ CONFIG
# ═══════════════════════════════════════════════════════════

PROTECTED_FILES = {"database.py", "auth.py", ".env", "requirements.txt",
                   "gym_pro_v2.db", "gym_pro_v3.db", "gym_pro.db"}
PROTECTED_EXTENSIONS = {".db", ".sqlite", ".sqlite3", ".env", ".key", ".pem"}
PROTECTED_DIRS = {"backups", ".backups", "uploads", "member_photos", ".git",
                  "gym-media", "uploaded_photos"}
ALLOWED_DIRS = {".", "gym_pages", "utils", "components", "face_engine", "gym-app"}

V12_MAX_CHARS = 12000          # Increased for bade kaam
V12_MAX_TOKENS = 10000         # Increased
V12_MAX_RETRIES = 3
V12_MAX_FILES_PER_TASK = 15    # Bade kaam ke liye
V12_BACKUP_ROOT = ".ai_coder_backups"
V12_COMMITS_FILE = ".ai_coder_v12_commits.json"
V12_INDEX_FILE = ".ai_coder_v12_index.json"
V12_MEMORY_FILE = ".ai_coder_v12_memory.json"
V12_TASKS_FILE = ".ai_coder_v12_tasks.json"
V12_SKIP_DIRS = {"__pycache__", ".git", "node_modules", ".streamlit",
                 "backups", ".backups", "uploads", "member_photos",
                 "docs", "logs", "gym-media", "uploaded_photos", V12_BACKUP_ROOT}

# ═══════════════════════════════════════════════════════════
# 🎯 COHERE CONFIG
# ═══════════════════════════════════════════════════════════

COHERE_API_KEY_ENV = "COHERE_API_KEY"
COHERE_MODEL = "command-r-plus-08-2024"
COHERE_MODEL_ALT = "command-r-08-2024"
COHERE_API_URL = "https://api.cohere.com/v2/chat"



# ═══════════════════════════════════════════════════════════
# 🔧 AUTO-IMPORT FIX
# ═══════════════════════════════════════════════════════════

def v12_fix_imports(code: str, file_content: str) -> Tuple[str, List[str]]:
    """Auto-fix common import mistakes based on file's style"""
    fixes = []
    
    # datetime: if file uses 'from datetime import datetime'
    if 'from datetime import datetime' in file_content and 'import datetime' not in file_content.split('from datetime')[0][:200]:
        if 'datetime.datetime.' in code:
            code = code.replace('datetime.datetime.', 'datetime.')
            fixes.append('datetime.datetime → datetime')
    
    # streamlit
    if 'import streamlit as st' in file_content:
        new_code = re.sub(r'\bstreamlit\.(\w+)\(', r'st.\1(', code)
        if new_code != code:
            code = new_code
            fixes.append('streamlit → st')
    
    # pandas
    if 'import pandas as pd' in file_content:
        new_code = re.sub(r'\bpandas\.(\w+)\(', r'pd.\1(', code)
        if new_code != code:
            code = new_code
            fixes.append('pandas → pd')
    
    # numpy
    if 'import numpy as np' in file_content:
        new_code = re.sub(r'\bnumpy\.(\w+)\(', r'np.\1(', code)
        if new_code != code:
            code = new_code
            fixes.append('numpy → np')
    
    # altair
    if 'import altair as alt' in file_content:
        new_code = re.sub(r'\baltair\.(\w+)\(', r'alt.\1(', code)
        if new_code != code:
            code = new_code
            fixes.append('altair → alt')
    
    return code, fixes




def v12_compile_test(fp: str) -> Tuple[bool, str]:
    try:
        with open(fp, "r", encoding="utf-8") as f:
            code = f.read()
        compile(code, fp, "exec")
        return True, "✅ Compiles"
    except SyntaxError as e:
        return False, f"Line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, str(e)[:100]


def v12_restore_file(fp: str, bpath) -> bool:
    try:
        if bpath and os.path.exists(bpath):
            shutil.copy2(bpath, fp)
            return True
    except Exception:
        pass
    return False


# ═══════════════════════════════════════════════════════════
# 🛡️ SAFETY LAYER
# ═══════════════════════════════════════════════════════════

def v12_is_protected(filepath):
    if not filepath:
        return True, "❌ Empty path"
    fp = filepath.replace("\\", "/").strip()
    bn = os.path.basename(fp)
    if bn in PROTECTED_FILES:
        return True, f"🛡️ '{bn}' PROTECTED"
    ext = os.path.splitext(bn)[1].lower()
    if ext in PROTECTED_EXTENSIONS:
        return True, f"🛡️ '{ext}' PROTECTED"
    for part in fp.split("/"):
        if part in PROTECTED_DIRS:
            return True, f"🛡️ '{part}/' PROTECTED"
    if "/" in fp:
        top = fp.split("/")[0]
        if top not in ALLOWED_DIRS and not top.startswith("."):
            return True, f"🛡️ '{top}/' protected"
    return False, "✅ Safe"


def v12_backup_dir():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    bdir = os.path.join(V12_BACKUP_ROOT, ts)
    os.makedirs(bdir, exist_ok=True)
    return bdir


def v12_backup_file(fp, bdir):
    try:
        if not os.path.exists(fp):
            return None
        rel = fp.replace("\\", "/").lstrip("./")
        dst = os.path.join(bdir, rel)
        os.makedirs(os.path.dirname(dst) or bdir, exist_ok=True)
        shutil.copy2(fp, dst)
        return dst
    except Exception:
        return None


def v12_validate_syntax(code):
    try:
        ast.parse(code)
        return True, "✅"
    except SyntaxError as e:
        return False, f"Line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, str(e)


def v12_validate_imports(code):
    stdlib = {"os","sys","io","re","json","ast","time","shutil","datetime",
              "pathlib","typing","hashlib","uuid","sqlite3","subprocess",
              "threading","contextlib","zipfile","difflib","collections",
              "functools","itertools","math","random","string","csv","base64",
              "asyncio","calendar","statistics","warnings"}
    local = {"database","auth","styles","themes","object_store","id_card",
             "qr_utils","profile_token","printer_utils","ai_assistant","ai_coder_v12"}
    missing = []
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for a in node.names:
                    top = a.name.split(".")[0]
                    if top not in stdlib and top not in local and top not in missing:
                        missing.append(top)
            elif isinstance(node, ast.ImportFrom) and node.module:
                top = node.module.split(".")[0]
                if top not in stdlib and top not in local and top not in missing:
                    missing.append(top)
    except Exception:
        pass
    return (len(missing) == 0), missing


def v12_validate_safety(code):
    warnings = []
    checks = [
        (r'\bshutil\.rmtree\s*\(', "🚨 rmtree"),
        (r'\bDROP\s+TABLE\b', "🚨 DROP TABLE"),
        (r'\bTRUNCATE\b', "🚨 TRUNCATE"),
        (r'\bDELETE\s+FROM\s+\w+\s*(?:;|$)', "🚨 DELETE without WHERE"),
        (r'\beval\s*\(', "⚠️ eval()"),
        (r'\bexec\s*\(', "⚠️ exec()"),
        (r'\bos\.remove\s*\([\'"].*\.py[\'"]', "⚠️ os.remove on .py"),
    ]
    for pat, msg in checks:
        if re.search(pat, code, re.IGNORECASE):
            warnings.append(msg)
    return (len(warnings) == 0), warnings


# ═══════════════════════════════════════════════════════════
# 🧠 PROJECT INDEXER (Enhanced for Multi-File)
# ═══════════════════════════════════════════════════════════

def v12_scan_project():
    index = {
        "scanned_at": datetime.now().isoformat(),
        "files": {},
        "stats": {"total_files": 0, "total_lines": 0, "pages": 0},
        "cross_refs": {},
        "page_registry": {},
    }
    for root, dirs, filenames in os.walk("."):
        dirs[:] = [d for d in dirs if d not in V12_SKIP_DIRS]
        for f in filenames:
            if not f.endswith(".py") or ".backup" in f:
                continue
            fp = os.path.join(root, f).replace("./", "").replace("\\", "/")
            if v12_is_protected(fp)[0]:
                continue
            try:
                with open(fp, "r", encoding="utf-8") as fh:
                    content = fh.read()
                lines = len(content.splitlines())
                funcs = re.findall(r'^def\s+(\w+)', content, re.MULTILINE)
                classes = re.findall(r'^class\s+(\w+)', content, re.MULTILINE)
                imports = list(set(re.findall(r'^(?:from|import)\s+([\w.]+)', content, re.MULTILINE)))
                render_calls = re.findall(r'(\w+)\.render\(', content)
                
                import_style = {}
                if 'from datetime import datetime' in content:
                    import_style['datetime'] = 'direct'
                elif 'import datetime' in content:
                    import_style['datetime'] = 'module'
                if 'import streamlit as st' in content:
                    import_style['streamlit'] = 'st'
                if 'import pandas as pd' in content:
                    import_style['pandas'] = 'pd'
                
                # Detect DB functions used
                db_calls = re.findall(r'db\.(\w+)\(', content)
                
                # Detect pages with any entry function
                has_render = False
                for marker in ['def render(', 'def show(', 'def main(', 'def display(']:
                    if marker in content:
                        has_render = True
                        break
                
                index["files"][fp] = {
                    "lines": lines,
                    "functions": funcs,
                    "classes": classes,
                    "imports": imports,
                    "import_style": import_style,
                    "db_calls": list(set(db_calls)),
                    "has_render": has_render,
                    "size_kb": round(os.path.getsize(fp) / 1024, 1),
                }
                
                # Cross-references (imports from local)
                for imp in imports:
                    if imp in ["database", "auth", "styles", "themes", "object_store",
                              "id_card", "qr_utils", "profile_token", "printer_utils"]:
                        index["cross_refs"].setdefault(imp, []).append(fp)
                
                # Page registry — track all gym_pages files with entry functions
                if has_render and ("/gym_pages/" in fp or fp.startswith("gym_pages/")):
                    page_name = os.path.basename(fp).replace(".py", "")
                    index["page_registry"][page_name] = fp
                
                index["stats"]["total_files"] += 1
                index["stats"]["total_lines"] += lines
                if "/gym_pages/" in fp or fp.startswith("gym_pages/"):
                    index["stats"]["pages"] += 1
            except Exception:
                pass
    try:
        with open(V12_INDEX_FILE, "w") as f:
            json.dump(index, f, indent=2)
    except Exception:
        pass
    return index


def v12_load_index():
    if os.path.exists(V12_INDEX_FILE):
        try:
            with open(V12_INDEX_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return v12_scan_project()


def v12_index_summary():
    idx = v12_load_index()
    s = idx.get("stats", {})
    pages = len(idx.get("page_registry", {}))
    return f"📊 {s.get('total_files', 0)} files · {s.get('total_lines', 0)} lines · {pages} pages"


def v12_get_all_pages():
    idx = v12_load_index()
    return idx.get("page_registry", {})


# ═══════════════════════════════════════════════════════════
# 🎯 SMART FILE FINDER (Enhanced)
# ═══════════════════════════════════════════════════════════

def v12_find_relevant_files(query, max_files=3):
    idx = v12_load_index()
    idx_files = idx.get("files", {})
    
    # Skip V12's own files (self-reference)
    idx_files = {k: v for k, v in idx_files.items()
                 if "ai_coder" not in k and "ai_assistant" not in k}
    
    direct = []
    for m in re.finditer(r'([\w/]+\.py)', query):
        cand = m.group(1).replace("\\", "/").lstrip("./")
        if cand in idx_files:
            direct.append(cand)
    for m in re.finditer(r'\b(\w{3,})\b', query.lower()):
        word = m.group(1)
        for fp in idx_files:
            basename = os.path.basename(fp).replace(".py", "")
            if basename == word and fp not in direct:
                direct.append(fp)
    
    if direct:
        return direct[:max_files]
    
    query_words = [w.lower() for w in re.findall(r'\w+', query) if len(w) > 2]
    scored = []
    for fp, info in idx_files.items():
        # Skip V12's own files
        if 'ai_coder' in fp or 'ai_assistant' in fp:
            continue
        score = 0
        fname = os.path.basename(fp).lower().replace(".py", "")
        for w in query_words:
            if w == fname:
                score += 100
            elif w in fname:
                score += 10
        for fn in info.get("functions", []) + info.get("classes", []):
            for w in query_words:
                if w in fn.lower():
                    score += 3
        if score > 0:
            scored.append((score, fp))
    scored.sort(reverse=True)
    return [fp for _, fp in scored[:max_files]]


def v12_load_db_api():
    for path in ["database_api.py", "../database_api.py", "gym-app/database_api.py"]:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception:
                pass
    return ""


def v12_build_context(query, max_chars_per_file=1500):
    """Enhanced context for bade kaam"""
    parts = ["=== DATABASE API ==="]
    db_api = v12_load_db_api()
    if db_api:
        parts.append(db_api[:5000])
    
    # Files mentioned explicitly
    forced = []
    for m in re.finditer(r'([\w/]+\.py)', query):
        cand = m.group(1).replace("\\", "/").lstrip("./")
        if os.path.exists(cand) and not v12_is_protected(cand)[0]:
            forced.append(cand)
    
    # Smart matching
    relevant = forced if forced else v12_find_relevant_files(query, max_files=3)
    
    parts.append("\n=== RELEVANT FILES ===")
    included = []
    total = len(parts[0]) + len(parts[1])
    
    for fp in relevant:
        if total > V12_MAX_CHARS:
            break
        try:
            with open(fp, "r", encoding="utf-8") as f:
                content = f.read()
            
            # For "add at end" style — show END
            if any(w in query.lower() for w in ["end", "add", "last", "ke baad", "niche", "append"]):
                snippet = content[-max_chars_per_file:] if len(content) > max_chars_per_file else content
                header = f"\n--- {fp} (END) ---"
            # For "imports" — show TOP
            elif any(w in query.lower() for w in ["import", "top", "upar", "start"]):
                snippet = content[:max_chars_per_file]
                header = f"\n--- {fp} (START) ---"
            # Otherwise show BOTH
            else:
                if len(content) > max_chars_per_file * 2:
                    snippet = content[:max_chars_per_file] + "\n\n...[MIDDLE TRUNCATED]...\n\n" + content[-max_chars_per_file:]
                else:
                    snippet = content
                header = f"\n--- {fp} ---"
            
            hint = ""
            if 'from datetime import datetime' in content:
                hint = "\n# ⚠️ IMPORT: datetime.now()"
            if 'import streamlit as st' in content:
                hint += "\n# ⚠️ IMPORT: st.metric()"
            if 'import pandas as pd' in content:
                hint += "\n# ⚠️ IMPORT: pd.DataFrame()"
            
            parts.append(header + hint + "\n" + snippet)
            included.append(fp)
            total += len(snippet) + len(header)
        except Exception:
            pass
    
    # Add page registry for context
    idx = v12_load_index()
    pages = idx.get("page_registry", {})
    if pages:
        parts.append("\n=== EXISTING PAGES ===")
        for pname, ppath in list(pages.items())[:20]:
            parts.append(f"  {pname} → {ppath}")
    
    return "\n".join(parts), included


# ═══════════════════════════════════════════════════════════
# 🎯 AI CALL
# ═══════════════════════════════════════════════════════════

V12_SYS_PROMPT = """You are GymPro AI Coder V12 ULTIMATE 2.0 — BADE KAAM MODE.

You handle LARGE tasks: new pages, multi-file changes, complex features.

⚠️ IMPORT RULES (CRITICAL):
- If file has "from datetime import datetime" → use datetime.now()
- If file has "import streamlit as st" → use st.metric()
- If file has "import pandas as pd" → use pd.DataFrame()
- NEVER mix import styles. Match the file exactly.

⚠️ DATABASE FUNCTIONS (use ONLY from DATABASE API):
- get_member_count() → total (NO args)
- get_active_member_count() → active (NO args)
- get_active_members(gym_id) → needs gym_id!
- get_members(gym_id=None) → list
- get_fee_records(gym_id=None, ...) → list
- get_stats(gym_id=None) → dict
- Never invent function names

⚠️ SEARCH TEXT:
- Must exist EXACTLY in file (including indentation)
- Include 2-3 lines for unique match
- Copy from the ACTUAL file content shown

⚠️ FOR BADE KAAM (new pages, multi-file):
1. Create new file with action="create" and full content
2. Modify app.py to add sidebar entry (search for existing pattern)
3. Modify app.py to add router entry (search for existing pattern)
4. Modify auth.py to add roles (search for existing pattern)
5. All in ONE response with multiple changes

⚠️ FOR CHHOTE CHANGES:
- Prefer SMALL changes. Never rewrite whole files.
- Only change what user asked.

CONTEXT: Gym Management app (Streamlit + SQLAlchemy + SQLite/Postgres).
Pages: gym_pages/ folder.
Database: database.py (PROTECTED — never touch).
Main: app.py (sidebar + router).

EXISTING PAGES — always use THIS pattern when making new pages:

app.py SIDEBAR pattern:
    "Page Name": ("🎯", "Page Name"),

app.py ROUTER pattern:
    elif page == "Page Name":
        from gym_pages import page_name
        page_name.render(gid, role, username)

auth.py ROLE_PAGES pattern:
    "admin": ["Dashboard", ..., "Page Name"],

gym_pages/new_page.py structure:
    import streamlit as st
    from datetime import datetime
    from database import (...)  # only needed functions
    
    def render(gym_id=None, role=None, username=""):
        st.title("Page Title")
        # your code here

RULES:
1. 🛡️ database.py, auth.py, *.db, *.env — NEVER touch.
2. Output valid JSON only. No markdown.
3. Never use: eval(), exec(), shutil.rmtree, DROP/DELETE SQL.
4. Roman Urdu for user messages.
5. Multi-file changes ALLOWED and ENCOURAGED for bade kaam.

RESPONSE FORMAT:
{
  "explanation": "Roman Urdu mein short",
  "plan": ["step 1", "step 2", "step 3"],
  "changes": [
    {"file": "path.py", "action": "create", "new_content": "..."},
    {"file": "app.py", "action": "modify", "search_for": "...", "replace_with": "..."}
  ],
  "verify_notes": ["kya check karna hai"]
}"""


def v12_call_ai(prompt, system=None, max_tokens=V12_MAX_TOKENS):
    key = os.environ.get("GROQ_API_KEY", "").strip()
    if not key:
        return '{"error": "GROQ_API_KEY missing"}'
    if system is None:
        system = V12_SYS_PROMPT
    
    models = ["openai/gpt-oss-120b", "openai/gpt-oss-20b"]
    last_error = "unknown"
    
    for model in models:
        for attempt in range(2):
            try:
                r = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {key}",
                             "Content-Type": "application/json"},
                    json={"model": model,
                          "messages": [{"role": "system", "content": system},
                                       {"role": "user", "content": prompt}],
                          "temperature": 0.2,
                          "max_tokens": max_tokens},
                    timeout=90)
                
                if r.status_code == 200:
                    data = r.json()
                    if "choices" not in data or not data["choices"]:
                        last_error = f"{model}: no choices"
                        continue
                    msg = data["choices"][0].get("message", {})
                    out = (msg.get("content") or "").strip()
                    if not out:
                        out = (msg.get("reasoning") or "").strip()
                    if out:
                        return out
                    last_error = f"{model}: empty"
                    continue
                elif r.status_code == 429:
                    last_error = f"{model}: rate limited"
                    time.sleep(8)
                else:
                    last_error = f"{model}: HTTP {r.status_code}"
                    break
            except requests.exceptions.Timeout:
                last_error = f"{model}: timeout"
                continue
            except Exception as e:
                last_error = f"{model}: {type(e).__name__}"
                continue
    
    return '{"error": "' + last_error.replace('"', "'") + '"}'




def v12_call_cohere(prompt, system=None, max_tokens=V12_MAX_TOKENS):
    """Call Cohere API (free tier — best for bade kaam)"""
    key = os.environ.get("COHERE_API_KEY", "").strip()
    if not key:
        return None  # Signal: fallback to Groq
    
    if system is None:
        system = V12_SYS_PROMPT
    
    models = [COHERE_MODEL, COHERE_MODEL_ALT]
    
    for model in models:
        try:
            r = requests.post(
                COHERE_API_URL,
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.2,
                    "max_tokens": max_tokens,
                },
                timeout=90,
            )
            
            if r.status_code == 200:
                data = r.json()
                # Cohere v2 response format
                if "message" in data and "content" in data["message"]:
                    for block in data["message"]["content"]:
                        if block.get("type") == "text":
                            text = block.get("text", "").strip()
                            if text:
                                return text
                # Fallback for older format
                if "text" in data:
                    return data["text"].strip()
            elif r.status_code == 429:
                time.sleep(5)
                continue
            elif r.status_code == 401:
                return '{"error": "COHERE_API_KEY invalid"}'
        except Exception:
            continue
    
    return None  # All Cohere attempts failed


def v12_call_ai_smart(prompt, system=None, max_tokens=V12_MAX_TOKENS, prefer="cohere"):
    """Smart AI call — Cohere first, Groq fallback"""
    # Try Cohere first (better for bade kaam)
    if prefer == "cohere":
        cohere_result = v12_call_cohere(prompt, system=system, max_tokens=max_tokens)
        if cohere_result and '"error"' not in cohere_result[:50]:
            return cohere_result
        # Fallback to Groq
        return v12_call_ai(prompt, system=system, max_tokens=max_tokens)
    else:
        # Groq first
        groq_result = v12_call_ai(prompt, system=system, max_tokens=max_tokens)
        if groq_result and '"error"' not in groq_result[:50]:
            return groq_result
        # Fallback to Cohere
        cohere_result = v12_call_cohere(prompt, system=system, max_tokens=max_tokens)
        return cohere_result or groq_result


def v12_parse_json(resp):
    if not isinstance(resp, str):
        return {"error": "not string"}
    c = resp.strip()
    if "```json" in c:
        c = c.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in c:
        parts = c.split("```")
        if len(parts) >= 3:
            c = parts[1].strip()
            if c.startswith("json"):
                c = c[4:].strip()
    try:
        return json.loads(c)
    except Exception:
        pass
    try:
        s, e = c.find("{"), c.rfind("}")
        if s != -1 and e > s:
            return json.loads(c[s:e+1])
    except Exception:
        pass
    return {"error": "JSON parse failed", "raw": resp[:500]}


# ═══════════════════════════════════════════════════════════
# 💾 APPLY CHANGES
# ═══════════════════════════════════════════════════════════

def v12_apply_create(fp, content):
    p, r = v12_is_protected(fp)
    if p:
        return False, r, []
    
    content, fixes = v12_fix_imports(content, content)
    
    ok, msg = v12_validate_syntax(content)
    if not ok:
        return False, f"Syntax: {msg}", fixes
    
    safe, warns = v12_validate_safety(content)
    if not safe and any("🚨" in w for w in warns):
        return False, f"🚨 {', '.join(warns)}", fixes
    
    try:
        os.makedirs(os.path.dirname(fp) or ".", exist_ok=True)
        with open(fp, "w", encoding="utf-8") as f:
            f.write(content)
        ok_c, msg_c = v12_compile_test(fp)
        if not ok_c:
            return False, f"Compile fail: {msg_c}", fixes
        return True, f"✅ Created: {fp}", fixes
    except Exception as e:
        return False, f"❌ {e}", fixes


def v12_apply_modify(fp, search, replace):
    p, r = v12_is_protected(fp)
    if p:
        return False, r, None, []
    if not os.path.exists(fp):
        return False, f"❌ {fp} not found", None, []
    if not search or search == replace:
        return False, "❌ Empty/same", None, []
    
    try:
        with open(fp, "r", encoding="utf-8") as f:
            old = f.read()
    except Exception as e:
        return False, f"❌ Read: {e}", None, []
    
    replace, fixes = v12_fix_imports(replace, old)
    
    actual = None
    if search in old:
        actual = search
    else:
        s_trim = search.strip()
        if s_trim and s_trim in old:
            actual = s_trim
        else:
            search_lines = [l.strip() for l in search.split("\n") if l.strip()]
            old_lines = old.split("\n")
            if search_lines:
                first = search_lines[0]
                for i, ol in enumerate(old_lines):
                    if ol.strip() == first:
                        match = True
                        for j, sl in enumerate(search_lines):
                            if i + j >= len(old_lines) or old_lines[i + j].strip() != sl:
                                match = False
                                break
                        if match:
                            actual = "\n".join(old_lines[i:i + len(search_lines)])
                            break
    
    if not actual:
        return False, f"❌ Search text not found in {fp}", None, fixes
    
    bdir = v12_backup_dir()
    bpath = v12_backup_file(fp, bdir)
    
    new = old.replace(actual, replace, 1)
    ok, msg = v12_validate_syntax(new)
    if not ok:
        return False, f"❌ Syntax: {msg}", bpath, fixes
    
    safe, warns = v12_validate_safety(new)
    if not safe and any("🚨" in w for w in warns):
        return False, f"🚨 {', '.join(warns)}", bpath, fixes
    
    try:
        with open(fp, "w", encoding="utf-8") as f:
            f.write(new)
    except Exception as e:
        v12_restore_file(fp, bpath)
        return False, f"❌ Write: {e}", bpath, fixes
    
    ok_c, msg_c = v12_compile_test(fp)
    if not ok_c:
        v12_restore_file(fp, bpath)
        return False, f"❌ Auto-rollback: {msg_c}", bpath, fixes
    
    # Verify actual change
    try:
        with open(fp, "r", encoding="utf-8") as f:
            _written = f.read()
        if _written.strip() == old.strip():
            return False, f"⚠️ No actual change in {fp}", bpath, fixes
        _diff = list(difflib.unified_diff(old.split("\n"), _written.split("\n"), lineterm=""))
        _added = sum(1 for l in _diff if l.startswith("+") and not l.startswith("+++"))
        _removed = sum(1 for l in _diff if l.startswith("-") and not l.startswith("---"))
        _cstr = f" (+{_added}/-{_removed} lines)"
    except Exception:
        _cstr = ""
    return True, f"✅ Modified: {fp}{_cstr}", bpath, fixes


# ═══════════════════════════════════════════════════════════
# 💾 COMMITS & MEMORY
# ═══════════════════════════════════════════════════════════

def v12_save_commit(desc, changes, bdir):
    try:
        commits = []
        if os.path.exists(V12_COMMITS_FILE):
            with open(V12_COMMITS_FILE) as f:
                commits = json.load(f)
        commits.append({
            "id": len(commits) + 1,
            "time": datetime.now().isoformat(),
            "description": desc,
            "backup_dir": bdir,
            "changes": [{"file": c.get("file"), "action": c.get("action", "modify")} for c in changes],
        })
        with open(V12_COMMITS_FILE, "w") as f:
            json.dump(commits, f, indent=2)
    except Exception:
        pass


def v12_get_commits():
    if os.path.exists(V12_COMMITS_FILE):
        try:
            with open(V12_COMMITS_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return []


def v12_time_travel(commit_id):
    commits = v12_get_commits()
    c = next((x for x in commits if x["id"] == commit_id), None)
    if not c:
        return False, "❌ Commit not found"
    bdir = c.get("backup_dir", "")
    if not os.path.exists(bdir):
        return False, "❌ Backup not found"
    restored = []
    for ch in c.get("changes", []):
        fp = ch.get("file", "")
        if v12_is_protected(fp)[0]:
            continue
        bf = os.path.join(bdir, fp.replace("\\", "/").lstrip("./"))
        if os.path.exists(bf):
            try:
                shutil.copy2(bf, fp)
                restored.append(fp)
            except Exception:
                pass
    return True, f"✅ Restored {len(restored)} files"


def v12_save_memory(command, result):
    try:
        memory = []
        if os.path.exists(V12_MEMORY_FILE):
            with open(V12_MEMORY_FILE) as f:
                memory = json.load(f)
        memory.append({
            "time": datetime.now().isoformat(),
            "command": command[:200],
            "success": result.get("success"),
            "files": [c.get("file") for c in result.get("changes_applied", [])],
        })
        memory = memory[-50:]
        with open(V12_MEMORY_FILE, "w") as f:
            json.dump(memory, f, indent=2)
    except Exception:
        pass


def v12_get_memory(limit=20):
    if os.path.exists(V12_MEMORY_FILE):
        try:
            with open(V12_MEMORY_FILE) as f:
                return json.load(f)[-limit:]
        except Exception:
            pass
    return []


def v12_quick_templates():
    return {
        # Chhote kaam
        "Search Bar": "gym_pages/{file}.py mein search bar add karo",
        "Filter": "gym_pages/{file}.py mein filter dropdown add karo",
        "Chart": "gym_pages/{file}.py mein chart add karo",
        "Export CSV": "gym_pages/{file}.py mein CSV export add karo",
        # Bade kaam
        "New Page": "Naya page banао: gym_pages/{name}.py — admin aur staff dekh sakein",
        "New Report Page": "Naya report page banao: gym_pages/{name}.py — monthly data ke saath",
        "New Dashboard": "Naya dashboard banao: gym_pages/{name}.py — charts ke saath",
        "Full Feature": "Naya feature banao: page + database queries + charts + export",
    }


# ═══════════════════════════════════════════════════════════
# 🚀 MAIN EXECUTE
# ═══════════════════════════════════════════════════════════



def v12_detect_multi_page_command(command):
    """Detect 'sab pages' type commands and return list of matching files"""
    cmd_lower = command.lower()
    multi_indicators = ["sab page", "sab pages", "all pages", "har page",
                        "saare page", "saaray pages", "every page", "poora app"]
    is_multi = any(ind in cmd_lower for ind in multi_indicators)
    
    if not is_multi:
        return None
    
    # Find matching pages
    idx = v12_load_index()
    pages = idx.get("page_registry", {})
    
    # Filter by keyword
    matching = []
    for name, path in pages.items():
        # Skip v12's own files
        if "ai_coder" in path or "ai_assistant" in path:
            continue
        matching.append({"name": name, "path": path})
    
    return matching




def v12_detect_mode(command):
    """Detect if user wants analysis or fix"""
    cmd_lower = command.lower()
    
    # Analysis keywords
    analysis_kw = ["dekho", "batao", "analyze", "kyun", "kyu", "samjhao",
                   "research", "check karo", "kya problem", "kya issue",
                   "suggest", "recommend", "advise", "explain", "review"]
    
    # Fix keywords  
    fix_kw = ["karo", "fix karo", "add karo", "change karo", "modify karo",
              "update karo", "banao", "thik karo", "theek karo", "sahi karo"]
    
    is_analysis = any(kw in cmd_lower for kw in analysis_kw)
    is_fix = any(kw in cmd_lower for kw in fix_kw)
    
    # If both, prefer analysis (safer)
    if is_analysis and not is_fix:
        return "analysis"
    if is_fix and not is_analysis:
        return "fix"
    if is_analysis and is_fix:
        return "analysis"  # Analysis first
    return "fix"  # Default




# ═══════════════════════════════════════════════════════════
# 🧠 CONVERSATION MEMORY
# ═══════════════════════════════════════════════════════════

CONVERSATION_FILE = ".ai_coder_v12_conversation.json"
MAX_CONVERSATION = 20


def v12_save_conversation(user_msg, ai_response, mode="fix", topic=None, success=None):
    """Save conversation turn"""
    try:
        conv = []
        if os.path.exists(CONVERSATION_FILE):
            with open(CONVERSATION_FILE) as f:
                conv = json.load(f)
        
        conv.append({
            "time": datetime.now().isoformat(),
            "user": user_msg[:500],
            "ai_explanation": (ai_response or "")[:500],
            "mode": mode,
            "topic": topic,
            "success": success,
        })
        
        conv = conv[-MAX_CONVERSATION:]
        
        with open(CONVERSATION_FILE, "w") as f:
            json.dump(conv, f, indent=2)
    except Exception:
        pass


def v12_get_conversation(limit=5):
    """Get recent conversation"""
    if os.path.exists(CONVERSATION_FILE):
        try:
            with open(CONVERSATION_FILE) as f:
                conv = json.load(f)
            return conv[-limit:]
        except Exception:
            pass
    return []


def v12_detect_topic(command):
    """Detect topic from command — improved"""
    cmd_lower = command.lower()
    
    # Common topics with aliases
    topic_map = {
        "whatsapp": ["whatsapp", "whats app", "whatsap"],
        "dashboard": ["dashboard", "dash board", "design dashboard", "admin dashboard"],
        "members": ["member", "members", "member page"],
        "attendance": ["attendance", "attendence", "hazri"],
        "fee": ["fee", "fees", "collection", "fee collection"],
        "expenses": ["expense", "expenses", "kharcha"],
        "inventory": ["inventory", "stock", "maal"],
        "reports": ["report", "reports", "reporting"],
        "settings": ["setting", "settings"],
        "gym_setup": ["gym setup", "setup"],
        "progress": ["progress", "tracker"],
        "membership": ["membership", "card", "id card"],
        "complaints": ["complaint", "shikayat"],
        "message": ["message", "messages"],
        "auditor": ["auditor", "audit"],
        "staff_targets": ["staff target", "target", "staff target"],
        "user_management": ["user", "user management"],
        "public_profile": ["public profile", "public"],
        "bulk_id_cards": ["bulk id", "id card"],
        "body_ai": ["body ai", "body"],
    }
    
    for topic, aliases in topic_map.items():
        for alias in aliases:
            if alias in cmd_lower:
                return topic
    
    # Check page names from index
    try:
        idx = v12_load_index()
        pages = idx.get("page_registry", {})
        for page_name in pages.keys():
            if page_name.lower() in cmd_lower:
                return page_name
    except Exception:
        pass
    
    return None




def v12_conversation_context(limit=3):
    """Build conversation context for AI"""
    conv = v12_get_conversation(limit)
    if not conv:
        return ""
    
    lines = ["\n=== RECENT CONVERSATION ==="]
    for turn in conv:
        lines.append(f"User: {turn.get('user', '')[:200]}")
        if turn.get('ai_explanation'):
            lines.append(f"AI ({turn.get('mode', '?')}): {turn.get('ai_explanation', '')[:200]}")
        if turn.get('topic'):
            lines.append(f"  [Topic: {turn['topic']}]")
    
    return "\n".join(lines)

def v12_execute(command, preview_only=False):
    result = {
        "success": False, "message": "", "plan": [],
        "changes_applied": [], "changes_preview": [],
        "verification": {}, "backup_dir": None, "included_files": [],
        "explanation": "", "import_fixes": [],
    }
    if not command.strip():
        result["message"] = "❌ Empty command"
        return result
    
    # Detect mode
    mode = v12_detect_mode(command)
    result["mode"] = mode
    
    # Detect multi-page commands
    multi_pages = v12_detect_multi_page_command(command)
    if multi_pages and len(multi_pages) > 3:
        result["message"] = f"⚠️ Ye command {len(multi_pages)} pages ko affect karti hai. V12 ek waqt mein 3-4 files hi handle kar sakta hai. Chhota command do (ek page ka naam likho)."
        result["multi_page_detected"] = [p["path"] for p in multi_pages[:10]]
        return result
    
    ctx, included = v12_build_context(command)
    result["included_files"] = included
    result["context_size"] = len(ctx) if ctx else 0
    
    prompt = f"""USER COMMAND: {command}

{ctx}

IMPORTANT:
- Agar bara kaam hai (naya page) — full content create karo + app.py + auth.py modify karo
- Agar chhota kaam hai — sirf wahi change karo
- Search text FILE mein exactly jaisa hai waisa likho (indentation include)
- Import style match karo (file ke hints dekho)
- Database functions sirf DATABASE API se use karo
- Agar unsure ho toh changes khali rakho aur explanation do

Output JSON only:
{{"explanation":"short Roman Urdu","plan":["step1","step2"],"changes":[{{"file":"path","action":"create","new_content":"full code"}},{{"file":"app.py","action":"modify","search_for":"exact","replace_with":"new"}}],"verify_notes":[]}}"""

    # Try Cohere first (better for bade kaam), fallback to Groq
    ai_resp = v12_call_ai_smart(prompt, max_tokens=V12_MAX_TOKENS, prefer="cohere")
    parsed = v12_parse_json(ai_resp)
    
    if "error" in parsed:
        result["message"] = f"❌ AI error: {parsed.get('error')}"
        result["explanation"] = str(parsed.get("raw", ""))[:300]
        try:
            v12_save_memory(command, result)
            v12_save_conversation(command, result.get("explanation", ""), 
                                  result.get("mode", "fix"), 
                                  v12_detect_topic(command), False)
        except Exception:
            pass
        return result
    
    result["plan"] = parsed.get("plan", [])
    result["explanation"] = parsed.get("explanation", "")
    changes = parsed.get("changes", [])
    
    if not changes:
        result["message"] = "⚠️ AI ne koi change nahi diya."
        try:
            v12_save_memory(command, result)
            v12_save_conversation(command, result.get("explanation", ""), 
                                  result.get("mode", "fix"), 
                                  v12_detect_topic(command), False)
        except Exception:
            pass
        return result
    
    # Check file count
    if len(changes) > V12_MAX_FILES_PER_TASK:
        result["message"] = (f"⚠️ AI ne {len(changes)} changes diye (max {V12_MAX_FILES_PER_TASK}). "
                            f"Command chhota karo — ek waqt mein 3-4 files best hain.")
        result["change_count"] = len(changes)
        result["max_allowed"] = V12_MAX_FILES_PER_TASK
        result["changes_preview"] = changes[:5]  # Show first 5
        return result
    
    safe_changes, blocked = [], []
    for ch in changes:
        fp = ch.get("file", "")
        if v12_is_protected(fp)[0]:
            blocked.append(fp)
        else:
            safe_changes.append(ch)
    
    if blocked and not safe_changes:
        result["message"] = "🛡️ Protected: " + ", ".join(blocked)
        try:
            v12_save_memory(command, result)
            v12_save_conversation(command, result.get("explanation", ""), 
                                  result.get("mode", "fix"), 
                                  v12_detect_topic(command), False)
        except Exception:
            pass
        return result
    
    if preview_only:
        result["success"] = True
        result["message"] = f"📸 Preview: {len(safe_changes)} changes ready"
        result["changes_preview"] = safe_changes
        result["blocked"] = blocked
        return result
    
    bdir = v12_backup_dir()
    applied, failed = [], []
    all_fixes = []
    
    for ch in safe_changes:
        fp = ch.get("file", "")
        act = ch.get("action", "modify")
        if os.path.exists(fp):
            v12_backup_file(fp, bdir)
        
        if act == "create":
            ok, msg, fixes = v12_apply_create(fp, ch.get("new_content", ""))
            all_fixes.extend(fixes)
        elif act == "modify":
            ok, msg, _, fixes = v12_apply_modify(fp, ch.get("search_for", ""), ch.get("replace_with", ""))
            all_fixes.extend(fixes)
        else:
            ok, msg = False, f"Unknown: {act}"
        
        if ok:
            applied.append({"file": fp, "action": act, "message": msg})
        else:
            failed.append({"file": fp, "action": act, "message": msg})
    
    result["backup_dir"] = bdir
    result["changes_applied"] = applied
    result["import_fixes"] = list(set(all_fixes))
    
    for ch in applied:
        fp = ch["file"]
        if os.path.exists(fp):
            with open(fp) as f:
                c = f.read()
            ok_s, ms = v12_validate_syntax(c)
            ok_i, mi = v12_validate_imports(c)
            ok_c, mc = v12_compile_test(fp)
            result["verification"][fp] = {
                "syntax": ok_s, "syntax_msg": ms,
                "imports_ok": ok_i, "missing": mi,
                "compiles": ok_c, "compile_msg": mc,
            }
    
    if applied:
        v12_save_commit(command[:100], safe_changes, bdir)
        v12_scan_project()
    
    parts = []
    if applied:
        parts.append(f"✅ {len(applied)} applied")
    if failed:
        parts.append(f"❌ {len(failed)} failed")
    if blocked:
        parts.append(f"🛡️ {len(blocked)} blocked")
    if all_fixes:
        parts.append(f"🔧 {len(set(all_fixes))} auto-fixes")
    result["message"] = " | ".join(parts) if parts else "No changes"
    result["success"] = len(failed) == 0 and len(applied) > 0
    
    try:
        v12_save_memory(command, result)
    except Exception:
        pass
    
    # Save conversation
    try:
        v12_save_conversation(
            user_msg=command,
            ai_response=result.get("explanation", ""),
            mode=result.get("mode", "fix"),
            topic=v12_detect_topic(command),
            success=result.get("success"),
        )
    except Exception:
        pass
    
    return result


def v12_auto_fix(error_text, filepath=None):
    ctx = ""
    if filepath and os.path.exists(filepath):
        try:
            with open(filepath) as f:
                ctx = f"\n\nFILE: {filepath}\nCONTENT:\n{f.read()[:12000]}"
        except Exception:
            pass
    prompt = f"""AUTO-FIX REQUEST

ERROR:
{error_text}
{ctx}

Diagnose karo aur fix do. Output JSON per system prompt."""
    resp = v12_call_ai_smart(prompt, max_tokens=8000, prefer="cohere")
    parsed = v12_parse_json(resp)
    if "error" in parsed:
        return {"success": False, "message": parsed["error"]}
    
    changes = parsed.get("changes", [])
    bdir = v12_backup_dir()
    applied, failed = [], []
    all_fixes = []
    
    for ch in changes:
        fp = ch.get("file", "")
        if v12_is_protected(fp)[0]:
            failed.append({"file": fp, "message": "🛡️ Protected"})
            continue
        if ch.get("action") == "modify":
            ok, msg, _, fixes = v12_apply_modify(fp, ch.get("search_for", ""), ch.get("replace_with", ""))
            all_fixes.extend(fixes)
        elif ch.get("action") == "create":
            ok, msg, fixes = v12_apply_create(fp, ch.get("new_content", ""))
            all_fixes.extend(fixes)
        else:
            ok, msg = False, "Unknown"
        if ok:
            applied.append({"file": fp, "message": msg})
        else:
            failed.append({"file": fp, "message": msg})
    
    if applied:
        v12_save_commit(f"Auto-fix: {error_text[:60]}", changes, bdir)
    return {
        "success": len(failed) == 0 and len(applied) > 0,
        "diagnosis": parsed.get("diagnosis", parsed.get("explanation", "")),
        "applied": applied, "failed": failed,
        "backup_dir": bdir, "fixes": list(set(all_fixes)),
    }


def v12_cleanup_backups(days=7):
    deleted = 0
    if not os.path.exists(V12_BACKUP_ROOT):
        return 0, "No backups"
    cutoff = datetime.now() - timedelta(days=days)
    for d in os.listdir(V12_BACKUP_ROOT):
        path = os.path.join(V12_BACKUP_ROOT, d)
        if os.path.isdir(path):
            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(path))
                if mtime < cutoff:
                    shutil.rmtree(path)
                    deleted += 1
            except Exception:
                pass
    return deleted, f"✅ Deleted {deleted} old backups"


def v12_self_test():
    r = {}
    r["protected_check"] = v12_is_protected("database.py")[0] and not v12_is_protected("gym_pages/bmi.py")[0]
    r["syntax_validate"] = v12_validate_syntax("x=1")[0] and not v12_validate_syntax("def x(")[0]
    r["import_validate"] = v12_validate_imports("import os")[0] and not v12_validate_imports("import zzz_xyz_999")[0]
    r["safety_check"] = v12_validate_safety("x=1")[0] and not v12_validate_safety("import shutil; shutil.rmtree('/')")[0]
    
    # import_fix
    try:
        test_code = "x = datetime.datetime.now()"
        test_file = "from datetime import datetime"
        fixed, _ = v12_fix_imports(test_code, test_file)
        r["import_fix"] = "datetime.datetime" not in fixed
    except Exception:
        r["import_fix"] = False
    
    # backup
    try:
        bdir = v12_backup_dir()
        r["backup_system"] = os.path.exists(bdir)
    except Exception:
        r["backup_system"] = False
    
    # project index
    try:
        idx = v12_load_index()
        r["project_index"] = idx.get("stats", {}).get("total_files", 0) > 0
        # page_registry key should exist (may be empty)
        r["page_registry"] = "page_registry" in idx
    except Exception:
        r["project_index"] = False
        r["page_registry"] = False
    
    # compile test
    try:
        ct_ok, _ = v12_compile_test(__file__) if os.path.exists(__file__) else (True, "")
        r["compile_test"] = ct_ok
    except Exception:
        r["compile_test"] = False
    
    # groq
    try:
        resp = v12_call_ai("Reply OK", max_tokens=10)
        r["groq_connection"] = "error" not in resp.lower()
    except Exception:
        r["groq_connection"] = False
    
    # cohere
    try:
        cohere_key = os.environ.get("COHERE_API_KEY", "").strip()
        if cohere_key:
            resp = v12_call_cohere("Reply OK", max_tokens=10)
            r["cohere_connection"] = bool(resp) and "error" not in str(resp).lower()
        else:
            r["cohere_connection"] = False
    except Exception:
        r["cohere_connection"] = False
    
    return r
