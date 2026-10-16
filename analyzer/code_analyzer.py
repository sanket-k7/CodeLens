import ast
import json
import os
import re
from collections import Counter

LANGUAGE_MAP = {
    '.py': 'Python', '.js': 'JavaScript', '.jsx': 'JavaScript',
    '.ts': 'TypeScript', '.tsx': 'TypeScript', '.java': 'Java',
    '.c': 'C', '.h': 'C/C++ Header', '.cpp': 'C++', '.cc': 'C++',
    '.cxx': 'C++', '.hpp': 'C++ Header', '.cs': 'C#', '.go': 'Go',
    '.rs': 'Rust', '.php': 'PHP', '.kt': 'Kotlin', '.swift': 'Swift',
    '.html': 'HTML', '.htm': 'HTML', '.css': 'CSS', '.scss': 'SCSS',
    '.json': 'JSON', '.xml': 'XML', '.yaml': 'YAML', '.yml': 'YAML',
    '.csv': 'CSV', '.sql': 'SQL', '.md': 'Markdown', '.txt': 'Text',
    '.sh': 'Shell', '.bat': 'Batch', '.cmd': 'Batch', '.ps1': 'PowerShell',
    '.pkl': 'Pickle/Binary', '.pickle': 'Pickle/Binary', '.ipynb': 'Jupyter Notebook',
}

SPECIAL_FILES = {
    'dockerfile': 'Docker', 'makefile': 'Makefile', 'jenkinsfile': 'Jenkins',
    '.gitignore': 'Git Configuration', '.gitattributes': 'Git Configuration',
    '.dockerignore': 'Docker Configuration', '.env': 'Environment',
    '.env.example': 'Environment', 'requirements.txt': 'Python Dependencies',
    'pyproject.toml': 'TOML', 'package.json': 'Node.js Configuration',
    'package-lock.json': 'Node.js Lockfile', 'pnpm-lock.yaml': 'YAML',
    'yarn.lock': 'Lockfile', 'readme': 'Documentation',
}

BINARY_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.ico', '.pdf', '.exe', '.dll', '.zip', '.rar', '.7z', '.mp3', '.mp4', '.mov', '.woff', '.woff2', '.ttf', '.otf'}


def get_extension(file_path):
    return os.path.splitext(file_path)[1].lower()


def detect_language(file_path):
    name = os.path.basename(file_path).lower()
    if name in SPECIAL_FILES:
        return SPECIAL_FILES[name]
    if name.startswith('readme'):
        return 'Documentation'
    if name.startswith('license'):
        return 'License'
    return LANGUAGE_MAP.get(get_extension(file_path), 'Unknown')


def read_file(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
        return file.read()


def count_lines(source_code):
    return len(source_code.splitlines())


def _unique(items):
    return list(dict.fromkeys(items))


def _node_info(node, kind, source_lines):
    end = getattr(node, 'end_lineno', node.lineno)
    return {
        'name': node.name,
        'line_start': node.lineno,
        'line_end': end,
        'kind': kind,
        'lines': max(1, end - node.lineno + 1),
    }


def _cyclomatic_python(node):
    decision_nodes = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.IfExp, ast.Try, ast.With, ast.AsyncWith)
    score = 1
    for child in ast.walk(node):
        if isinstance(child, decision_nodes):
            score += 1
        elif isinstance(child, ast.BoolOp):
            score += max(0, len(child.values) - 1)
        elif isinstance(child, ast.comprehension):
            score += 1
    return score


def analyze_python_file(file_path):
    result = {'language': 'Python', 'classes': [], 'functions': [], 'imports': [], 'lines': 0, 'errors': []}
    try:
        source = read_file(file_path)
        result['lines'] = count_lines(source)
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                info = _node_info(node, 'class', source.splitlines())
                info['methods'] = [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                result['classes'].append(info)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                info = _node_info(node, 'function', source.splitlines())
                info['async'] = isinstance(node, ast.AsyncFunctionDef)
                info['complexity'] = _cyclomatic_python(node)
                result['functions'].append(info)
            elif isinstance(node, ast.Import):
                result['imports'].extend(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    result['imports'].append(node.module)
        result['imports'] = _unique(result['imports'])
    except SyntaxError as exc:
        result['errors'].append(f'Python syntax error at line {exc.lineno}: {exc.msg}')
    except Exception as exc:
        result['errors'].append(str(exc))
    return result


def _js_complexity(source):
    return 1 + len(re.findall(r'\b(if|for|while|case|catch)\b|&&|\|\|', source))


def analyze_javascript_file(file_path, language):
    result = {'language': language, 'classes': [], 'functions': [], 'imports': [], 'lines': 0, 'errors': []}
    try:
        source = read_file(file_path)
        lines = source.splitlines()
        result['lines'] = len(lines)
        for m in re.finditer(r'\bclass\s+([A-Za-z_$][\w$]*)', source):
            result['classes'].append({'name': m.group(1), 'line_start': source.count('\n', 0, m.start()) + 1, 'line_end': source.count('\n', 0, m.end()) + 1, 'kind': 'class'})
        functions = []
        patterns = [
            r'\bfunction\s+([A-Za-z_$][\w$]*)\s*\(',
            r'\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z_$][\w$]*)\s*=>',
            r'^\s*(?:async\s+)?([A-Za-z_$][\w$]*)\s*\([^;{}]*\)\s*\{',
        ]
        for pattern in patterns:
            for m in re.finditer(pattern, source, re.MULTILINE):
                functions.append({'name': m.group(1), 'line_start': source.count('\n', 0, m.start()) + 1, 'line_end': source.count('\n', 0, m.end()) + 1, 'kind': 'function', 'complexity': _js_complexity(m.group(0))})
        seen = set()
        result['functions'] = [x for x in functions if not (x['name'] in seen or seen.add(x['name']))]
        imports = re.findall(r'\bimport\s+(?:[^;]*?\s+from\s+)?[\'\"]([^\'\"]+)[\'\"]', source)
        imports += re.findall(r'\brequire\s*\(\s*[\'\"]([^\'\"]+)[\'\"]\s*\)', source)
        result['imports'] = _unique(imports)
    except Exception as exc:
        result['errors'].append(str(exc))
    return result


def analyze_html_file(file_path):
    result = {'language': 'HTML', 'classes': [], 'functions': [], 'imports': [], 'lines': 0, 'tags': [], 'scripts': [], 'stylesheets': [], 'errors': []}
    try:
        source = read_file(file_path)
        result['lines'] = count_lines(source)
        result['tags'] = sorted(set(re.findall(r'<\s*([a-zA-Z][\w-]*)', source)))
        result['scripts'] = _unique(re.findall(r'<script[^>]+src\s*=\s*[\'\"]([^\'\"]+)', source, re.I))
        result['stylesheets'] = _unique(re.findall(r'<link[^>]+href\s*=\s*[\'\"]([^\'\"]+)', source, re.I))
    except Exception as exc:
        result['errors'].append(str(exc))
    return result


def analyze_css_file(file_path, language):
    result = {'language': language, 'classes': [], 'functions': [], 'imports': [], 'lines': 0, 'selectors': [], 'errors': []}
    try:
        source = read_file(file_path)
        result['lines'] = count_lines(source)
        selectors = []
        for raw in re.findall(r'([^{}]+)\{', source):
            raw = raw.strip()
            if raw and not raw.startswith('@'):
                selectors.extend(x.strip() for x in raw.split(',') if x.strip())
        result['selectors'] = _unique(selectors)
        result['imports'] = _unique(re.findall(r'@import\s+[\'\"]([^\'\"]+)', source))
    except Exception as exc:
        result['errors'].append(str(exc))
    return result


def analyze_text_file(file_path, language):
    result = {'language': language, 'classes': [], 'functions': [], 'imports': [], 'lines': 0, 'errors': []}
    try:
        source = read_file(file_path)
        result['lines'] = count_lines(source)
        if language == 'JSON':
            try:
                result['json_keys'] = len(json.loads(source)) if isinstance(json.loads(source), dict) else 0
            except json.JSONDecodeError as exc:
                result['errors'].append(f'Invalid JSON: line {exc.lineno}')
    except Exception as exc:
        result['errors'].append(str(exc))
    return result


def analyze_generic_source_file(file_path, language):
    result = {'language': language, 'classes': [], 'functions': [], 'imports': [], 'lines': 0, 'errors': []}
    try:
        source = read_file(file_path)
        result['lines'] = count_lines(source)
        result['classes'] = [{'name': x, 'kind': 'class'} for x in _unique(re.findall(r'\b(?:class|interface|struct)\s+([A-Za-z_][A-Za-z0-9_]*)', source))]
        result['functions'] = [{'name': x, 'kind': 'function'} for x in _unique(re.findall(r'\b(?:function|def)\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(', source))]
        result['imports'] = _unique(re.findall(r'\b(?:import|include|using|require)\s*[<\"\']?([^>\"\'\s;]+)', source))
    except Exception as exc:
        result['errors'].append(str(exc))
    return result


def analyze_file(file_path):
    language = detect_language(file_path)
    base = {'file': file_path, 'language': language, 'classes': [], 'functions': [], 'imports': [], 'lines': 0, 'errors': []}
    if get_extension(file_path) in BINARY_EXTENSIONS or language == 'Pickle/Binary':
        return base
    if language == 'Python': result = analyze_python_file(file_path)
    elif language in ('JavaScript', 'TypeScript'): result = analyze_javascript_file(file_path, language)
    elif language == 'HTML': result = analyze_html_file(file_path)
    elif language in ('CSS', 'SCSS'): result = analyze_css_file(file_path, language)
    elif language in ('CSV', 'JSON', 'XML', 'YAML', 'Markdown', 'Text', 'Documentation', 'Git Configuration', 'Environment', 'Docker', 'Docker Configuration', 'Node.js Configuration', 'Node.js Lockfile', 'TOML', 'License', 'Makefile', 'Jenkins', 'Lockfile'):
        result = analyze_text_file(file_path, language)
    elif language != 'Unknown': result = analyze_generic_source_file(file_path, language)
    else:
        result = analyze_text_file(file_path, language) if os.path.getsize(file_path) < 2_000_000 else base
    result['file'] = file_path
    result.setdefault('errors', [])
    return result
