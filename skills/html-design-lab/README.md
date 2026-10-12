# HTML Design Lab · V6.0 Candidate

**将 Markdown / Org Mode / DocumentSpec JSON 生成离线可用的单文件 HTML。** 内置 30 种视觉风格和 30 套构图，支持主题切换、章节目录、JSON 导入导出、复制、代码展示、数据表格及已提供的注释。无需网页服务器或 CDN。

## 立即使用

在本目录运行：

```sh
python3 scripts/generate.py --input examples/poem.document.json --output poem.html
python3 scripts/generate.py --input examples/tutorial.md --kind tutorial --output sql.html --style terminal
python3 scripts/generate.py --input examples/tutorial.org --kind tutorial --output org-tutorial.html
python3 scripts/generate.py --input examples/real-loop-review.md --kind report --output report.html --style saas
```

然后用浏览器打开生成的 HTML。初始风格可通过 `--style` 设定，打开网页后仍能自由切换 30 种风格。

生成器只依赖 Python 标准库。自动浏览器 QA 可选依赖 Playwright 和 Chromium，未安装时可以运行纯单元测试。

```sh
python3 -m unittest discover -s tests -v
python3 scripts/browser_review.py --html poem.html --out poem-smoke.json
```

## 输入限制

Markdown/Org 是明确子集解析器，不是全规格编译器。需要高保真排版、人工今译或关联批注时请传入 `DocumentSpec` JSON；需要执行 Org Babel、复杂嵌入资源或数学公式时不能直接声明支持。详细规则在 `references/document-contract.md`，最新 30 风格 ID 在 `references/styles.md`。

## 质量边界

V6.0 是具备实际生成、校验和测试能力的**候选 Skill**，并非已安装到任何 GitHub 仓库或插件的版本。Chromium `page.set_content()` 的通过不能替代 Chrome / Firefox / Safari 的 `file://` 实机兼容性认证。内置 SQL 仅展示/复制，**不执行 SQL**。

## 文件职责

- `SKILL.md`：Agent 执行契约
- `assets/v55-renderer.html`：冻结的 30 风格渲染基线
- `scripts/generate.py`：唯一 HTML 生成入口
- `scripts/browser_review.py`：浏览器边界冒烟测试
- `references/`：内容协议、风格目录、Loop 质量门禁
- `tests/`：结构、反例、安全、保真测试
- `examples/`：源文档实例和演示输入
- `output/`：独立生成的验证样例及其证据
