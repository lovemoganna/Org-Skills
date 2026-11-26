# V6.0 RC.1 · 代码高亮与正式输出清理

## 真实仓库状态

- 修复分支：`fix/html-design-lab-clean-release-highlight`，PR [#74](https://github.com/lovemoganna/Org-Skills/pull/74)。旧版基线来源仍可见 PR #73。
- 核心文件：`SKILL.md`、`scripts/generate.py`、`scripts/browser_review.py`、`tests/test_generator.py`、`references/`、`assets/v55-renderer.html` 和原始输入样例均已进入该分支。
- 独立 CI：`html-design-lab regression` [修复验证成功运行](https://github.com/lovemoganna/Org-Skills/actions/runs/38254207565)。
- 单元测试：14/14，通过（旧版 11 项，新增调试残留、恶意代码保真、正文“测试”词保留 3 项）。诗歌、Org 教程、Markdown 教程、真实质量报告由远端 checkout 后的生成器重新生成。
- Chromium 冒烟回归：四份输出全部通过，包含文档标题、章节数、30 种点击切换、页面溢出、外部依赖、JS 运行错误；另覆盖发布态无 V4.5 QA 面板，以及 SQL、Python、JavaScript、Shell 代码高亮、原文保真及恶意标记不执行。
- GitHub 原有 Skills Regression：通过。

## 仍未验证

1. 在 Windows/macOS 上直接通过 `file://` 打开生成 HTML。
2. Firefox 与正式 Safari 的功能及排版；Chromium `page.set_content()` 不能替代此证据。
3. 真人盲测与完整 WCAG 2.2 AA 审计。

## Loop 裁决

- G0/G1/G2/G4/G5：在已覆盖的输入、安全和 CI 范围内通过。
- G3：**有条件通过**（终端离线打开与浏览器矩阵缺边界证据）。
- G6：一个生成器入口、一个冻结渲染模板、参考契约及单元/浏览器检查均有明确代码归属。
- 这属于可复用的候选 Skill，不应描述成已全面完成跨浏览器正式验收。

本次最小修复已通过真实 GitHub Actions；同步版本元数据后须再次确认最终提交 CI 通过再合并。未直接访问用户浏览器中的本地文件，不能宣称 `file://` 或 Firefox、Safari 已覆盖。