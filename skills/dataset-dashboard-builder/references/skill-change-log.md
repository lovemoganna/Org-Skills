# Skill Change Log

## V1：真实四表数据集回归

| 暴露缺陷 | 根因 | 最小修正 | 可泛化规则 |
|---|---|---|---|
| 单日汇率覆盖跨期交易，初版仍可能生成“历史成交额” | 只有“识别指标”，没有时间维表语义门 | 新增 Time-dimension Gate | exact → as-of → snapshot → blocked；snapshot 必须改名 |
| 9 个活跃用户如果默认 Top10，会把全体当集中度 | 初版只有 Top/Bottom，没有样本自适应 | 新增 Adaptive TopN | active ≤10 使用 Top1/Top3；覆盖全体不得当集中度结论 |
| 数据中存在订单 ID 日期与 created_at 冲突，初版可能直接出 KPI | 缺少 KPI 前置数据质量门 | 新增 Quality Gate | 会改变解释的数据异常必须显式 LIMITED/BLOCKED |
| 初版要求“生成看板”，但没有验证 HTML 实际可读 | 只约束生成，没有渲染验收 | 新增 Rendered QA | DOM、JS、响应式、内容覆盖、限制位置都需验证 |
