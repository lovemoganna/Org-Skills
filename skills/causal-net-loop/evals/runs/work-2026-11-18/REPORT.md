# PR #115 Work A/B 实测报告

**保留 Draft，Candidate V2 不晋升。** 2026-11-18 完成 12 题双臂实测和 24 条独立模型匿名评分。复杂题共 10 道，Candidate V2 为 **1 胜、3 负、6 平**，平均 **89.25/100**，Baseline 为 **95.00/100**，差 **−5.75 分**。

| 预注册门槛 | 实测 | 结果 |
| --- | --- | --- |
| 至少 8 胜、最多 1 负 | 1 胜、3 负、6 平 | 未通过 |
| 平均提升至少 5 分 | −5.75 分 | 未通过 |
| 硬失败 0 次 | 两臂均为 0/12 | 通过 |
| 两道负对照均通过 | 两臂均为 2/2 | 通过 |
| 复杂题字数比中位数 ≤ 1.25 | 0.907 | 通过 |

## 实际差异

| 案例 | Candidate − Baseline | 盲评依据 |
| --- | ---: | --- |
| [N02 冷静期](outputs/candidate/N02.json) | +7.5 | 候选给出额外挽损和结算延误两条停止条件。 |
| [N01 制裁筛查](outputs/candidate/N01.json) | −25.0 | 候选用证件号和生日复核身份，遗漏对备选出生日期或录入差错的查证。 |
| [N04 RFI 结论复审](outputs/candidate/N04.json) | −27.5 | 候选提出原案重放，但未给出文件有效期、交易日期、地址归属置信度各自的复核动作。 |
| [N07 导出故障复发](outputs/candidate/N07.json) | −12.5 | 候选给出 CSV 往返验收，权限与时区仅保留复现样例，缺少各自的验收检查。 |

N09 两臂均为 65 分，均抓到公共交通运力约束，均缺少试点停止规则。盲评还记录了对其他后果覆盖不足的意见，而题目要求聚焦单条连锁影响。这项口径张力影响对 N09 绝对分数的解读。原始锁分及预注册计分保留。其余五个复杂案例持平。

## 执行证据与限制

- 两臂在三个相互独立角色中的前两条 Work 子线程运行，均显式指定 `gpt-6.2-sol` / `medium`，上下文继承为 `none`。每臂按 N01–N12 顺序一次提交 12 个完整回答。执行线程各自接收一个冻结 Skill 和相同题面，工具仅用于本地读取和存档。第三条新线程收到逐题随机匿名的答案、评分模板及固定判据。锁分哈希在恢复密钥前记录。参见 [协作工具回执和输入输出指纹](execution-evidence.json)。
- [原始输入和答卷](raw/)、[24 份逐题记录](outputs/)、[匿名评审材料和锁分](review/)、[解盲密钥](unblind/key.json)、[复算结果](result.json)及[运行日志](score.log)一并归档。评分脚本通过逐字引用校验。
- 平台提供本轮真实协作线程路由名和完成回执。后端会话 UUID、可导出运行轨迹、推理快照、token 和推理耗时均为 `NOT_VERIFIED`。共享工作区依靠限定输入范围隔离。本轮模型为 Work GPT-6.2 Sol，原 Chat GPT-6 Instant 的表现未经验证。
- 两臂复杂题合计字符数为 1,788 和 1,588，候选少 200 字符（11.2%）。字符数衡量输出长度。本轮仅有每臂一次执行和一名模型盲评员，无法由此估计统计显著性。

## 复算

在本 PR 分支根目录运行。

```bash
R=skills/causal-net-loop/evals/runs/work-2026-11-18
P=skills/causal-net-loop/evals/blind12.py
python3 "$P" check
python3 "$P" verify --source "$R/outputs"
python3 "$P" score --source "$R/outputs" \
  --review "$R/review/locked-scores.json" --key "$R/unblind/key.json" \
  --out /tmp/causal115-reproduced.json
cmp "$R/result.json" /tmp/causal115-reproduced.json
```
