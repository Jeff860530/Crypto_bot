import os
import fnmatch

# 🔥 1. 路徑設定
# CURRENT_DIR:  .../crypto_bot/scripts (腳本所在位置)
# PROJECT_ROOT: .../crypto_bot (專案根目錄)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

# 預設忽略清單
# 注意：我們依然忽略 scripts 資料夾的掃描，避免把腳本自己也寫進去 context
DEFAULT_IGNORE_DIRS = {
    '.git', '.venv', 'venv', '__pycache__', 
    '.idea', '.vscode', 'node_modules', 'logs'
}

DEFAULT_IGNORE_FILES = {
    'project_context.txt', '.DS_Store', 'poetry.lock', 'package-lock.json', '*.pyc'
}

ALLOWED_EXTENSIONS = {
    '.py', '.json', '.md', '.txt', '.yml', '.yaml', 
    '.html', '.css', '.js', '.ini'
}

def load_gitignore_patterns(root_dir):
    """讀取 .gitignore"""
    gitignore_path = os.path.join(root_dir, '.gitignore')
    patterns = set()
    
    if os.path.exists(gitignore_path):
        try:
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        patterns.add(line.rstrip('/'))
        except Exception as e:
            print(f"⚠️ 無法讀取 .gitignore: {e}")
            
    return patterns

def is_ignored(path, root_dir, ignore_dirs, ignore_files, gitignore_patterns):
    """檢查是否忽略"""
    name = os.path.basename(path)
    
    if name in ignore_dirs or name in ignore_files:
        return True
    
    rel_path = os.path.relpath(path, root_dir)
    rel_path_unix = rel_path.replace(os.sep, '/')
    
    for pattern in gitignore_patterns:
        if fnmatch.fnmatch(name, pattern):
            return True
        if fnmatch.fnmatch(rel_path_unix, pattern):
            return True
        if pattern in rel_path_unix.split('/'):
             return True

    return False

def generate_project_context(output_filename="project_context.txt"):
    # 🔥 修改這裡：將輸出路徑改為 CURRENT_DIR (scripts 資料夾)
    output_file = os.path.join(CURRENT_DIR, output_filename)
    
    gitignore_patterns = load_gitignore_patterns(PROJECT_ROOT)
    
    print(f"📂 掃描目標: {PROJECT_ROOT}")
    print(f"📄 輸出位置: {output_file}")

    with open(output_file, 'w', encoding='utf-8') as outfile:
        # 1. 目錄結構
        outfile.write("=== PROJECT STRUCTURE ===\n")
        for dirpath, dirnames, filenames in os.walk(PROJECT_ROOT):
            dirnames[:] = [d for d in dirnames if not is_ignored(os.path.join(dirpath, d), PROJECT_ROOT, DEFAULT_IGNORE_DIRS, DEFAULT_IGNORE_FILES, gitignore_patterns)]
            
            level = dirpath.replace(PROJECT_ROOT, '').count(os.sep)
            indent = ' ' * 4 * level
            outfile.write(f"{indent}{os.path.basename(dirpath)}/\n")
            
            subindent = ' ' * 4 * (level + 1)
            for f in filenames:
                if not is_ignored(os.path.join(dirpath, f), PROJECT_ROOT, DEFAULT_IGNORE_DIRS, DEFAULT_IGNORE_FILES, gitignore_patterns):
                    outfile.write(f"{subindent}{f}\n")
        
        outfile.write("\n" + "="*50 + "\n\n")

        # 2. 檔案內容
        outfile.write("=== FILE CONTENTS ===\n")
        file_count = 0
        for dirpath, dirnames, filenames in os.walk(PROJECT_ROOT):
            dirnames[:] = [d for d in dirnames if not is_ignored(os.path.join(dirpath, d), PROJECT_ROOT, DEFAULT_IGNORE_DIRS, DEFAULT_IGNORE_FILES, gitignore_patterns)]
            
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                
                if is_ignored(filepath, PROJECT_ROOT, DEFAULT_IGNORE_DIRS, DEFAULT_IGNORE_FILES, gitignore_patterns):
                    continue
                
                ext = os.path.splitext(filename)[1]
                if ext not in ALLOWED_EXTENSIONS and filename != 'requirements.txt':
                    continue

                rel_path = os.path.relpath(filepath, PROJECT_ROOT)
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as infile:
                        content = infile.read()
                        
                    outfile.write(f"\n--- START OF FILE: {rel_path} ---\n")
                    outfile.write(content)
                    outfile.write(f"\n--- END OF FILE: {rel_path} ---\n")
                    file_count += 1
                except Exception as e:
                    print(f"⚠️ 無法讀取檔案 {rel_path}: {e}")

    print(f"✅ 匯出完成！檔案位於 scripts 資料夾內。")

if __name__ == "__main__":
    generate_project_context()