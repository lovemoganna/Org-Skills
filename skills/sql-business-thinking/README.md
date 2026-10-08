# sql-business-thinking

训练路径：

陌生多表或完整自主分析先执行：业务语义还原 → 本体原子知识库 → 本体识别规则库。简单单题保持快速通道。

```text
业务语言 → 数据逻辑 → SQL → 验证 → 可复述结论
```

## 入口

- [`SKILL.md`](SKILL.md)：主协议与路由。
- [`references/dataset-planning.md`](references/dataset-planning.md)：陌生数据集勘察、时间维表、JOIN 基数与分析地图。
- [`references/ontology-analysis.md`](references/ontology-analysis.md)：本体前置、业务模式、分析信号与局部展开。
- [`references/debug-stages.md`](references/debug-stages.md)：开发调试用逻辑阶段、状态记录、锁定、回退、重跑和完整回归；阶段边界不代表最终工程拆分方式。
- [`references/protocol.md`](references/protocol.md)：判级、暂停、账本、代码增长、复盘。
- [`references/dialogue-rendering.md`](references/dialogue-rendering.md)：人物角色绑定、协作推演与 Code-in-Conversation。
- [`references/report-rendering.md`](references/report-rendering.md)：ReportSpec、HTML/DuckDB-Wasm 与渲染验收。
- [`references/regression-loop.md`](references/regression-loop.md)：扫描 → 修正 → 自检 → 再修正闭环。
- [`references/skill-change-log.md`](references/skill-change-log.md)：已沉淀的缺陷与泛化规则。

## 回归

- [`tests/regression-cases.md`](tests/regression-cases.md)：原失败样本、历史通过样本和新增泛化样本。
- [`tests/check_repo.py`](tests/check_repo.py)：仓库结构与引用完整性检查。

维护时必须先读取仓库当前版本，再做最小 Diff；不要从聊天附件覆盖仓库 HEAD。

## 测试资产维护

| 分类 | 保留依据 | 维护原则 |
|---|---|---|
| 执行必需 | `SKILL.md`、`references/`、`tests/mandatory-gates.json`、远程 Runner | 保留；变动必须验证引用和执行契约。 |
| 核心回归 | `tests/check_repo.py`、`tests/check_d*.py`、`tests/check_native_contract.py`、`tests/check_delivery_handoff.py`、`tests/d23_rendered_qa.mjs` | 每项验证不同阶段或边界；统一从既有入口执行，禁止因表面重复删检查。 |
| 历史缺陷证据 | `tests/regression-cases.md`、`tests/audits/`、`tests/verified-*`、`tests/d10-fiat-direction-status.sql`、`artifacts/verified-d22-report.html`、`tests/render-qa-fixture.html` | 保留固定样本、版本与哈希，可复现历史故障。不得以历史 PASS 冒充当前 E2E。 |
| 临时产物 | CI 生成的 `d02.sql`、`d03.sql`、`holdout.xlsx`、`render-output/`、缓存、截图等 | 不纳入版本控制，见仓库根 `.gitignore`；正式测试证据由 Actions Artifacts 保存。 |

仓库清理基线（2026-10-08）：本 Skill 原有 37 个受控文件，未发现可以证明无用、可安全删除的测试文件。相同的 `check_native_contract.py` 被多个工作流复用，是独立运行保护，不属于重复资产；暂不合并删除。历史审计仅说明当时通过的范围。确认引用关系、独立覆盖及可复现性后才能删除或合并文件。

## 默认 HTML 交付

完整分析报告默认写入 `/mnt/data/sql_business_thinking_report.html`，并在最终回复提供可点击下载链接；用户显式指定其他路径时覆盖默认值。
