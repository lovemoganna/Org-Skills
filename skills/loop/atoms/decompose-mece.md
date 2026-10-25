---
name: decompose-mece
status: draft
---
# 最小 MECE 子任务

输入：goal、necessary_conditions、scope_out。按互不重复的**产出物**拆解子任务；标输入与依赖，逐个必要条件建覆盖映射，未覆盖则报告缺口。
输出：子任务表(id/名称/产出物/输入/依赖)、覆盖矩阵、重叠/缺口。
不得引入 scope_out 或超范围产物；不替 S3 制定执行路由。
