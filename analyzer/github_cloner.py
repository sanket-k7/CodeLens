import os
import re
import shutil
import tempfile
from collections import Counter
from urllib.parse import urlparse

from git import Repo

from analyzer.file_scanner import scan_repository
from analyzer.code_analyzer import analyze_file


def validate_github_url(url):
    parsed = urlparse(url.strip())
    if parsed.scheme not in ('http', 'https') or parsed.netloc.lower() not in ('github.com', 'www.github.com'):
        raise ValueError('Only public GitHub repository URLs are supported.')
    parts = [p for p in parsed.path.strip('/').split('/') if p]
    if len(parts) < 2:
        raise ValueError('Enter a URL like https://github.com/user/repository')
    return f'https://github.com/{parts[0]}/{parts[1]}.git'


def _relative(path, root):
    return os.path.relpath(path, root).replace(os.sep, '/')


def _repo_name(url):
    name = urlparse(url).path.strip('/').split('/')[-1]
    return name[:-4] if name.endswith('.git') else name


def _technology_stack(files):
    names = {os.path.basename(f['file']).lower() for f in files}
    languages = Counter(f['language'] for f in files if f['language'] not in ('Unknown', 'Text', 'CSV', 'Markdown', 'Documentation'))
    stack = []
    if 'package.json' in names: stack.append('Node.js')
    if any(f['language'] == 'TypeScript' for f in files): stack.append('TypeScript')
    if any(f['language'] == 'JavaScript' for f in files): stack.append('JavaScript')
    if any(f['language'] == 'Python' for f in files): stack.append('Python')
    if 'dockerfile' in names or 'docker-compose.yml' in names: stack.append('Docker')
    if 'requirements.txt' in names or 'pyproject.toml' in names: stack.append('Python package manager')
    if 'package.json' in names: stack.append('npm')
    if 'readme.md' in names: stack.append('README documentation')
    return stack or [languages.most_common(1)[0][0]] if languages else []


def _onboarding(files, stack):
    candidates = []
    priority = ['README.md', 'main.py', 'app.py', 'server.py', 'index.ts', 'index.tsx', 'main.tsx', 'App.tsx', 'App.jsx', 'package.json', 'requirements.txt']
    for wanted in priority:
        for f in files:
            if os.path.basename(f['file']).lower() == wanted.lower():
                candidates.append(_relative(f['file'], f['_root']))
                break
    return {
        'first_steps': candidates[:7],
        'summary': f"Start with {candidates[0]}" if candidates else 'Start with the README and project entry point.',
        'technology_stack': stack,
    }


def analyze_github_repository(github_url):
    clone_url = validate_github_url(github_url)
    repository_path = tempfile.mkdtemp(prefix='codelens_')
    try:
        Repo.clone_from(clone_url, repository_path, depth=1)
        paths = scan_repository(repository_path)
        analyzed = []
        for path in paths:
            try:
                item = analyze_file(path)
                item['_root'] = repository_path
                item['file'] = _relative(path, repository_path)
                analyzed.append(item)
            except Exception as exc:
                analyzed.append({'file': _relative(path, repository_path), 'language': 'Unknown', 'classes': [], 'functions': [], 'imports': [], 'lines': 0, 'errors': [str(exc)]})

        languages = Counter(item['language'] for item in analyzed)
        total_lines = sum(item.get('lines', 0) for item in analyzed)
        total_classes = sum(len(item.get('classes', [])) for item in analyzed)
        total_functions = sum(len(item.get('functions', [])) for item in analyzed)
        total_imports = sum(len(item.get('imports', [])) for item in analyzed)
        errors = sum(len(item.get('errors', [])) for item in analyzed)
        stack = _technology_stack(analyzed)
        onboarding = _onboarding(analyzed, stack)
        for item in analyzed: item.pop('_root', None)

        return {
            'repository': _repo_name(clone_url),
            'github_url': github_url,
            'total_files': len(analyzed),
            'total_lines': total_lines,
            'total_classes': total_classes,
            'total_functions': total_functions,
            'total_imports': total_imports,
            'languages': dict(languages),
            'technology_stack': stack,
            'analysis_errors': errors,
            'onboarding': onboarding,
            'files': analyzed,
        }
    finally:
        shutil.rmtree(repository_path, ignore_errors=True)
