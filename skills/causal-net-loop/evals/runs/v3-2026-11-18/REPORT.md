# 因果 Skill V3 实测报告

**保留 Baseline，V3 不晋升。** 六道开发回归通过。随后以一条新规则对照冻结 Baseline，完成 12 道新题的双臂实跑和 24 条独立匿名评分。复杂题 V3 **4 胜、0 负、6 平**，均分 **99.00/100**，Baseline 为 **95.50/100**。

| 预注册门槛 | 实测 | 判定 |
| --- | --- | --- |
| 复杂题至少 8 胜、最多 1 负 | 4 胜、0 负、6 平 | 未通过 |
| 复杂题平均提升至少 5 分 | +3.50 分 | 未通过 |
| 两臂均无硬失败 | 0/24 条触发硬失败 | 通过 |
| 两臂各通过两道负对照 | 4/4 条通过 | 通过 |
| 复杂题字符数比值中位数 ≤ 1.25 | 1.106 | 通过 |

## 分题结果

| 题目 | Baseline | V3 | 分差 |
| --- | ---: | ---: | ---: |
| [N01](outputs/candidate/N01.json) | 100 | 100 | +0 |
| [N02](outputs/candidate/N02.json) | 82.5 | 90 | +7.5 |
| [N03](outputs/candidate/N03.json) | 100 | 100 | +0 |
| [N04](outputs/candidate/N04.json) | 92.5 | 100 | +7.5 |
| [N05](outputs/candidate/N05.json) | 100 | 100 | +0 |
| [N06](outputs/candidate/N06.json) | 100 | 100 | +0 |
| [N07](outputs/candidate/N07.json) | 92.5 | 100 | +7.5 |
| [N08](outputs/candidate/N08.json) | 100 | 100 | +0 |
| [N09](outputs/candidate/N09.json) | 87.5 | 100 | +12.5 |
| [N10](outputs/candidate/N10.json) | 100 | 100 | +0 |
| [N11](outputs/candidate/N11.json) | 55 | 55 | +0 |
| [N12](outputs/candidate/N12.json) | 55 | 55 | +0 |

复杂题累计字符数为 Baseline **2,053**、V3 **2,363**。字符数只用于衡量输出长度。

## 如何解读

V3 在四道有提升空间的题上均得分更高。N02 补了生效边界和冲突规则验收，仍缺少排除冲突机制的一种判据。N04 写清自动关单试点的停试、回退和受影响批次复核。N07 把账务修复和资金升级与核验结果对应。N09 补充可比较的办理基线。

本轮出现评分天花板。Baseline 有六道复杂题拿满分，按实际盲评分，候选理论上最多赢四题。Baseline 均分 95.50，候选即使题题满分，平均最多提升 4.50 分。两项晋升门槛在这组实际得分下均无法达到。结论是本轮没有达到事先约定的晋升证据，四道题的增益仍有效记录。本轮没有触发事后改题或改评分。

## 执行证据

- [定向回归](development/REGRESSION.md)在新题实跑前完成。实验先提交 [冻结版本](https://github.com/lovemoganna/Org-Skills/commit/ffffc5bf8d37ad858f11797883ec8b8e6e7d8a14)，其树包含冻结题集、预注册门槛和一条候选规则。新集与旧集无逐字重复题面，由主线程设计，侧重本次修复目标。
- 两臂均配置 Work GPT-6.2 Sol / medium，使用独立新线程，每臂一次按序回答。第三个同配置的新线程独立匿名评分。[线程回执、输入输出指纹与锁分记录](execution-evidence.json)可查。线程隔离采用无上下文继承和限定文件访问。
- [原始输入与回答](raw/) · [逐题记录](outputs/) · [匿名评审包和锁分](review/) · [解盲密钥](unblind/key.json) · [机器复算](result.json) · [本地回归日志](local-regression.log)
- 后端会话 UUID、可导出原始 trace、模型快照、token 和模型推理时延均为 `NOT_VERIFIED`。本轮仅一次双臂实测和一名模型盲评员，得分和胜负适用于本次样本。

## 按冻结脚本复算

```bash
git fetch origin 4c114b27233abd3b04d6bff47f51de4fe3921a13
R=skills/causal-net-loop/evals/runs/v3-2026-11-18
P=skills/causal-net-loop/evals/blind12_v3.py
python3 "$P" check
python3 "$P" score --source "$R/outputs" --review "$R/review/locked-scores.json" \
  --key "$R/unblind/key.json" --out /tmp/causal-v3-replayed.json
cmp "$R/result.json" /tmp/causal-v3-replayed.json
```
