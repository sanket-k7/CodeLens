import os

IGNORED_DIRECTORIES = {'.git', '.venv', 'venv', 'env', 'node_modules', '__pycache__', 'build', 'dist', '.idea', '.vscode', 'coverage', '.pytest_cache'}
IGNORED_EXTENSIONS = {'.pyc', '.pyo', '.so', '.dll', '.exe'}
MAX_TEXT_FILE_SIZE = 5 * 1024 * 1024


def scan_repository(repository_path):
    files = []
    for root, directories, filenames in os.walk(repository_path):
        directories[:] = [d for d in directories if d not in IGNORED_DIRECTORIES]
        for filename in filenames:
            path = os.path.join(root, filename)
            if os.path.splitext(filename)[1].lower() in IGNORED_EXTENSIONS:
                continue
            try:
                if os.path.getsize(path) <= MAX_TEXT_FILE_SIZE:
                    files.append(path)
            except OSError:
                continue
    return sorted(files)
