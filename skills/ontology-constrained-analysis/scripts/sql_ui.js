/* Self-contained SQL formatting, syntax highlighting, and copy for single HTML reports.
   Presentation only: never replace executed SQL with formatted SQL. */
(function (root) {
  'use strict';
  const KEYWORDS = new Set('SELECT FROM WHERE GROUP BY ORDER HAVING LIMIT OFFSET JOIN LEFT RIGHT INNER FULL OUTER CROSS ON WITH AS UNION ALL DISTINCT CASE WHEN THEN ELSE END AND OR NOT IN IS NULL TRUE FALSE INSTALL LOAD CREATE TEMP TABLE COPY COUNT SUM AVG MIN MAX OVER PARTITION ROWS BETWEEN DESC ASC CAST FILTER QUALIFY'.split(' '));
  const BREAK_BEFORE = new Set('SELECT FROM WHERE GROUP ORDER HAVING LIMIT OFFSET JOIN LEFT RIGHT INNER FULL CROSS WITH UNION QUALIFY'.split(' '));
  function tokens(value) {
    return String(value).replace(/\r\n?/g, '\n').match(/--[^\n]*|\/\*[\s\S]*?\*\/|'(?:''|[^'])*'|"(?:\"\"|[^"])*"|[A-Za-z_][\w$]*|\d+(?:\.\d+)?|>=|<=|<>|!=|::|->>|->|[^\s]/g) || [];
  }
  function formatSQL(source) {
    const parts = tokens(source);
    let out = '', depth = 0, last = '';
    const stack = [];
    const trim = () => { out = out.replace(/[ \t]+$/g, ''); };
    const line = (level = depth) => {
      trim();
      if (out && !out.endsWith('\n')) out += '\n';
      if (out) out += '  '.repeat(Math.max(0, level));
    };
    const word = value => {
      if (out && !/[\s(.]$/.test(out) && last !== '.' && last !== '::') out += ' ';
      out += value;
    };
    for (let i = 0; i < parts.length; i++) {
      const raw = parts[i], upper = raw.toUpperCase(), prev = last.toUpperCase();
      if (raw.startsWith('--') || raw.startsWith('/*')) {
        if (out && !/\s$/.test(out)) out += ' ';
        out += raw;
        line();
      } else if (raw === '(') {
        const expanded = prev === 'READ_XLSX';
        if (out && (['AS', 'IN', 'VALUES'].includes(prev) || (!/[\s(.]$/.test(out) && !/^[A-Za-z_\d'"]/.test(last)))) out += ' ';
        out += '(';
        stack.push(expanded); depth++;
        if (expanded) line();
      } else if (raw === ')') {
        const expanded = stack.pop() || false;
        depth = Math.max(0, depth - 1);
        if (expanded) line(depth); else trim();
        out += ')';
      } else if (raw === ',') {
        trim(); out += ',';
        if (stack[stack.length - 1]) line();
      } else if (raw === ';') {
        trim(); out += ';'; line(0);
      } else if (raw === '.' || raw === '::') {
        trim(); out += raw;
      } else if (BREAK_BEFORE.has(upper) && i > 0 && prev !== '.' &&
                 (depth === 0 || upper === 'SELECT' || stack[stack.length - 1] === false)) {
        line(depth); word(upper);
      } else if (KEYWORDS.has(upper)) {
        word(upper);
      } else {
        word(raw);
      }
      last = raw;
    }
    return out.trim();
  }
  const escapeHTML = value => String(value).replace(/&/g, '&amp;')
    .replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  function highlightSQL(formatted) {
    const re = /--[^\n]*|\/\*[\s\S]*?\*\/|'(?:''|[^'])*'|"(?:""|[^"])*"|[A-Za-z_][\w$]*|\d+(?:\.\d+)?/g;
    let lastIndex = 0, result = '', match;
    while ((match = re.exec(formatted))) {
      result += escapeHTML(formatted.slice(lastIndex, match.index));
      const t = match[0];
      let cls = '';
      if (/^(?:--|\/\*)/.test(t)) cls = 'sql-comment';
      else if (/^['"]/.test(t)) cls = 'sql-string';
      else if (KEYWORDS.has(t.toUpperCase())) cls = 'sql-keyword';
      else if (/^\d+(?:\.\d+)?$/.test(t)) cls = 'sql-number';
      result += cls ? '<span class="' + cls + '">' + escapeHTML(t) + '</span>' : escapeHTML(t);
      lastIndex = re.lastIndex;
    }
    return result + escapeHTML(formatted.slice(lastIndex));
  }
  function renderSqlBlock(mount, sql) {
    const formatted = formatSQL(sql);
    mount.replaceChildren();
    const shell = document.createElement('div');
    shell.className = 'sql-shell';
    const bar = document.createElement('div');
    bar.className = 'sql-toolbar';
    const label = document.createElement('span');
    label.textContent = 'SQL · DuckDB';
    const copy = document.createElement('button');
    copy.type = 'button'; copy.textContent = '复制 SQL';
    const pre = document.createElement('pre');
    const code = document.createElement('code');
    code.className = 'language-sql';
    code.innerHTML = highlightSQL(formatted);
    copy.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(formatted);
        copy.textContent = '已复制';
      } catch (error) {
        copy.textContent = '复制失败';
        copy.title = String(error);
      }
    });
    pre.appendChild(code); bar.append(label, copy);
    shell.append(bar, pre); mount.appendChild(shell);
    return {formatted, code, copy};
  }
  const API = {tokens, formatSQL, highlightSQL, renderSqlBlock};
  if (typeof module !== 'undefined' && module.exports) module.exports = API;
  root.OntologySQL = API;
})(typeof window !== 'undefined' ? window : globalThis);
