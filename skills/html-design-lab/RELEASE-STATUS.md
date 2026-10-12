# V6.0 RC 发布状态：未完成

本分支仅用于审查，不能合并，也不能标为正式版。

已核对提交的 `SKILL.md`、`README.md` 和 `assets/v55-renderer.html` 的原始 Git Blob SHA。已提供三种从生成页提取的 DocumentSpec 用例。

## 阻塞项

- `scripts/generate.py` 和 `scripts/browser_review.py` 尚未写入 GitHub。
- `tests/test_generator.py`、完整 `references/` 与原始输入样例尚未写入 GitHub。
- 本地归档中运行的 11/11 单测不能代替远端 checkout 后重新执行。

本轮遵循 `loop-engineering-meta` 的 G3/G5 门禁：不得因为本地成功或只有规范文件，就宣称远端 Skill 可运行。

## 下一步

将本地 V6.0 RC 归档中缺失的原文件提交至分支；核对 SHA-256；从分支独立重新生成诗歌、Markdown/Org 教程和真实报告，运行单测及浏览器回归；通过后才考虑合并至 main。
