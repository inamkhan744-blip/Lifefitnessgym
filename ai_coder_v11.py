# ai_coder_v11.py
# AI Coder V11 — Trust Mode
# Database NEVER touched. Har change verified. Auto-rollback.

import os, re, json, ast, shutil, time, subprocess, zipfile, difflib
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

# ============================================================
# 🛡️ SAFETY CONFIG — DATABASE PROTECTED ZONE
# ============================================================

# Ye files AI KABHI touch nahi karega
PROTECTED_FILES = {
    "database.py",           # ← TUMHARA DATABASE — SACRED
    "auth.py",               # ← Auth logic — sensitive
    ".env",                  # ← Secrets
    "gym_pro_v2.db",         # ← SQLite DB
    "gym_pro_v3.db",         # ← SQLite DB
    "gym_pro.db",            # ← SQLite DB
    "requirements.txt",      # ← Dependency lock
}

# Ye file extensions AI KABHI modify nahi karega
PROTECTED_EXTENSIONS = {".db", ".sqlite", ".sqlite3", ".env", ".key", ".pem"}

# Ye folders AI KABHI touch nahi karega
PROTECTED_DIRS = {"backups", ".backups", "uploads", "member_photos", ".git"}

# Sirf in folders mein AI kaam kar sakta hai
ALLOWED_WORK_DIRS = {".", "gym_pages", "utils", "components"}

CODER_MAX_CHARS = 32000
CODER_MAX_TOKENS = 16000
CODER_MAX_RETRIES = 3
BACKUP_ROOT = ".ai_coder_backups"
COMMITS_FILE = ".ai_coder_v11_commits.json"
SKIP_DIRS = {"__pycache__", ".git", "node_modules", ".streamlit", "backups",
             "uploads", "member_photos", "docs", "logs", ".backups", BACKUP_ROOT}


# ============================================================
# 🛡️ SAFETY LAYER 1 — FILE PROTECTION CHECK
# ============================================================

def is_protected(filepath: str) -> Tuple[bool, str]:
    """Check karo ke file protected hai ya nahi"""
    if not filepath:
        return True, "❌ Empty path"
    
    fp = filepath.replace("\\", "/").strip()
    basename = os.path.basename(fp)
    
    # Direct protected file?
    if basename in PROTECTED_FILES:
        return True, f"🛡️ '{basename}' PROTECTED hai — database/auth safe zone"
    
    # Protected extension?
    ext = os.path.splitext(basename)[1].lower()
    if ext in PROTECTED_EXTENSIONS:
        return True, f"🛡️ '{ext}' files PROTECTED hain"
    
    # Protected folder?
    parts = fp.split("/")
    for part in parts:
        if part in PROTECTED_DIRS:
            return True, f"🛡️ '{part}/' folder PROTECTED hai"
    
    # Allowed work dir?
    if "/" in fp:
        top_dir = parts[0]
        if top_dir not in ALLOWED_WORK_DIRS and not top_dir.startswith("."):
            return True, f"🛡️ '{top_dir}/' mein AI kaam nahi kar sakta"
    
    return False, "✅ Safe"


def assert_not_protected(filepath: str) -> None:
    """Raise karo agar file protected hai"""
    protected, reason = is_protected(filepath)
    if protected:
        raise PermissionError(reason)


# ============================================================
# 🛡️ SAFETY LAYER 2 — BACKUP BEFORE EVERY CHANGE
# ============================================================

def _make_backup_dir() -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    bdir = os.path.join(BACKUP_ROOT, ts)
    os.makedirs(bdir, exist_ok=True)
    return bdir


def _backup_file(fp: str, backup_dir: str) -> Optional[str]:
    """File ka backup lo backup_dir mein"""
    try:
        if not os.path.exists(fp):
            return None
        # Relative path preserve karo
        rel = fp.replace("\\", "/").lstrip("./")
        dst = os.path.join(backup_dir, rel)
        os.makedirs(os.path.dirname(dst) or backup_dir, exist_ok=True)
        shutil.copy2(fp, dst)
        return dst
    except Exception:
        return None


def _restore_from_backup(fp: str, backup_path: str) -> bool:
    """Backup se restore karo"""
    try:
        if backup_path and os.path.exists(backup_path):
            shutil.copy2(backup_path, fp)
            return True
    except Exception:
        pass
    return False


# ============================================================
# 🛡️ SAFETY LAYER 3 — SYNTAX + IMPORT VERIFICATION
# ============================================================

def validate_syntax(code: str) -> Tuple[bool, str]:
    """Python syntax check"""
    try:
        ast.parse(code)
        return True, "✅ Syntax OK"
    except SyntaxError as e:
        return False, f"❌ Line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, f"❌ Parse error: {e}"


def validate_imports(code: str) -> Tuple[bool, List[str]]:
    """Import check — sirf syntax level (execute nahi karega)"""
    stdlib = {"os","sys","io","re","json","ast","time","shutil","datetime",
              "pathlib","typing","hashlib","uuid","sqlite3","subprocess",
              "threading","contextlib","zipfile","difflib","collections",
              "functools","itertools","math","random","string","csv","base64"}
    local_modules = {"database","auth","styles","themes","object_store",
                     "id_card","qr_utils","profile_token","printer_utils",
                     "ai_coder_v11","ai_assistant"}
    missing = []
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    if top in stdlib or top in local_modules:
                        continue
                    if top not in missing:
                        missing.append(top)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    top = node.module.split(".")[0]
                    if top in stdlib or top in local_modules:
                        continue
                    if top not in missing:
                        missing.append(top)
    except Exception:
        pass
    return (len(missing) == 0), missing


def validate_code_safety(code: str) -> Tuple[bool, List[str]]:
    """Dangerous patterns check karo"""
    warnings = []
    dangerous = [
        (r'\bos\.remove\s*\(', "⚠️ os.remove — file delete"),
        (r'\bshutil\.rmtree\s*\(', "🚨 shutil.rmtree — folder delete!"),
        (r'\bDROP\s+TABLE\b', "🚨 DROP TABLE!"),
        (r'\bDELETE\s+FROM\b', "⚠️ DELETE FROM — DB rows delete"),
        (r'\bTRUNCATE\b', "🚨 TRUNCATE!"),
        (r'database\.py', "🛡️ database.py reference — PROTECTED"),
        (r'\beval\s*\(', "⚠️ eval() — unsafe"),
        (r'\bexec\s*\(', "⚠️ exec() — unsafe"),
        (r'__import__\s*\(', "⚠️ __import__ — dynamic import"),
    ]
    for pattern, msg in dangerous:
        if re.search(pattern, code):
            warnings.append(msg)
    return (len(warnings) == 0), warnings


# ============================================================
# 🛡️ SAFETY LAYER 4 — APPLY WITH AUTO-ROLLBACK
# ============================================================

def safe_apply_create(filepath: str, content: str) -> Tuple[bool, str]:
    """Naya file safely banao"""
    protected, reason = is_protected(filepath)
    if protected:
        return False, reason
    
    ok, msg = validate_syntax(content)
    if not ok:
        return False, f"❌ Syntax fail: {msg}"
    
    safe, warnings = validate_code_safety(content)
    if not safe and any("🚨" in w for w in warnings):
        return False, f"🚨 DANGEROUS code: {', '.join(warnings)}"
    
    try:
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return True, f"✅ Created: {filepath}"
    except Exception as e:
        return False, f"❌ {filepath}: {e}"


def safe_apply_search_replace(filepath: str, search: str, replace: str) -> Tuple[bool, str, Optional[str]]:
    """Search-replace with full safety"""
    protected, reason = is_protected(filepath)
    if protected:
        return False, reason, None
    
    if not os.path.exists(filepath):
        return False, f"❌ {filepath} nahi mila", None
    
    if not search or search == replace:
        return False, "❌ Empty ya same search/replace", None
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            old_content = f.read()
    except Exception as e:
        return False, f"❌ Read fail: {e}", None
    
    if search not in old_content:
        # Try trimmed match
        search_trim = search.strip()
        if search_trim and search_trim in old_content:
            search = search_trim
        else:
            return False, f"❌ Search text nahi mila in {filepath}", None
    
    # Backup
    bdir = _make_backup_dir()
    backup_path = _backup_file(filepath, bdir)
    
    # New content
    new_content = old_content.replace(search, replace, 1)
    
    # Syntax check
    ok, msg = validate_syntax(new_content)
    if not ok:
        return False, f"❌ Syntax fail (rollback): {msg}", backup_path
    
    # Dangerous check
    safe, warnings = validate_code_safety(new_content)
    if not safe and any("🚨" in w for w in warnings):
        return False, f"🚨 DANGEROUS (rollback): {', '.join(warnings)}", backup_path
    
    # Write
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        return True, f"✅ Modified: {filepath}", backup_path
    except Exception as e:
        _restore_from_backup(filepath, backup_path)
        return False, f"❌ Write fail (restored): {e}", backup_path


# ============================================================
# 🧠 AI BRAIN — MULTI-STEP PLANNER
# ============================================================

CODER_SYSTEM_PROMPT = """You are GymPro AI Coder V11 — TRUST MODE.

ABSOLUTE RULES (never break):
1. 🛡️ database.py, auth.py, *.db, *.env — NEVER touch these. Protected zone.
2. Output valid JSON only. No markdown. No explanation outside JSON.
3. Existing files: use search_for / replace_with (exact match).
4. New files: complete content in new_content.
5. Validate Python syntax before output.
6. Never use: eval(), exec(), os.remove on .py files, DROP/DELETE SQL.
7. If user asks to modify database.py — REFUSE politely.
8. Roman Urdu for user-facing messages.

RESPONSE FORMAT:
{
  "explanation": "Roman Urdu mein short explanation",
  "plan": ["step 1", "step 2"],
  "confidence": 95,
  "changes": [
    {"file": "path.py", "action": "create", "new_content": "..."},
    {"file": "path.py", "action": "modify", "search_for": "...", "replace_with": "..."}
  ],
  "verification": ["check 1", "check 2"]
}
"""


def call_ai(prompt: str, system: str = None, max_tokens: int = CODER_MAX_TOKENS) -> str:
    """Groq AI call with retry"""
    key = os.environ.get("GROQ_API_KEY", "").strip()
    if not key:
        return '{"error": "GROQ_API_KEY nahi mila"}'
    if system is None:
        system = CODER_SYSTEM_PROMPT
    
    models = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "llama-3.3-70b-versatile"]
    for attempt in range(CODER_MAX_RETRIES):
        for model in models:
            try:
                r = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {key}",
                             "Content-Type": "application/json"},
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.2,
                        "max_tokens": max_tokens,
                    },
                    timeout=120,
                )
                if r.status_code == 200:
                    return r.json()["choices"][0]["message"]["content"].strip()
                elif r.status_code == 429:
                    time.sleep(5)
            except Exception:
                continue
        time.sleep(2)
    return '{"error": "All models failed"}'


def parse_json_response(response: str) -> Dict:
    """Robust JSON parsing"""
    if not isinstance(response, str):
        return {"error": "Not string", "raw": str(response)[:500]}
    clean = response.strip()
    if "```json" in clean:
        clean = clean.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in clean:
        parts = clean.split("```")
        if len(parts) >= 3:
            clean = parts[1].strip()
            if clean.startswith("json"):
                clean = clean[4:].strip()
    try:
        return json.loads(clean)
    except Exception:
        pass
    try:
        start = clean.find("{")
        end = clean.rfind("}")
        if start != -1 and end > start:
            return json.loads(clean[start:end+1])
    except Exception:
        pass
    return {"error": "JSON parse fail", "raw": response[:500]}


# ============================================================
# 📁 PROJECT SCANNER
# ============================================================

def list_project_files() -> List[str]:
    """Saari safe files list karo"""
    files = []
    for root, dirs, filenames in os.walk("."):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in filenames:
            if f.endswith(".py") and ".backup" not in f:
                path = os.path.join(root, f).replace("./", "").replace("\\", "/")
                protected, _ = is_protected(path)
                if not protected:
                    files.append(path)
    return sorted(files)


def read_file_safe(fp: str, max_chars: int = CODER_MAX_CHARS) -> str:
    """File read karo (protected check ke saath)"""
    protected, reason = is_protected(fp)
    if protected:
        return f"# {reason}"
    try:
        with open(fp, "r", encoding="utf-8") as f:
            content = f.read()
        if len(content) > max_chars:
            return content[:max_chars] + "\n\n... [truncated]"
        return content
    except Exception as e:
        return f"# Error: {e}"


def file_stats(fp: str) -> Dict:
    try:
        with open(fp, "r", encoding="utf-8") as f:
            content = f.read()
        return {
            "lines": len(content.splitlines()),
            "functions": re.findall(r'^def\s+(\w+)', content, re.MULTILINE),
            "classes": re.findall(r'^class\s+(\w+)', content, re.MULTILINE),
        }
    except Exception:
        return {"lines": 0, "functions": [], "classes": []}


def project_context() -> str:
    """AI ko project ka context do"""
    files = list_project_files()
    lines = ["=== PROJECT CONTEXT ==="]
    for f in files[:50]:
        s = file_stats(f)
        lines.append(f"{f}: {s['lines']} lines, {len(s['functions'])} funcs, {len(s['classes'])} classes")
    return "\n".join(lines)


# ============================================================
# 💾 COMMIT SYSTEM
# ============================================================

def save_commit(description: str, changes: List[Dict], backup_dir: str):
    try:
        commits = []
        if os.path.exists(COMMITS_FILE):
            with open(COMMITS_FILE) as f:
                commits = json.load(f)
        commit = {
            "id": len(commits) + 1,
            "time": datetime.now().isoformat(),
            "description": description,
            "backup_dir": backup_dir,
            "changes": [{"file": c.get("file"), "action": c.get("action", "modify")} for c in changes],
        }
        commits.append(commit)
        with open(COMMITS_FILE, "w") as f:
            json.dump(commits, f, indent=2)
    except Exception:
        pass


def get_commits() -> List[Dict]:
    if os.path.exists(COMMITS_FILE):
        try:
            with open(COMMITS_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return []


def time_travel(commit_id: int) -> Tuple[bool, str]:
    """Commit par wapas jao"""
    commits = get_commits()
    commit = next((c for c in commits if c["id"] == commit_id), None)
    if not commit:
        return False, "❌ Commit not found"
    bdir = commit.get("backup_dir", "")
    if not os.path.exists(bdir):
        return False, "❌ Backup folder not found"
    restored = []
    for ch in commit.get("changes", []):
        fp = ch.get("file", "")
        protected, _ = is_protected(fp)
        if protected:
            continue
        backup_fp = os.path.join(bdir, fp.replace("\\", "/").lstrip("./"))
        if os.path.exists(backup_fp):
            try:
                shutil.copy2(backup_fp, fp)
                restored.append(fp)
            except Exception:
                pass
    return True, f"✅ Restored {len(restored)} files"


# ============================================================
# 🎯 MAIN WORKFLOW — "SUNO AUR KARO"
# ============================================================

def execute_command(user_command: str, verbose: bool = False) -> Dict:
    """
    User ka natural language command lo aur poora karo.
    
    Returns: {
        "success": bool,
        "message": str,
        "plan": list,
        "changes_applied": list,
        "verification": dict,
        "backup_dir": str,
    }
    """
    result = {
        "success": False,
        "message": "",
        "plan": [],
        "changes_applied": [],
        "verification": {},
        "backup_dir": None,
    }
    
    if not user_command.strip():
        result["message"] = "❌ Empty command"
        return result
    
    # Step 1: AI ko command do + project context
    ctx = project_context()
    prompt = f"""USER COMMAND: {user_command}

PROJECT CONTEXT:
{ctx}

Now output your plan + changes in JSON (per system prompt)."""
    
    ai_response = call_ai(prompt, max_tokens=CODER_MAX_TOKENS)
    parsed = parse_json_response(ai_response)
    
    if "error" in parsed:
        result["message"] = f"❌ AI error: {parsed.get('error')}"
        return result
    
    result["plan"] = parsed.get("plan", [])
    
    # Step 2: Verify safety of all changes
    changes = parsed.get("changes", [])
    if not changes:
        result["message"] = "⚠️ AI ne koi change nahi diya. Explanation: " + str(parsed.get("explanation", ""))
        return result
    
    safe_changes = []
    blocked_changes = []
    for ch in changes:
        fp = ch.get("file", "")
        protected, reason = is_protected(fp)
        if protected:
            blocked_changes.append(f"{fp}: {reason}")
        else:
            safe_changes.append(ch)
    
    if blocked_changes:
        result["message"] = "🛡️ Kuch files protected hain:\n" + "\n".join(blocked_changes)
        if not safe_changes:
            return result
    
    # Step 3: Apply changes with auto-backup
    backup_dir = _make_backup_dir()
    applied = []
    failed = []
    
    for ch in safe_changes:
        fp = ch.get("file", "")
        action = ch.get("action", "modify")
        
        # Backup before change
        if os.path.exists(fp):
            _backup_file(fp, backup_dir)
        
        if action == "create":
            ok, msg = safe_apply_create(fp, ch.get("new_content", ""))
        elif action == "modify":
            ok, msg, _ = safe_apply_search_replace(
                fp,
                ch.get("search_for", ""),
                ch.get("replace_with", ""),
            )
        elif action == "delete":
            ok, msg = False, "❌ Delete not allowed via AI (safety)"
        else:
            ok, msg = False, f"❌ Unknown action: {action}"
        
        if ok:
            applied.append({"file": fp, "action": action, "message": msg})
        else:
            failed.append({"file": fp, "action": action, "message": msg})
    
    result["backup_dir"] = backup_dir
    result["changes_applied"] = applied
    
    # Step 4: Post-verification
    verification = {}
    for ch in applied:
        fp = ch["file"]
        if os.path.exists(fp):
            with open(fp) as f:
                content = f.read()
            ok_syn, msg_syn = validate_syntax(content)
            ok_imp, missing = validate_imports(content)
            verification[fp] = {
                "syntax": ok_syn,
                "syntax_msg": msg_syn,
                "imports_ok": ok_imp,
                "missing_imports": missing,
            }
    result["verification"] = verification
    
    # Step 5: Save commit
    if applied:
        save_commit(user_command[:100], safe_changes, backup_dir)
    
    # Step 6: Build result message
    if failed:
        result["message"] = f"⚠️ {len(applied)} applied, {len(failed)} failed"
    else:
        result["message"] = f"✅ {len(applied)} changes applied successfully!"
    
    result["success"] = len(failed) == 0 and len(applied) > 0
    return result


def auto_fix_error(error_text: str, filepath: str = None) -> Dict:
    """Error message lo, fix karo"""
    ctx = ""
    if filepath and os.path.exists(filepath):
        ctx = f"\n\nFILE: {filepath}\nCONTENT:\n{read_file_safe(filepath, 15000)}"
    
    prompt = f"""AUTO-FIX REQUEST

ERROR:
{error_text}
{ctx}

Diagnose karo aur fix do. Output JSON:
{{
  "diagnosis": "kya galat hai",
  "fix_plan": ["step 1", "step 2"],
  "changes": [
    {{"file": "...", "action": "modify", "search_for": "...", "replace_with": "..."}}
  ]
}}"""
    
    resp = call_ai(prompt, max_tokens=8000)
    parsed = parse_json_response(resp)
    
    if "error" in parsed:
        return {"success": False, "message": parsed["error"]}
    
    # Apply changes
    changes = parsed.get("changes", [])
    backup_dir = _make_backup_dir()
    applied = []
    failed = []
    
    for ch in changes:
        fp = ch.get("file", "")
        protected, reason = is_protected(fp)
        if protected:
            failed.append({"file": fp, "message": reason})
            continue
        ok, msg, _ = safe_apply_search_replace(fp, ch.get("search_for", ""), ch.get("replace_with", ""))
        if ok:
            applied.append({"file": fp, "message": msg})
        else:
            failed.append({"file": fp, "message": msg})
    
    if applied:
        save_commit(f"Auto-fix: {error_text[:60]}", changes, backup_dir)
    
    return {
        "success": len(failed) == 0,
        "diagnosis": parsed.get("diagnosis", ""),
        "fix_plan": parsed.get("fix_plan", []),
        "applied": applied,
        "failed": failed,
        "backup_dir": backup_dir,
    }


# ============================================================
# 🧪 SELF-TEST
# ============================================================

def self_test() -> Dict:
    """AI Coder ka self-test"""
    results = {
        "protected_check": False,
        "syntax_validate": False,
        "import_validate": False,
        "safety_check": False,
        "backup_system": False,
        "ai_connection": False,
    }
    
    # 1. Protected check
    p1, _ = is_protected("database.py")
    p2, _ = is_protected("gym_pages/bmi.py")
    results["protected_check"] = p1 and not p2
    
    # 2. Syntax validate
    ok1, _ = validate_syntax("x = 1")
    ok2, _ = validate_syntax("def broken(")
    results["syntax_validate"] = ok1 and not ok2
    
    # 3. Import validate
    ok3, _ = validate_imports("import os\nimport database")
    ok4, missing = validate_imports("import nonexistent_xyz_123")
    results["import_validate"] = ok3 and not ok4
    
    # 4. Safety check
    safe1, _ = validate_code_safety("x = 1")
    safe2, _ = validate_code_safety("import shutil; shutil.rmtree('/')")
    results["safety_check"] = safe1 and not safe2
    
    # 5. Backup system
    try:
        bdir = _make_backup_dir()
        results["backup_system"] = os.path.exists(bdir)
    except Exception:
        pass
    
    # 6. AI connection
    try:
        r = call_ai("Reply with just: OK", max_tokens=10)
        results["ai_connection"] = "error" not in r.lower()
    except Exception:
        pass
    
    return results