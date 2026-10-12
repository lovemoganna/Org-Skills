# HTML Design Lab · V6.0 Candidate

**将 Markdown / Org Mode / DocumentSpec JSON 生成可离线阅读的单文件 HTML。** 内置 30 种视觉风格、30 套构图，支持主题切换、章节目录、JSON 导入导出、代码块、表格、复制及输入提供的批注。生成网页不依赖 CDN。

## 立即使用

在 `skills/html-design-lab/` 目录执行：

```sh
python3 scripts/generate.py --input examples/poem.document.json --output poem.html
python3 scripts/generate.py --input examples/tutorial.md --kind tutorial --output sql.html --style terminal
python3 scripts/generate.py --input examples/tutorial.org --kind tutorial --output org-tutorial.html
python3 scripts/generate.py --input examples/real-loop-review.md --kind report --output report.html --style saas
```

打开生成的 HTML 即可阅读，支持在页面内切换 30 种风格。指定 `--style` 只改变初始风格，不锁定选择。

生成器依赖 Python 3.10+ 标准库。浏览器 QA 另需 Playwright 和 Chromium；GitHub Actions 工作流包含自动安装步骤。

```sh
python3 -m unittest discover -s tests -v
python3 scripts/browser_review.py --html poem.html --out poem-smoke.json
```

## 输入边界

Markdown/Org 只支持明确子集，**不支持执行 Org Babel/SQL**。严格保留字词、对照今译或特定注释，请使用 DocumentSpec JSON；不认识的内容不能默默删除。详见 `references/document-contract.md`、`references/styles.md`。

## 发布及测试边界

源码已经提交到 `lovemoganna/Org-Skills` 的候选分支，详见 [PR #73](https://github.com/lovemoganna/Org-Skills/pull/73)。是否在其他 Agent 运行时自动加载，取决于该环境是否读取并安装了这个 Skill；GitHub 合并本身不等于插件安装。

当前独立仓库回归使用 GitHub Actions 上的 Chromium `page.set_content()`。这验证已覆盖的生成与交互，不证明本地 `file://`、Firefox、正式 Safari 或完整无障碍审计全部通过。风控样例均为明示的虚构演示内容。

## 目录说明

- `SKILL.md`：Skill 触发条件、约束与执行流程
- `assets/v55-renderer.html`：冻结的 30 风格内联渲染器
- `scripts/generate.py`：唯一生成入口
- `scripts/browser_review.py`：Chromium QA
- `references/`：输入规范、风格索引与 Loop 验收契约
- `tests/`：纯 Python 单元测试
- `examples/`：可复查的输入样例
- `.github/workflows/html-design-lab-regression.yml`：仓库 CI 生成与浏览器回归

仓库不提交大量生成样例 HTML；CI 生成临时文件并归档 JSON 验收记录。