# Causal Net Loop Work 盲评报告

**决定：`DO_NOT_PROMOTE`。PR #115 维持 Draft。** 两个 Work 子代理按冻结版本各回答 12 题，第三个子代理对匿名答案独立评分。用原脚本复算后，Candidate V2 在 10 个复杂任务中 **2 胜、2 负、6 平**。平均加权分从 93.75 降至 93.00。两臂均通过两道负对照，匿名评审未判定关键错误。

| 预注册门槛 | 实测 | 结果 |
| --- | --- | --- |
| 复杂任务至少 8 胜 | 2 胜 | 未达 |
| 复杂任务最多 1 负 | 2 负 | 未达 |
| 平均加权提升至少 5 分 | −0.75 分 | 未达 |
| 两臂无硬失败 | 0/24 | 通过 |
| 两臂 N11 和 N12 均通过 | 4/4 | 通过 |
| 复杂任务字符数比值中位数 ≤ 1.25 | 1.044 | 通过 |

复杂题总字符数为 2,207 → 2,357（+6.8%）。所有题总字符数为 2,256 → 2,401。字符数是输出长度代理指标。实际 token、模型延迟及服务端计费均为 `NOT_VERIFIED`。

## 逐题分数

| 题目 | Baseline | Candidate V2 | 分差 |
| --- | ---: | ---: | ---: |
| N01 制裁身份核对 | 92.5 | 92.5 | 0 |
| N02 提现冷静期 | 100 | 92.5 | −7.5 |
| N03 交易操纵核查 | 100 | 100 | 0 |
| N04 RFI 复审推翻 | 87.5 | 100 | +12.5 |
| N05 缓存与投诉 | 92.5 | 92.5 | 0 |
| N06 驱动与审计 | 100 | 100 | 0 |
| N07 导出故障预防 | 100 | 80 | −20 |
| N08 急诊等待 | 100 | 100 | 0 |
| N09 入城收费试点 | 65 | 72.5 | +7.5 |
| N10 晨读归因 | 100 | 100 | 0 |
| N11 必要条件 | 100 | 100 | 0 |
| N12 单句改写 | 100 | 100 | 0 |

- **N07 最大退步。** 候选详细设计了 CSV 回放，对权限和时区仅保留故障分类。基线为三类故障都给出了可执行回归和验收条件。
- **N02 退步。** 候选提出历史回放和可回退试点，缺少停止扩量的触发条件与解禁后的观察安排。基线同时给出分层随机对照、商户止损线与解禁后观察。
- **N04 与 N09 改善。** 候选在 N04 加入证据不足时触发复核的规则，并用正常样例验证放行。在 N09 加入持续超载或候车恶化时暂停试点的条件。
- **N09 口径冲突。** 题面只要求分析一条连锁影响。预注册的通过条件另强调周边道路分流或弱势群体成本与周边拥堵数据。两臂选择公交运力路径，评审依据预注册条件对两臂均扣分。锁分保留原判。

## 运行与证据边界

- 以 PR 起始提交 `4c114b27233abd3b04d6bff47f51de4fe3921a13` 运行冻结脚本。Baseline、Candidate V2 和案例集的 Git Blob SHA 均校验通过。两臂请求相同 Work 模型 `gpt-6.2-sol`、推理档位 `medium`，未调用 OpenAI API。角色用于解题和评分的工具配置为无，仅用本地读取投递输入。
- 三个原生子代理均设置 `fork_turns=none`。Work 返回的角色路径及答复发送者分别为 `/root/p7`、`/root/q3`、`/root/r8`，这些是本轮可见的线程标识。执行者各收到一个冻结 Skill 和相同的 N01–N12 题面，按同序一次交回。评审只获随机 A/B、题面、评分标准和模板。映射在评分锁定后才进入归档。
- 角色共享工作环境，隔离来自新线程及角色专属输入。每臂 12 项在同一线程的一次答复内生成。底层会话 UUID、可导出的服务端原始轨迹与模型版本证明均为 `NOT_VERIFIED`。本次用单个独立模型评审做一次比较，未测量评审间一致性或重复运行稳定性。

## 同一 PR 上的另一轮

发布前，PR 分支已新增另一轮实测。本轮归档至 `run-02/`。已用原评分脚本复算[另一轮报告](../REPORT.md)的结果，逐字匹配其 `result.json`。另一轮为 1 胜、3 负、6 平，均分差 −5.75。两轮都未过晋升门槛，N07 都是候选落后，其余单题胜负与输出长度变化有波动。两轮沿用同一个题集，不能作为 20 道独立复杂题汇总。

## 复核

[运行配置与证据边界](evidence/work-runtime.json) · [两臂原始答复一](evidence/p7-final.txt) · [两臂原始答复二](evidence/q3-final.txt) · [24 个回答文件](outputs/) · [评审原始答复](evidence/r8-final.json) · [匿名评审包](blind/review.json) · [锁定评分](blind/locked-scores.json) · [解盲映射](blind/key.json) · [逐题复算结果](result.json) · [评分日志](evidence/score.log) · [文件校验清单](SHA256SUMS)

从 PR 分支仓库根目录执行以下命令。需保留冻结基线提交对象。

```bash
run=skills/causal-net-loop/evals/runs/work-2026-11-18/run-02
python skills/causal-net-loop/evals/blind12.py check
( cd "$run" && sha256sum -c SHA256SUMS )
python skills/causal-net-loop/evals/blind12.py verify --source "$run/outputs"
python skills/causal-net-loop/evals/blind12.py score --source "$run/outputs" \
  --review "$run/blind/locked-scores.json" --key "$run/blind/key.json" \
  --out /tmp/causal-work115-recomputed.json
cmp "$run/result.json" /tmp/causal-work115-recomputed.json
```
