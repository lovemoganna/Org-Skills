# Changelog

## v16 — Source Gate / Fail-closed reporting

- 固定来源只可由同一 URL 的真实完整字节填充，不得因远端元数据存在即推进分析。
- 源 Gate 失败时自动交付 Markdown、HTML、JSON 审计文件。
- 阻塞不等于完成分析；禁止构造 SQL Result 或 Finding。
- Olist 特定执行器不属于通用 Skill。
- 保留 v15 的本体、Signal、关系执行、竞争解释和多表粒度约束。
- 新增源阻塞与通用性回归 Eval；Eval 定义验证不代表模型行为已验证。
