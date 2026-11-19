# Causal Net Loop｜跨领域测试与候选优化总结（2026-11-17）

## 结论
- **代码静态门禁：PASS**。GitHub Actions 在 Candidate 版本执行原生 Python 检查，具体执行结果见下方。
- **归档回放与结构检查：PASS（限 smoke test）**。H1–H6 三套答复均完整，T10 负例可观察；V2 比 V1 压缩 **32.1%**；比 Baseline 字符数减少 **11.9%**。
- **真实质量优于正式版：NOT_VERIFIED**。三套答复由同一 GPT-6 会话和执行者提供；并非模型隔离运行、独立盲评，不能把文本长度或自查结果冒充统计显著的能力提升。
- **状态**：PR #115 继续保留 Draft；本轮不合并 main。

## 冻结版本与证据链

| 标的 | Blob SHA | 原始记录 |
| --- | --- | --- |
| Baseline Skill（main） | `893b581a23fc2474d6d4fad761ecb4d2965c163c` | `2026-11-17-cross-domain-baseline-raw.md` |
| Candidate V1 | `44156432c3f821d51e897fe8584824ba26562df7` | `2026-11-17-cross-domain-candidate-raw.md` |
| Candidate V2 | `57581f87ba669cffe1900ad0b199a9fd24b0e6f6` | `2026-11-17-cross-domain-v2-raw.md` |

- 预注册场景和门禁：`../heldout-2026-11-17-cross-domain.md`（H1 电商、H2 SRE、H3 AML、H4 求职、H5 教育、H6 简单问答）。
- V1 第一次发现的具体缺陷与审计：`2026-11-17-cross-domain-v1-audit.md`。
- V2 新增的 T10 是后补开发集负例，**不计入原 H1–H6 held-out**。
- 机械复算工具：`../compare_smoke.py`；只复算章节、字符长度和少量负例关键词，**不替代语义审查或独立模型运行**。

## 逐题结果（正文 Unicode 字符数）

| 案例 | Baseline | Candidate V1 | Candidate V2 | V2 保留价值 / 可见问题 |
| --- | ---: | ---: | ---: | --- |
| H1 电商退款入口 | 162 | 221 | 128 | 保留错误 KPI 纠正、可逆实验、潜在后果边界 |
| H2 SRE 三次超时 | 175 | 242 | 150 | 保留相似症状与不同机制的区分、分故障复发预防 |
| H3 AML 告警阈值 | 174 | 221 | 149 | 拒绝把告警下降等同风险下降；删除硬凑三阶因果 |
| H4 求职漏斗 | 134 | 119 | 119 | 单动作、不启动复杂模块 |
| H5 教育迁移 | 170 | 267 | 166 | 保留测量反证、迁移对照、跨批验收 |
| H6 简单概念 | 47 | 47 | 47 | 负对照保持不变 |
| **总计** | **862** | **1117** | **759** | **V2 相比 V1 -32.1%** |

这些长度是本次生成的文本体量，不是输出 token 价格、耗时或者真实模型质量的客观指标。六题对照均为预注册输入，但三个版本不是独立采样。

## 真实 CI 检查

- **Causal Net Loop Contract**：<https://github.com/lovemoganna/Org-Skills/actions/runs/44079751260>，PASS；具体包含：
  - `python skills/causal-net-loop/tests/check_contract.py`（原生 Python，T1–T10，主干、触发、传导和表达预算合同校验）。
  - `python skills/causal-net-loop/evals/compare_smoke.py`（原生 Python，对归档的三版答复复算章节和长度）。
- **Skills Regression**：<https://github.com/lovemoganna/Org-Skills/actions/runs/44079427545>，PASS（此前 HEAD）；本轮最终 HEAD 需以 GitHub 最新工作流为准。
- 新工作流 `.github/workflows/causal-net-loop-contract.yml` 对后续 PR / main 下的相关文件变更执行无模型 API 的静态回归；不是自动 LLM 质量测试。

## 质量风险与晋升门槛

- 结构正确不等于因果判断正确；真实任务质量、独立评分者复评、模型重复运行方差、真实 token/延迟、生产效果仍为 `NOT_VERIFIED`。
- 在当前无需模型 API 的约束下，不能合法地凭空生成隔离的 GPT-6 模型会话记录或给出独立盲评成绩。
- 后续要决定合并：冻结同一证据包，真实隔离运行 Baseline 和 Candidate V2；保存两份原始同题输出与工具配置，独立评审错误、关键反证、误报与成本，复测 H4/H6/T10 负例。完成之前 **保持 Draft / 不自动晋升**。

**结果：完成候选优化、预注册跨领域 smoke test、原始产物留存、原生 CI 与失败回归修正；严格 A/B、质量胜出尚未证实。**
