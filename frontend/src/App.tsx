import { useMemo, useState } from "react";
import "./style.css";

interface SymbolInfo {
  name: string;
  line_start?: number;
  line_end?: number;
  lines?: number;
  complexity?: number;
  methods?: string[];
  async?: boolean;
  kind?: string;
}

interface FileAnalysis {
  file: string;
  language: string;
  classes: SymbolInfo[];
  functions: SymbolInfo[];
  imports: string[];
  lines: number;
  tags?: string[];
  scripts?: string[];
  stylesheets?: string[];
  selectors?: string[];
  errors?: string[];
}

interface AnalysisResult {
  repository?: string;
  github_url?: string;
  total_files: number;
  total_lines: number;
  total_classes: number;
  total_functions: number;
  total_imports: number;
  languages: Record<string, number>;
  technology_stack?: string[];
  analysis_errors?: number;
  onboarding?: { first_steps: string[]; summary: string; technology_stack: string[] };
  files: FileAnalysis[];
}

const API_BASE = "http://127.0.0.1:8000";

function fileName(path: string) {
  return path.replace(/\\/g, "/").split("/").pop() || path;
}

function complexityLabel(value?: number) {
  if (!value) return "—";
  if (value <= 5) return "Low";
  if (value <= 10) return "Medium";
  return "High";
}

function App() {
  const [githubUrl, setGithubUrl] = useState("");
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [activePage, setActivePage] = useState<"dashboard" | "repositories" | "about">("dashboard");
  const [search, setSearch] = useState("");
  const [languageFilter, setLanguageFilter] = useState("All");
  const [selectedFile, setSelectedFile] = useState<FileAnalysis | null>(null);

  const analyzeRepository = async () => {
    const url = githubUrl.trim();
    setError("");
    if (!url) return setError("Please enter a GitHub repository URL.");
    if (!/^https?:\/\/(www\.)?github\.com\/[^/]+\/[^/]+/.test(url)) {
      return setError("Enter a valid public GitHub repository URL, for example https://github.com/user/repository");
    }
    setLoading(true);
    setResult(null);
    try {
      const response = await fetch(`${API_BASE}/repository/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ github_url: url }),
      });
      const data = await response.json().catch(() => null);
      if (!response.ok) throw new Error(data?.detail || `Backend error (${response.status})`);
      if (!data?.files || typeof data.total_files !== "number") throw new Error("The analyzer returned an incomplete response.");
      setResult(data);
      setActivePage("dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to analyze the repository.");
    } finally {
      setLoading(false);
    }
  };

  const filteredFiles = useMemo(() => {
    if (!result) return [];
    const q = search.toLowerCase().trim();
    return result.files.filter((f) => {
      const matchesSearch = !q || f.file.toLowerCase().includes(q) || f.functions.some(x => x.name.toLowerCase().includes(q)) || f.classes.some(x => x.name.toLowerCase().includes(q));
      const matchesLanguage = languageFilter === "All" || f.language === languageFilter;
      return matchesSearch && matchesLanguage;
    });
  }, [result, search, languageFilter]);

  const allFunctions = result?.files.flatMap(f => f.functions.map(fn => ({ ...fn, file: f.file, language: f.language }))) || [];
  const allClasses = result?.files.flatMap(f => f.classes.map(c => ({ ...c, file: f.file, language: f.language }))) || [];
  const allImports = result ? [...new Set(result.files.flatMap(f => f.imports))] : [];
  const languages = result ? Object.entries(result.languages).sort((a, b) => b[1] - a[1]) : [];

  const newAnalysis = () => {
    setResult(null); setGithubUrl(""); setError(""); setSearch(""); setLanguageFilter("All"); setSelectedFile(null); setActivePage("dashboard");
  };

  const renderHome = () => {
    if (result) return renderResults();
    return (
      <section className="hero">
        <div className="eyebrow">CODEBASE INTELLIGENCE</div>
        <h1>Understand Any Codebase</h1>
        <p>Analyze a GitHub repository and turn an unfamiliar codebase into a clear technical map for developers and teams.</p>
        <div className="repository-box">
          <input value={githubUrl} disabled={loading} onChange={e => setGithubUrl(e.target.value)} onKeyDown={e => e.key === "Enter" && analyzeRepository()} placeholder="https://github.com/user/repository" />
          <button onClick={analyzeRepository} disabled={loading}>{loading ? "Analyzing…" : "Analyze Repository"}</button>
        </div>
        {loading && <div className="loading-box"><span className="spinner" /><div><strong>Analyzing repository</strong><p>Cloning, scanning source files and extracting code structure.</p></div></div>}
        {error && <div className="error-box"><strong>Analysis failed</strong><p>{error}</p><button className="link-button" onClick={() => setError("")}>Dismiss</button></div>}
        <div className="capability-grid">
          <div><b>01</b><strong>Repository mapping</strong><span>Files, languages and technology stack.</span></div>
          <div><b>02</b><strong>Code structure</strong><span>Classes, functions, imports and complexity.</span></div>
          <div><b>03</b><strong>Onboarding guide</strong><span>Find the best files to read first.</span></div>
        </div>
      </section>
    );
  };

  const renderResults = () => {
    if (!result) return null;
    const maxLang = Math.max(...languages.map(([, n]) => n), 1);
    return (
      <section className="results">
        <div className="repository-header">
          <div><div className="small-label">ANALYZED REPOSITORY</div><h1>{result.repository || "Repository"}</h1><a href={result.github_url} target="_blank" rel="noreferrer">{result.github_url}</a></div>
          <button className="secondary-button" onClick={newAnalysis}>+ New Analysis</button>
        </div>

        <div className="stats">
          {[["📁", result.total_files, "Files"], ["📝", result.total_lines, "Lines"], ["◈", result.total_classes, "Classes"], ["ƒ", result.total_functions, "Functions"], ["↗", result.total_imports, "Imports"]].map(([icon, value, label]) => <div className="stat-card" key={String(label)}><div className="stat-icon">{icon}</div><div className="stat-number">{Number(value).toLocaleString()}</div><div className="stat-label">{label}</div></div>)}
        </div>

        <div className="insight-grid">
          <div className="panel"><div className="panel-heading"><div><h2>Technology Stack</h2><p>Detected from repository files and dependencies.</p></div></div><div className="tags">{(result.technology_stack || []).map(x => <span className="tag tech-tag" key={x}>{x}</span>)}</div></div>
          <div className="panel onboarding"><h2>Developer Onboarding</h2><p>{result.onboarding?.summary}</p><ol>{(result.onboarding?.first_steps || []).slice(0, 5).map(x => <li key={x}><code>{x}</code></li>)}</ol></div>
        </div>

        <div className="panel"><div className="panel-heading"><div><h2>Languages</h2><p>File distribution across the repository.</p></div></div><div className="language-list">{languages.map(([language, count]) => <div className="language-item" key={language}><div className="language-info"><b>{language}</b><span>{count} file{count !== 1 ? "s" : ""}</span></div><div className="progress"><div className="progress-bar" style={{ width: `${Math.max(3, (count / maxLang) * 100)}%` }} /></div></div>)}</div></div>

        <div className="panel"><div className="panel-heading"><div><h2>Repository Explorer</h2><p>Search files and inspect their symbols without opening the repository manually.</p></div><span className="count-badge">{filteredFiles.length} / {result.files.length}</span></div><div className="filters"><input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search files, functions or classes…" /><select value={languageFilter} onChange={e => setLanguageFilter(e.target.value)}><option>All</option>{languages.map(([l]) => <option key={l}>{l}</option>)}</select></div><div className="file-list">{filteredFiles.map(file => <button className="file-card" key={file.file} onClick={() => setSelectedFile(file)}><div className="file-main"><div className="file-icon">{file.language === "Python" ? "PY" : file.language === "TypeScript" ? "TS" : "<>"}</div><div><div className="file-name">{fileName(file.file)}</div><div className="file-path">{file.file}</div></div></div><div className="file-meta"><span className="language-badge">{file.language}</span><span>{file.lines} lines</span><span>{file.functions.length} fn</span><span>{file.classes.length} cls</span></div></button>)}{filteredFiles.length === 0 && <div className="empty">No files match your filters.</div>}</div></div>

        <div className="insight-grid">
          <div className="panel"><h2>Functions</h2><p className="panel-description">Functions and methods discovered by the analyzer.</p><div className="symbol-list">{allFunctions.slice(0, 80).map((fn, i) => <button className="symbol-row" key={`${fn.file}-${fn.name}-${i}`} onClick={() => setSelectedFile(result.files.find(f => f.file === fn.file) || null)}><code>{fn.name}()</code><span>{fileName(fn.file)} · line {fn.line_start || "—"} · {complexityLabel(fn.complexity)}</span></button>)}</div>{allFunctions.length > 80 && <p className="muted">Showing first 80 of {allFunctions.length} functions.</p>}</div>
          <div className="panel"><h2>Classes</h2><p className="panel-description">Classes, interfaces and their methods.</p><div className="symbol-list">{allClasses.slice(0, 50).map((c, i) => <button className="symbol-row" key={`${c.file}-${c.name}-${i}`} onClick={() => setSelectedFile(result.files.find(f => f.file === c.file) || null)}><code>{c.name}</code><span>{fileName(c.file)} · line {c.line_start || "—"}</span></button>)}</div>{allClasses.length === 0 && <div className="empty">No classes detected.</div>}</div>
        </div>

        <div className="panel"><h2>Imports & Dependencies</h2><p className="panel-description">Unique libraries and modules detected in source code.</p><div className="tags">{allImports.map(item => <span className="tag import-tag" key={item}>{item}</span>)}</div>{allImports.length === 0 && <div className="empty">No imports detected.</div>}</div>

        {selectedFile && <div className="modal-backdrop" onClick={() => setSelectedFile(null)}><div className="modal" onClick={e => e.stopPropagation()}><button className="modal-close" onClick={() => setSelectedFile(null)}>×</button><div className="small-label">FILE DETAILS</div><h2>{fileName(selectedFile.file)}</h2><code className="modal-path">{selectedFile.file}</code><div className="detail-grid"><div><b>Language</b><span>{selectedFile.language}</span></div><div><b>Lines</b><span>{selectedFile.lines}</span></div><div><b>Classes</b><span>{selectedFile.classes.length}</span></div><div><b>Functions</b><span>{selectedFile.functions.length}</span></div><div><b>Imports</b><span>{selectedFile.imports.length}</span></div></div><h3>Functions</h3><div className="tags">{selectedFile.functions.map((fn, i) => <span className="tag function-tag" key={`${fn.name}-${i}`}>{fn.name} · L{fn.line_start || "?"}</span>)}</div><h3>Classes</h3><div className="tags">{selectedFile.classes.map((c, i) => <span className="tag class-tag" key={`${c.name}-${i}`}>{c.name}</span>)}</div><h3>Imports</h3><div className="tags">{selectedFile.imports.map(x => <span className="tag import-tag" key={x}>{x}</span>)}</div></div></div>}
      </section>
    );
  };

  const renderRepositories = () => <section className="page"><div className="page-header"><div className="page-icon">⌘</div><div><h1>Repositories</h1><p>Start a fresh analysis of any public GitHub repository.</p></div></div><div className="repository-card"><h2>Analyze Repository</h2><p>CodeLens clones the repository, scans supported files and builds a codebase map.</p><div className="repository-box"><input value={githubUrl} disabled={loading} onChange={e => setGithubUrl(e.target.value)} onKeyDown={e => e.key === "Enter" && analyzeRepository()} placeholder="https://github.com/user/repository" /><button onClick={analyzeRepository} disabled={loading}>{loading ? "Analyzing…" : "Analyze"}</button></div>{error && <div className="error-box"><strong>Analysis failed</strong><p>{error}</p></div>}</div></section>;

  const renderAbout = () => <section className="page"><div className="about-card"><div className="about-logo">CodeLens</div><h1>Codebase Intelligence for Developers</h1><p>CodeLens is being built as a developer onboarding platform: give it a repository and it explains the project's structure, technologies, symbols and recommended starting points.</p><div className="feature-grid"><div className="feature"><b>01</b><h3>Static Analysis</h3><p>AST and source analysis for files, classes, functions and imports.</p></div><div className="feature"><b>02</b><h3>Architecture</h3><p>Repository structure and dependency relationships.</p></div><div className="feature"><b>03</b><h3>Onboarding</h3><p>Prioritized files and an understandable technical map.</p></div><div className="feature"><b>04</b><h3>AI Layer</h3><p>Planned Ollama/Qwen explanations on top of verified analysis data.</p></div></div></div></section>;

  return <div className="app"><header className="navbar"><button className="logo" onClick={() => setActivePage("dashboard")}>CodeLens</button><nav><button className={activePage === "dashboard" ? "nav-button active" : "nav-button"} onClick={() => setActivePage("dashboard")}>Dashboard</button><button className={activePage === "repositories" ? "nav-button active" : "nav-button"} onClick={() => setActivePage("repositories")}>Repositories</button><button className={activePage === "about" ? "nav-button active" : "nav-button"} onClick={() => setActivePage("about")}>About</button></nav></header><main className="container">{activePage === "dashboard" && renderHome()}{activePage === "repositories" && renderRepositories()}{activePage === "about" && renderAbout()}</main><footer><span>CodeLens</span><span>Codebase Intelligence · Developer Onboarding</span></footer></div>;
}

export default App;
