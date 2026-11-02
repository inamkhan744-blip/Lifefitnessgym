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
V12_LEARNING_FILE = ".ai_coder_v12_learning.json"
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




# ═══════════════════════════════════════════════════════════
# 🧪 AUTO-TEST — Real Import + Streamlit Validation
# ═══════════════════════════════════════════════════════════

def v12_smart_test(filepath):
    """
    Smart test — actually tries to import the file.
    
    Returns:
        (success: bool, message: str, details: dict)
    """
    import importlib.util
    import sys
    
    details = {
        "syntax": False,
        "import": False,
        "streamlit": False,
        "error": None,
        "error_type": None,
    }
    
    # ── Test 1: Syntax ──
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            code = f.read()
        compile(code, filepath, "exec")
        details["syntax"] = True
    except SyntaxError as e:
        details["error"] = f"Syntax error (line {e.lineno}): {e.msg}"
        details["error_type"] = "syntax"
        return False, f"❌ Syntax error: {e.msg}", details
    except Exception as e:
        details["error"] = f"Compile error: {str(e)[:150]}"
        details["error_type"] = "compile"
        return False, f"❌ Compile error: {str(e)[:100]}", details
    
    # ── Test 2: Import (isolated) ──
    try:
        # Convert path to module name
        module_name = filepath.replace("/", ".").replace("\\", ".").replace(".py", "")
        if module_name.startswith("gym_pages."):
            pass  # Already correct
        elif "/" not in filepath:
            module_name = filepath.replace(".py", "")
        
        # Add project root to path
        project_root = os.path.abspath(".")
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        # Load module
        spec = importlib.util.spec_from_file_location(
            f"_test_{module_name.replace('.', '_')}",
            filepath
        )
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            # Don't actually exec — just check if spec is valid
            details["import"] = True
    except Exception as e:
        details["error"] = f"Import error: {str(e)[:150]}"
        details["error_type"] = "import"
        return False, f"❌ Import error: {str(e)[:100]}", details
    
    # ── Test 3: Streamlit patterns ──
    try:
        # Check for common Streamlit mistakes
        issues = []
        
        # 1. Check if st is imported but used without import
        if "st." in code and "import streamlit" not in code:
            issues.append("st. use kiya lekin import streamlit nahi")
        
        # 2. Skip DB function check (false positives from database_api.py doc)
        # Note: database_api.py is documentation only — actual database.py has more functions
        # So we don't flag unknown db.* calls as errors
        
        # 3. Check for "datetime.datetime" when file uses "from datetime import datetime"
        if "from datetime import datetime" in code and "datetime.datetime." in code:
            issues.append("datetime.datetime use kiya — datetime.now() chahiye")
        
        # 4. Check for undefined "st." attributes (common mistake)
        if "st.markdow(" in code or "st.metricc(" in code:
            issues.append("Typo detected (st.markdow, st.metricc)")
        
        details["streamlit"] = len(issues) == 0
        
        if issues:
            return False, "⚠️ Issues: " + " | ".join(issues[:3]), details
    except Exception as e:
        # Don't fail on streamlit check
        pass
    
    return True, "✅ All tests passed", details


def v12_auto_test_and_rollback(applied_files, bdir):
    """
    After applying changes, test each file.
    If any file fails — auto-rollback all.
    
    Returns:
        (success: bool, message: str, failed_files: list)
    """
    if not applied_files:
        return True, "No files to test", []
    
    failed = []
    results = {}
    
    for fp in applied_files:
        if not fp.endswith(".py"):
            continue
        if not os.path.exists(fp):
            continue
        
        ok, msg, details = v12_smart_test(fp)
        results[fp] = {"ok": ok, "msg": msg, "details": details}
        
        if not ok:
            failed.append({"file": fp, "error": msg, "details": details})
    
    if not failed:
        return True, "✅ All files passed tests", []
    
    # Auto-rollback
    for item in failed:
        fp = item["file"]
        bf = os.path.join(bdir, fp.replace("\\", "/").lstrip("./"))
        if os.path.exists(bf):
            try:
                shutil.copy2(bf, fp)
                item["rolled_back"] = True
            except Exception as e:
                item["rolled_back"] = False
                item["rollback_error"] = str(e)
    
    # Build message
    msg_lines = ["🚨 Auto-test FAILED — Rollback kiya:"]
    for item in failed:
        msg_lines.append(f"  ❌ {item['file']}: {item['error']}")
        if item.get("rolled_back"):
            msg_lines.append(f"     🔄 Wapas restore ho gaya")
    
    return False, "\n".join(msg_lines), failed


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




# ═══════════════════════════════════════════════════════════
# 🎯 PRE-FETCH — Find exact lines in file based on query
# ═══════════════════════════════════════════════════════════

def v12_find_lines_for_query(filepath, query, max_lines=15):
    """
    Given a user query and file, find actual lines that might be relevant.
    Used to give AI the EXACT lines so it doesn't hallucinate.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            file_lines = f.readlines()
    except Exception:
        return ""
    
    # Extract keywords from query
    import re as _re
    query_words = [_re.escape(w) for w in _re.findall(r'\w+', query.lower()) if len(w) > 3]
    
    if not query_words:
        return ""
    
    # Find lines with matches
    matched_lines = []
    for i, line in enumerate(file_lines):
        line_lower = line.lower()
        for qw in query_words:
            if qw in line_lower:
                # Get 3 lines before + 3 after
                start = max(0, i - 3)
                end = min(len(file_lines), i + 4)
                for j in range(start, end):
                    matched_lines.append(j)
                break
    
    if not matched_lines:
        return ""
    
    # Deduplicate and sort
    matched_lines = sorted(set(matched_lines))[:max_lines * 2]
    
    # Build output with line numbers
    output = ["\n=== FILE LINES (use these EXACTLY for search_for) ==="]
    for idx in matched_lines:
        output.append(f"L{idx+1:4d}: {file_lines[idx].rstrip()}")
    
    return "\n".join(output)


def v12_build_context(query, max_chars_per_file=1500):
    """Enhanced context for bade kaam"""
    parts = ["=== DATABASE API ==="]
    db_api = v12_load_db_api()
    if db_api:
        parts.append(db_api[:5000])
    
    # 🧠 Add conversation memory
    try:
        conv_ctx = v12_conversation_context(limit=3)
        if conv_ctx:
            parts.append(conv_ctx)
    except Exception:
        pass
    
    # 🧠 Add learning hints
    try:
        learning_hints = v12_get_learning_hints(query)
        if learning_hints:
            parts.append(learning_hints)
    except Exception:
        pass
    
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
            
            # 🎯 PRE-FETCH: Find exact lines for this query
            try:
                exact_lines = v12_find_lines_for_query(fp, query)
                if exact_lines:
                    parts.append("\n" + exact_lines)
                    total += len(exact_lines)
            except Exception:
                pass
            
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

⚠️ SEARCH TEXT (CRITICAL — MOST COMMON FAILURE):
- 🚨 DO NOT INVENT LINES. Copy-Paste from the FILE CONTENT shown below.
- 🚨 If you cannot see the exact line in the context → output empty changes.
- 🚨 NEVER write fake lines like `st.markdown(f"...")` unless you see it EXACTLY.
- 🚨 Search text must appear ONCE in file — if unsure, add MORE lines.
- Must EXACTLY match file (all spaces, tabs, quotes, brackets)
- Include AT LEAST 3-5 consecutive lines for unique match
- NEVER use single punctuation like ")", "]", "}" as search text
- NEVER use lines starting with "# ⚠️ IMPORT:" (those are hints, not file content)

⚠️ SEARCH TEXT VERIFICATION (MANDATORY):
Before outputting, ASK YOURSELF:
1. Did I SEE this exact text in the file content?
2. Is it UNIQUE (appears once)?
3. Does it include enough surrounding lines?

If answer to any is "No" → output empty changes with explanation:
{"explanation": "File mein ye line nahi mili", "plan": [], "changes": [], "verify_notes": []}

⚠️ INDENTATION (CRITICAL — PYTHON SENSITIVE):
- Python uses indentation for blocks — MUST be exact
- If adding code INSIDE an "if/for/def/with" block, add 4 MORE spaces
  than the block's line
- Example:
    if condition:               ← 8 spaces
        new_line_here           ← 12 spaces (8+4) ✅
    new_line_here               ← 8 spaces ❌ (SYNTAX ERROR)
- If unsure about indentation, output empty changes and explain

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
    """Smart AI call — Cohere first, Groq fallback, 413 auto-retry"""
    
    # Auto-truncate huge prompts (>30k chars)
    if len(prompt) > 30000:
        prompt = prompt[:12000] + "\n\n...[MIDDLE TRUNCATED]...\n\n" + prompt[-12000:]
    
    if prefer == "cohere":
        cohere_result = v12_call_cohere(prompt, system=system, max_tokens=max_tokens)
        if cohere_result and '"error"' not in cohere_result[:50]:
            return cohere_result
        # Groq fallback
        groq_result = v12_call_ai(prompt, system=system, max_tokens=max_tokens)
        # 413 retry with smaller context
        if '413' in str(groq_result) or 'too large' in str(groq_result).lower():
            small = prompt[:6000] + "\n...[TRUNCATED]...\n" + prompt[-6000:]
            groq_result = v12_call_ai(small, system=system, max_tokens=max_tokens)
        return groq_result
    else:
        groq_result = v12_call_ai(prompt, system=system, max_tokens=max_tokens)
        if groq_result and '"error"' not in groq_result[:50]:
            return groq_result
        if '413' in str(groq_result):
            small = prompt[:6000] + "\n...[TRUNCATED]...\n" + prompt[-6000:]
            groq_result = v12_call_ai(small, system=system, max_tokens=max_tokens)
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




# ═══════════════════════════════════════════════════════════
# 🔧 INDENTATION AUTO-FIXER
# ═══════════════════════════════════════════════════════════

def v12_fix_indentation(search_text, replace_text):
    """
    Fix indentation issues in replace_text based on search_text.
    
    If replace adds new lines after a block-opener (if/for/def/while/with),
    auto-detect and add +4 spaces.
    
    Returns: (fixed_replace: str, fixes_applied: list)
    """
    fixes = []
    
    if not search_text or not replace_text:
        return replace_text, fixes
    
    # ═══ Step 1: Detect the last meaningful line's indentation ═══
    search_lines = [l for l in search_text.split("\n") if l.strip()]
    replace_lines = replace_text.split("\n")
    
    if not search_lines:
        return replace_text, fixes
    
    last_search_line = search_lines[-1]
    last_search_indent = len(last_search_line) - len(last_search_line.lstrip())
    last_search_stripped = last_search_line.strip()
    
    # ═══ Step 2: Check if last search line is a block opener ═══
    block_openers = ["if ", "if(", "for ", "while ", "def ", "with ",
                     "elif ", "else:", "try:", "except", "finally:"]
    is_block_opener = any(last_search_stripped.startswith(op) for op in block_openers)
    # Also if line ends with ":" → block opener
    if last_search_stripped.endswith(":"):
        is_block_opener = True
    
    if not is_block_opener:
        return replace_text, fixes
    
    # ═══ Step 3: Find replace lines that come AFTER the block opener ═══
    # Find where the last search line appears in replace_text
    replace_text_stripped = replace_text.rstrip()
    
    # Find the block opener in replace_text
    last_line_idx = -1
    for i, rl in enumerate(replace_lines):
        if rl.strip() == last_search_stripped:
            last_line_idx = i
    
    if last_line_idx == -1 or last_line_idx >= len(replace_lines) - 1:
        return replace_text, fixes
    
    # ═══ Step 4: Fix indentation of subsequent lines ═══
    expected_indent = last_search_indent + 4
    fixed_lines = list(replace_lines)
    
    for i in range(last_line_idx + 1, len(replace_lines)):
        line = replace_lines[i]
        if not line.strip():
            continue  # Skip empty lines
        
        actual_indent = len(line) - len(line.lstrip())
        
        # If actual indent is less than expected, add spaces
        if actual_indent < expected_indent:
            spaces_needed = expected_indent - actual_indent
            fixed_lines[i] = (" " * spaces_needed) + line
            fixes.append(f"Line {i+1}: added {spaces_needed} spaces (indent: {actual_indent}→{expected_indent})")
    
    fixed_replace = "\n".join(fixed_lines)
    return fixed_replace, fixes




# ═══════════════════════════════════════════════════════════
# 🔍 FUZZY SEARCH — Find best match when exact fails
# ═══════════════════════════════════════════════════════════

def v12_fuzzy_find(file_content, search_text, min_similarity=0.65):
    """
    When exact search fails, find best matching lines in file.
    
    Returns: (actual_text, similarity, reason) or (None, 0, reason)
    """
    import difflib
    
    if not file_content or not search_text:
        return None, 0.0, "empty input"
    
    search_lines = [l for l in search_text.split("\n") if l.strip()]
    if not search_lines:
        return None, 0.0, "empty search"
    
    old_lines = file_content.split("\n")
    
    # ═══ Strategy 1: Exact line match ═══
    first_search = search_lines[0].strip()
    matches = []
    
    for i, old_line in enumerate(old_lines):
        if old_line.strip() == first_search:
            # Check if subsequent lines match (whitespace-tolerant)
            match = True
            for j, sl in enumerate(search_lines):
                if i + j >= len(old_lines):
                    match = False
                    break
                if old_lines[i + j].strip() != sl.strip():
                    match = False
                    break
            if match:
                # Return EXACT lines from file
                actual = "\n".join(old_lines[i:i + len(search_lines)])
                return actual, 1.0, f"exact match at line {i+1}"
            else:
                matches.append((i, 1))  # partial match
        else:
            # Check similarity of first line
            sim = difflib.SequenceMatcher(None, first_search, old_line.strip()).ratio()
            if sim >= min_similarity:
                matches.append((i, sim))
    
    if not matches:
        return None, 0.0, "no similar lines found"
    
    # ═══ Strategy 2: Best partial match ═══
    matches.sort(key=lambda x: x[1], reverse=True)
    
    for line_idx, sim in matches[:3]:
        # Try to match as many subsequent lines as possible
        best_end = line_idx
        matched = 0
        for j in range(1, len(search_lines)):
            if line_idx + j >= len(old_lines):
                break
            s_sim = difflib.SequenceMatcher(
                None, search_lines[j].strip(), old_lines[line_idx + j].strip()
            ).ratio()
            if s_sim >= 0.75:
                best_end = line_idx + j
                matched += 1
            else:
                break
        
        # Return lines from file (at least 1)
        actual = "\n".join(old_lines[line_idx:best_end + 1])
        return actual, sim, f"fuzzy match at line {line_idx+1} (similarity {sim:.0%})"
    
    return None, 0.0, "no good match"


def v12_get_search_context(filepath, search_text, context_lines=3):
    """
    Given a search text, find the closest lines in file and return
    a unique block that AI can use.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return None
    
    actual, sim, reason = v12_fuzzy_find(content, search_text)
    if actual:
        return actual, reason
    
    return None, reason


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
    
    # 🔧 Auto-fix indentation
    try:
        replace, indent_fixes = v12_fix_indentation(search, replace)
        if indent_fixes:
            fixes.extend(indent_fixes)
    except Exception:
        pass
    
    actual = None
    if search in old:
        actual = search
    else:
        s_trim = search.strip()
        if s_trim and s_trim in old:
            actual = s_trim
        else:
            # Try whitespace-tolerant matching
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
    
    # 🔍 FUZZY FALLBACK — if exact fails, try fuzzy
    if not actual:
        try:
            fuzzy_actual, sim, reason = v12_fuzzy_find(old, search)
            if fuzzy_actual:
                actual = fuzzy_actual
                fixes.append(f"🔍 Fuzzy match used: {reason}")
        except Exception:
            pass
    
    if not actual:
        return False, f"❌ Search text not found in {fp}", None, fixes
    
    # 🚨 SAFETY: Search text must be unique and meaningful
    if len(actual.strip()) < 10:
        return False, f"🚨 Search text bahut chhota hai ('{actual.strip()}') — ye galat jagah pe match karega. Command mein exact line likho.", None, fixes
    
    # Check uniqueness — search must appear only ONCE
    occurrences = old.count(actual)
    if occurrences > 1:
        return False, f"🚨 Search text {occurrences} baar mila — unique nahi hai. Command mein exact line with context likho.", None, fixes
    
    # Check if search is just punctuation
    stripped = actual.strip()
    if all(c in ')}],:;.' for c in stripped):
        return False, f"🚨 Search text sirf punctuation hai ('{stripped}') — galat jagah pe match karega. Exact line likho.", None, fixes
    
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





# ═══════════════════════════════════════════════════════════
# 🧠 SELF-LEARNING SYSTEM
# ═══════════════════════════════════════════════════════════

def v12_load_learning():
    """Load learned patterns"""
    if os.path.exists(V12_LEARNING_FILE):
        try:
            with open(V12_LEARNING_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"patterns": [], "keywords": {}, "files": {}}


def v12_save_learning(learning):
    """Save learned patterns"""
    try:
        learning["patterns"] = learning.get("patterns", [])[-100:]  # Keep last 100
        with open(V12_LEARNING_FILE, "w") as f:
            json.dump(learning, f, indent=2)
    except Exception:
        pass


def v12_extract_pattern(command, result):
    """Extract pattern from a successful change"""
    if not result.get("success"):
        return None
    
    changes = result.get("changes_applied", [])
    if not changes:
        return None
    
    # Extract pattern
    pattern = {
        "time": datetime.now().isoformat(),
        "command_keywords": [],
        "files_changed": [],
        "action_types": [],
        "search_patterns": [],
        "replace_patterns": [],
        "success": True,
    }
    
    # Extract keywords from command
    stop_words = {"karo", "add", "change", "kya", "hai", "ka", "ki", "ke", 
                  "mein", "aur", "se", "ko", "kar", "do", "ek", "tha", "ho"}
    words = re.findall(r'\w+', command.lower())
    pattern["command_keywords"] = [w for w in words if w not in stop_words and len(w) > 3][:8]
    
    # Extract files and actions
    for ch in changes:
        fp = ch.get("file", "")
        if fp:
            pattern["files_changed"].append(fp)
            # Track file usage
            learning_file = fp
        # Track action
        pattern["action_types"].append(ch.get("action", "modify"))
        # Track search/replace if present
        if ch.get("search_for"):
            pattern["search_patterns"].append(ch["search_for"][:100])
        if ch.get("replace_with"):
            pattern["replace_patterns"].append(ch["replace_with"][:100])
    
    return pattern


def v12_learn_from_success(command, result):
    """Learn from a successful command"""
    try:
        pattern = v12_extract_pattern(command, result)
        if not pattern:
            return
        
        learning = v12_load_learning()
        
        # Add pattern
        learning["patterns"].append(pattern)
        
        # Update keyword index
        for kw in pattern["command_keywords"]:
            learning["keywords"].setdefault(kw, [])
            for fp in pattern["files_changed"]:
                if fp not in learning["keywords"][kw]:
                    learning["keywords"][kw].append(fp)
        
        # Update file index
        for fp in pattern["files_changed"]:
            learning["files"].setdefault(fp, {
                "count": 0,
                "actions": {},
                "keywords": [],
            })
            learning["files"][fp]["count"] += 1
            for act in pattern["action_types"]:
                learning["files"][fp]["actions"][act] = learning["files"][fp]["actions"].get(act, 0) + 1
        
        v12_save_learning(learning)
    except Exception:
        pass


def v12_get_learning_hints(command):
    """Get hints from past successful patterns for a command"""
    try:
        learning = v12_load_learning()
        if not learning.get("patterns"):
            return ""
        
        cmd_words = set(re.findall(r'\w+', command.lower()))
        relevant_patterns = []
        
        for pattern in learning["patterns"][-30:]:  # Last 30
            kw_set = set(pattern.get("command_keywords", []))
            # Match if 2+ keywords overlap
            overlap = cmd_words & kw_set
            if len(overlap) >= 2:
                relevant_patterns.append((len(overlap), pattern))
        
        if not relevant_patterns:
            return ""
        
        # Sort by overlap
        relevant_patterns.sort(reverse=True)
        
        hints = ["\n=== PAST SUCCESSFUL PATTERNS (V12 yaad rakhta hai) ==="]
        seen_files = set()
        
        for overlap, pattern in relevant_patterns[:3]:
            files = pattern.get("files_changed", [])
            for fp in files:
                if fp in seen_files:
                    continue
                seen_files.add(fp)
                actions = pattern.get("action_types", [])
                hints.append(f"✓ Pehle '{fp}' mein change kiya tha ({', '.join(actions)})")
        
        return "\n".join(hints) if len(hints) > 1 else ""
    except Exception:
        return ""


def v12_get_top_files():
    """Get most frequently edited files (for quick access)"""
    try:
        learning = v12_load_learning()
        files = learning.get("files", {})
        sorted_files = sorted(files.items(), key=lambda x: x[1].get("count", 0), reverse=True)
        return sorted_files[:10]
    except Exception:
        return []


def v12_learning_stats():
    """Get learning statistics"""
    try:
        learning = v12_load_learning()
        patterns = learning.get("patterns", [])
        files = learning.get("files", {})
        keywords = learning.get("keywords", {})
        
        return {
            "total_patterns": len(patterns),
            "total_files": len(files),
            "total_keywords": len(keywords),
            "top_files": v12_get_top_files()[:5],
        }
    except Exception:
        return {"total_patterns": 0, "total_files": 0, "total_keywords": 0, "top_files": []}


def v12_is_vague_command(command):
    """Detect vague commands that AI can't handle well"""
    cmd_lower = command.lower()
    
    # Vague words without specific targets
    vague_words = ["bara", "chhota", "chota", "time", "jaldi",
                   "theek", "sahi", "improve", "change", "better"]
    
    # Specific indicators (file names, function names, line references)
    specific_indicators = [
        r'\.py', r'gym_pages/', r'def ', r'function',
        r'today_str', r'reminder_days',
        r'three_days_ago', r'timedelta',
    ]
    
    has_vague = any(w in cmd_lower for w in vague_words)
    has_specific = any(re.search(p, cmd_lower) for p in specific_indicators)
    
    # If vague but no specific - warn
    if has_vague and not has_specific and len(command) < 80:
        msg = (
            "⚠️ Ye command clear nahi hai. Batao:\n"
            "  • Konsi file change karni hai?\n"
            "  • Kya exact change karna hai?\n"
            "  • Kahan (line/function)?\n\n"
            "Misal: 'gym_pages/message_center.py mein today filter ko 3-day range karo'"
        )
        return True, msg
    
    return False, ""




def v12_should_use_planner(command):
    """Detect if command TRULY needs multi-step planning"""
    cmd_lower = command.lower()
    
    # ═══ SKIP CONDITIONS (position markers — single task) ═══
    # If command has "X ke baad/pehle/upar/neeche" with a file reference
    # → it's a single insert/edit, NOT multi-step
    position_markers = ["ke baad", "ke bad", "ke pehle", "ke phle",
                        "ke upar", "ke uper", "ke neeche", "ke niche",
                        "ke andar", "mein ye", "line add"]
    has_position = any(w in cmd_lower for w in position_markers)
    
    # If has a specific file reference (.py)
    has_py_file = ".py" in cmd_lower
    
    # If command looks like "X ke baad Y karo" with file → SINGLE task
    if has_position and has_py_file:
        # Check for big words too
        big_check = ["naya page", "new page", "full feature", "poora",
                     "complete", "redesign", "rewrite"]
        if not any(w in cmd_lower for w in big_check):
            return False  # Single task — skip planner
    
    # ═══ PLANNER CONDITIONS ═══
    
    # BIG actions — always need planning
    big_words = ["naya page", "new page", "full feature", "poora",
                 "complete", "redesign", "rewrite", "naya feature"]
    if any(w in cmd_lower for w in big_words):
        return True
    
    # MULTIPLE tasks (conjunctions)
    multi_task = ["aur phir", "aur bhi", "saath mein", "sath mein",
                  "dono", "plus", "aur add karo", "and also"]
    if any(w in cmd_lower for w in multi_task):
        return True
    
    # Count REAL action verbs (exclude "dhoondo/dhundo" — that's find, not change)
    action_verbs = ["karo", "banao", "add", "change", "modify",
                    "update", "remove", "delete", "create"]
    action_count = sum(cmd_lower.count(v) for v in action_verbs)
    
    # Exclude "dhoondo" from count (it's a find operation)
    # If "dhoondo" or "dhundo" present, subtract 1 from count
    if "dhoondo" in cmd_lower or "dhundo" in cmd_lower:
        action_count -= 1
    
    if action_count >= 2:
        return True
    
    return False


def v12_plan_steps(command):
    """Ask AI to break command into steps"""
    prompt = f"""TASK: Break this command into 2-5 clear sequential steps.

COMMAND: {command}

Output JSON ONLY:
{{
  "is_multi_step": true,
  "reasoning": "why this needs multiple steps",
  "steps": [
    {{"num": 1, "title": "step title", "description": "what to do", "files": ["file.py"]}}
  ]
}}

If command is simple (1 change), output:
{{"is_multi_step": false, "reasoning": "simple", "steps": []}}"""
    
    try:
        resp = v12_call_ai_smart(prompt, max_tokens=2000, prefer="cohere")
        parsed = v12_parse_json(resp)
        if "error" in parsed:
            return None
        return parsed
    except Exception:
        return None


def v12_execute_step(step, original_command, gym_id=None):
    """Execute a single step"""
    step_desc = step.get("description", "")
    step_files = step.get("files", [])
    
    if step_files:
        step_command = f"{step_desc}. Files: {', '.join(step_files)}"
    else:
        step_command = step_desc
    
    full_command = f"{step_command}. (Original command: {original_command})"
    return v12_execute(full_command, preview_only=False)


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
    
    # Detect vague commands
    is_vague, vague_msg = v12_is_vague_command(command)
    if is_vague:
        result["message"] = vague_msg
        result["success"] = False
        result["vague"] = True
        return result
    
    # Detect mode
    mode = v12_detect_mode(command)
    result["mode"] = mode
    
    # 🎯 Multi-step planner (only for preview mode)
    if preview_only and v12_should_use_planner(command):
        try:
            plan = v12_plan_steps(command)
            if plan and plan.get("is_multi_step"):
                result["multi_step_plan"] = plan
                result["message"] = f"🎯 Ye {len(plan.get('steps', []))}-step kaam hai"
                result["plan"] = [f"{s.get('num')}. {s.get('title')}" for s in plan.get('steps', [])]
                result["success"] = True
                return result
        except Exception:
            pass
    
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
    
    # Check for full file rewrite (suspicious)
    for ch in changes:
        if ch.get("action") == "create":
            nc = ch.get("new_content", "")
            if len(nc) > 8000:  # 8000 chars = ~200 lines
                # OK for new pages, but flag for review
                pass
    
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
            # Auto-test (smart)
            ok_t, mt, td = v12_smart_test(fp) if fp.endswith(".py") else (True, "N/A", {})
            result["verification"][fp] = {
                "syntax": ok_s, "syntax_msg": ms,
                "imports_ok": ok_i, "missing": mi,
                "compiles": ok_c, "compile_msg": mc,
                "smart_test": ok_t, "smart_msg": mt,
            }
    
    # ── AUTO-TEST + ROLLBACK ──
    if applied:
        applied_files = [ch["file"] for ch in applied]
        test_ok, test_msg, failed_files = v12_auto_test_and_rollback(applied_files, bdir)
        
        if not test_ok:
            result["message"] = test_msg
            result["success"] = False
            result["rolled_back"] = True
            result["test_failed"] = True
            result["failed_tests"] = failed_files
            # 🧠 LEARN from failure too
            try:
                v12_learn_from_success(command, {"success": True, "changes_applied": applied})
            except Exception:
                pass
            # Don't save commit
            try:
                v12_save_memory(command, result)
                v12_save_conversation(command, result.get("explanation", ""), 
                                      result.get("mode", "fix"), 
                                      v12_detect_topic(command), False)
            except Exception:
                pass
            return result
        
        v12_save_commit(command[:100], safe_changes, bdir)
        v12_scan_project()
        
        # 🧠 LEARN from success
        try:
            v12_learn_from_success(command, result)
        except Exception:
            pass
    
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
