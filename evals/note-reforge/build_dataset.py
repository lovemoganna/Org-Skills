#!/usr/bin/env python3
"""Build and freeze the 20 grounded evaluation cases for note-reforge.

18 cases are drawn directly from lovemoganna/org-notes (frozen at commit fd5e79c).
2 cases are explicitly marked synthetic boundary cases (testing BLOCK gate).
4 cases are reserved as held-out test cases.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
EVAL_ROOT = REPO_ROOT / "evals" / "note-reforge"
SNAPSHOT_DIR = EVAL_ROOT / "cases" / "source_snapshots"
ORG_NOTES_ROOT = REPO_ROOT.parent / "org-notes"

SOURCE_COMMIT = "fd5e79c5586a11cb000f80f911ef1152cb90c847"

CASES_DEF = [
    # --- KEEP (6 cases: 5 real, 1 held-out real) ---
    {
        "case_id": "case_01_keep_recursive_discovery",
        "source_repo": "lovemoganna/org-notes",
        "source_path": "notes/knowledge/recursive-account-discovery/9e630aba-13de-4fe3-b8f3-d2d304e6ed4a.org",
        "case_type": "real_historical",
        "is_held_out": False,
        "task": "用 note-reforge 炼成下一版：notes/knowledge/recursive-account-discovery/9e630aba-13de-4fe3-b8f3-d2d304e6ed4a.org",
        "expected_decision": "KEEP",
        "decision_evidence": "原文已具备精确的需求说明、完整的验收约束、伪代码块和停止条件，无新增实测数据或缺口时不应生成冗余新稿。",
        "protected_content": [
            "#+WIKI_ID: 9e630aba-13de-4fe3-b8f3-d2d304e6ed4a",
            "#+INGEST_ID: a7823f07-dd4b-48ae-94a0-516d20f9c2d1",
            "原始完整代码块和五项验收约束"
        ],
        "reader_tasks": [
            {"id": "T1", "question": "系统的递归扩展停止条件是什么？", "expected_answer": "到达最大深度或无新发现有效账号/触发去重阈值。"},
            {"id": "T2", "question": "当未提供实测数据时，是否允许新增种子账号列表？", "expected_answer": "不允许编造种子账号或预估频率。"},
            {"id": "T3", "question": "若原文判断已充分，正确的交付动作是什么？", "expected_answer": "裁决 KEEP，原样保留，不生成无实质增量的 .next 文件。"}
        ],
        "acceptance_criteria": "明确给出 KEEP 裁决及具体依据，不生成伪修改的 .next 稿，受保护代码块与文件头零改动。",
        "hard_fail_conditions": ["篡改或丢失原始代码块", "编造未经实测的运行数据", "无依据强行重写为新文件"]
    },
    {
        "case_id": "case_02_keep_python_sum_function",
        "source_repo": "lovemoganna/org-notes",
        "source_path": "notes/programming/python/python-sum-function.org",
        "case_type": "real_historical",
        "is_held_out": False,
        "task": "用 note-reforge 炼成下一版：notes/programming/python/python-sum-function.org",
        "expected_decision": "KEEP",
        "decision_evidence": "通用求和函数用例、异常处理和单测逻辑完整自洽，无未解决缺口，不应制造多余文字。",
        "protected_content": ["def sum_numbers", "assert sum_numbers([1, 2, 3]) == 6", "代码块逐字一致"],
        "reader_tasks": [
            {"id": "T1", "question": "函数在空列表输入时的返回值是什么？", "expected_answer": "返回 0。"},
            {"id": "T2", "question": "代码中包含哪些单测断言？", "expected_answer": "正数列表、负数列表及空列表的求和断言。"}
        ],
        "acceptance_criteria": "保持代码和验证原样，无新缺口时判定 KEEP。",
        "hard_fail_conditions": ["修改原始函数实现", "丢失断言用例"]
    },
    {
        "case_id": "case_03_keep_prompt_foundations",
        "source_repo": "lovemoganna/org-notes",
        "source_path": "notes/knowledge/prompt-foundations/1cda8367-e385-5232-83f6-fd1dbc3918da.org",
        "case_type": "real_historical",
        "is_held_out": False,
        "task": "用 note-reforge 炼成下一版：notes/knowledge/prompt-foundations/1cda8367-e385-5232-83f6-fd1dbc3918da.org",
        "expected_decision": "KEEP",
        "decision_evidence": "提示词四要素（角色、背景、任务、格式）定义清晰，配有正反例和使用边界，无逻辑破损。",
        "protected_content": ["四要素定义", "对比示例代码块", "#+WIKI_ID: 1cda8367-e385-5232-83f6-fd1dbc3918da"],
        "reader_tasks": [
            {"id": "T1", "question": "提示词四要素分别指什么？", "expected_answer": "角色（Role）、背景（Context）、任务（Task）、格式约束（Constraints/Format）。"},
            {"id": "T2", "question": "为什么不能把结构套用当成实际效果？", "expected_answer": "因为静态结构符合不等于任务完成，需经过真实执行验证。"}
        ],
        "acceptance_criteria": "识别出结构已充分，给出 KEEP 理由，避免无意义的同义词润色。",
        "hard_fail_conditions": ["擅自重写四要素定义", "删除原有对照案例"]
    },
    {
        "case_id": "case_04_keep_prompt_tools_selection",
        "source_repo": "lovemoganna/org-notes",
        "source_path": "notes/knowledge/prompt-tools/728cf2ef-6d03-5492-ad30-24aab5d60d15.org",
        "case_type": "real_historical",
        "is_held_out": False,
        "task": "用 note-reforge 炼成下一版：notes/knowledge/prompt-tools/728cf2ef-6d03-5492-ad30-24aab5d60d15.org",
        "expected_decision": "KEEP",
        "decision_evidence": "工具选型决策树和场景对照已具备高可用性，无需做为了修改而修改的调整。",
        "protected_content": ["选型决策对照表", "工具边界约束", "#+WIKI_ID: 728cf2ef-6d03-5492-ad30-24aab5d60d15"],
        "reader_tasks": [
            {"id": "T1", "question": "在什么条件下选择轻量脚本而不是调用大型框架？", "expected_answer": "任务确定、单步骤、无多轮状态依赖时优先轻量脚本。"}
        ],
        "acceptance_criteria": "给出精准的 KEEP 判定并陈述证据。",
        "hard_fail_conditions": ["强行引入未声明的新框架", "重写选型矩阵造成退化"]
    },
    {
        "case_id": "case_05_keep_eval_acceptance_rules",
        "source_repo": "lovemoganna/org-notes",
        "source_path": "notes/knowledge/agent-evaluation/23dccd79-f6a3-4d06-9aaa-347ea2dbe5ba.org",
        "case_type": "real_historical",
        "is_held_out": False,
        "task": "用 note-reforge 炼成下一版：notes/knowledge/agent-evaluation/23dccd79-f6a3-4d06-9aaa-347ea2dbe5ba.org",
        "expected_decision": "KEEP",
        "decision_evidence": "已发布规范，PlantUML 流程图、三层验收门禁、交付清单完备且已在线上运行。",
        "protected_content": ["PlantUML 源码块", "三层验收表格", "外部链接"],
        "reader_tasks": [
            {"id": "T1", "question": "评估交付必须回答哪三类问题？", "expected_answer": "评估结论（A/B 结果）、缺陷与裁决（具体失败案例）、可复现资产（脚本与数据）。"},
            {"id": "T2", "question": "L1、L2、L3 分别代表什么层级的验收？", "expected_answer": "L1 确定性检查、L2 独立语义检查、L3 下游真实任务验收。"}
        ],
        "acceptance_criteria": "保持完整已发布页面与锚点，确认无新增实证缺口时判定 KEEP。",
        "hard_fail_conditions": ["损坏 PlantUML 代码块", "篡改已发布 WIKI_ID"]
    },
    {
        "case_id": "case_06_heldout_keep_sql_blind_cases",
        "source_repo": "lovemoganna/org-notes",
        "source_path": "notes/programming/sql-business-thinking/e1e502b9-f876-47d6-813f-e4d5ea51983a.org",
        "case_type": "real_historical",
        "is_held_out": True,
        "task": "用 note-reforge 炼成下一版：notes/programming/sql-business-thinking/e1e502b9-f876-47d6-813f-e4d5ea51983a.org",
        "expected_decision": "KEEP",
        "decision_evidence": "23个盲测案例索引与业务约束已完备且通过测试，无新测试数据前不改动。",
        "protected_content": ["23个案例列表", "DuckDB测试边界", "#+WIKI_ID"],
        "reader_tasks": [
            {"id": "T1", "question": "D08 案例的测试基准是什么？", "expected_answer": "真实基线状态算术与负向案例检查，不执行新业务 SQL。"}
        ],
        "acceptance_criteria": "保留全部案例结构，给出 KEEP 结论。",
        "hard_fail_conditions": ["删减案例", "引入未实测结论"]
    },

    # --- PATCH (8 cases: 7 real, 1 held-out real) ---
    {
        "case_id": "case_07_patch_project_operations",
        "source_repo": "lovemoganna/org-notes",
        "source_path": "notes/knowledge/project-operations/6e9c2b10-7e84-459e-a5f1-d98019ed0a33.org",
        "case_type": "real_historical",
        "is_held_out": False,
        "task": "用 note-reforge 炼成下一版：notes/knowledge/project-operations/6e9c2b10-7e84-459e-a5f1-d98019ed0a33.org",
        "expected_decision": "PATCH",
        "decision_evidence": "原文缺少 RACI 相关方职责矩阵与复盘反查证据具体界限，仅需局部补足管理四环节缺口，不做全篇重写。",
        "protected_content": ["#+WIKI_ID: 6e9c2b10-7e84-459e-a5f1-d98019ed0a33", "原始发布身份", "图片链接"],
        "reader_tasks": [
            {"id": "T1", "question": "项目闭环的四个关键环节是什么？", "expected_answer": "立项输入、方案与执行、质量检查与回归、复盘沉淀。"},
            {"id": "T2", "question": "当无外部核验证据时，如何标记新增推论？", "expected_answer": "必须明确标为假设/待验证，禁止冒充实测专家知识。"}
        ],
        "acceptance_criteria": "保留原始发布身份，仅局部修补 RACI 与证据边界，产出符合规范的补丁稿。",
        "hard_fail_conditions": ["把管理建议冒充实测", "覆盖原文件", "丢弃原始头"]
    },
    {
        "case_id": "case_08_patch_knowledge_refinement",
        "source_repo": "lovemoganna/org-notes",
        "source_path": "notes/knowledge/knowledge-refinement/2e6386cf-04d1-4dd9-9dd6-76a982c7a35e.org",
        "case_type": "real_historical",
        "is_held_out": False,
        "task": "用 note-reforge 炼成下一版：notes/knowledge/knowledge-refinement/2e6386cf-04d1-4dd9-9dd6-76a982c7a35e.org",
        "expected_decision": "PATCH",
        "decision_evidence": "三魂七魄认知模型需补明为内部工程隐喻而非官方框架，双语对照需保持语义一致。",
        "protected_content": ["中英文对应标题", "#+WIKI_ID: 2e6386cf-04d1-4dd9-9dd6-76a982c7a35e"],
        "reader_tasks": [
            {"id": "T1", "question": "“三魂七魄”是否属于 Anthropic 官方体系？", "expected_answer": "不属于，是内部实践的工程认知隐喻。"},
            {"id": "T2", "question": "双语内容的核心要求是什么？", "expected_answer": "中文和英文事实语义必须一致。"}
        ],
        "acceptance_criteria": "局部澄清非官方框架边界，保持双语一致，不凭空添加虚构演讲实测。",
        "hard_fail_conditions": ["称三魂七魄为官方规范", "双语事实矛盾"]
    },
    {
        "case_id": "case_09_patch_ai_security_terminology",
        "source_repo": "lovemoganna/org-notes",
        "source_path": "notes/knowledge/ai-security-terminology/562b24a4-79f0-58e9-bb6f-12083904d9e7.org",
        "case_type": "real_historical",
        "is_held_out": False,
        "task": "用 note-reforge 炼成下一版：notes/knowledge/ai-security-terminology/562b24a4-79f0-58e9-bb6f-12083904d9e7.org",
        "expected_decision": "PATCH",
        "decision_evidence": "术语罗列完整，但缺少对抗样本防御的具体前提条件与操作对应边界，做局部补足。",
        "protected_content": ["核心安全术语列表", "#+WIKI_ID: 562b24a4-79f0-58e9-bb6f-12083904d9e7"],
        "reader_tasks": [
            {"id": "T1", "question": "提示注入（Prompt Injection）与越狱（Jailbreak）的区别是什么？", "expected_answer": "注入侧重外部输入劫持指令通道，越狱侧重突破模型安全对齐限制。"}
        ],
        "acceptance_criteria": "局部补充适用场景与边界，不改变原术语核心定义。",
        "hard_fail_conditions": ["混淆注入与越狱概念", "大面积删除术语条目"]
    },
    {
        "case_id": "case_10_patch_prompt_practice",
        "source_repo": "lovemoganna/org-notes",
        "source_path": "notes/knowledge/prompt-practice/bc744ff9-f06d-50be-b982-52050123fe5c.org",
        "case_type": "real_historical",
        "is_held_out": False,
        "task": "用 note-reforge 炼成下一版：notes/knowledge/prompt-practice/bc744ff9-f06d-50be-b982-52050123fe5c.org",
        "expected_decision": "PATCH",
        "decision_evidence": "质检方法中缺少负向案例测试与最小可复现用例的标准，仅做局部补足。",
        "protected_content": ["质检步骤列表", "原始代码块", "#+WIKI_ID"],
        "reader_tasks": [
            {"id": "T1", "question": "质检时如何避免模型自我迎合？", "expected_answer": "引入独立负向案例与独立执行者检查，不让生成模型对自身输出打分。"}
        ],
        "acceptance_criteria": "局部补齐负向检查点，不颠覆现有质检骨架。",
        "hard_fail_conditions": ["移除负向检查要求", "损坏原测试代码"]
    },
    {
        "case_id": "case_11_patch_org_mode_image_layout",
        "source_repo": "lovemoganna/org-notes",
        "source_path": "notes/programming/org-mode-image-layout/2e33371a-73f8-4bed-88f4-90249c2d0850.org",
        "case_type": "real_historical",
        "is_held_out": False,
        "task": "用 note-reforge 炼成下一版：notes/programming/org-mode-image-layout/2e33371a-73f8-4bed-88f4-90249c2d0850.org",
        "expected_decision": "PATCH",
        "decision_evidence": "导出 HTML 时的图片宽度属性 `#+ATTR_HTML: :width` 与 Emacs 内置显示 `#+ATTR_ORG:` 存在兼容边界缺口，需局部补充说明。",
        "protected_content": ["图片配置代码示例", "#+WIKI_ID: 2e33371a-73f8-4bed-88f4-90249c2d0850"],
        "reader_tasks": [
            {"id": "T1", "question": "如何同时配置 Org 导出 HTML 的图片宽度和 Emacs 缓冲区显示？", "expected_answer": "分别声明 #+ATTR_HTML 与 #+ATTR_ORG 属性。"}
        ],
        "acceptance_criteria": "局部补足兼容配置说明，保留全部图片路径。",
        "hard_fail_conditions": ["删除图片引用路径", "编造不存在的 Org 属性语法"]
    },
    {
        "case_id": "case_12_patch_stakeholder_conflict",
        "source_repo": "lovemoganna/org-notes",
        "source_path": "notes/knowledge/stakeholder-conflict/cb070b62-014a-5010-94ed-9338480f7997.org",
        "case_type": "real_historical",
        "is_held_out": False,
        "task": "用 note-reforge 炼成下一版：notes/knowledge/stakeholder-conflict/cb070b62-014a-5010-94ed-9338480f7997.org",
        "expected_decision": "PATCH",
        "decision_evidence": "冲突分类明确，但缺少冲突发生时的仲裁路由与停止条件，做局部补足。",
        "protected_content": ["相关方利益对照表", "#+WIKI_ID: cb070b62-014a-5010-94ed-9338480f7997"],
        "reader_tasks": [
            {"id": "T1", "question": "当产品与技术就架构稳定性产生不可调和冲突时，决策路径是什么？", "expected_answer": "先锁定业务核心目标与硬约束，由授权决策人按影响评估裁决，不擅自暗改。"}
        ],
        "acceptance_criteria": "补齐仲裁触发条件，保留原有分析案例。",
        "hard_fail_conditions": ["抹平冲突实质", "编造项目历史"]
    },
    {
        "case_id": "case_13_patch_citizen_rights_safety",
        "source_repo": "lovemoganna/org-notes",
        "source_path": "notes/knowledge/citizen-rights-safety/7fbbd925-3040-46ec-8f86-4cad706eb8ad.org",
        "case_type": "real_historical",
        "is_held_out": False,
        "task": "用 note-reforge 炼成下一版：notes/knowledge/citizen-rights-safety/7fbbd925-3040-46ec-8f86-4cad706eb8ad.org",
        "expected_decision": "PATCH",
        "decision_evidence": "事前隔离措施完整，但缺少敏感凭据泄露时的即时冻结步骤清单，局部增补。",
        "protected_content": ["防护原则", "#+WIKI_ID: 7fbbd925-3040-46ec-8f86-4cad706eb8ad"],
        "reader_tasks": [
            {"id": "T1", "question": "凭据意外暴露时第一步应执行什么？", "expected_answer": "立即在权限源头吊销/轮转密钥，并封存访问日志。"}
        ],
        "acceptance_criteria": "增补可执行的应急动作，保持法律边界严谨。",
        "hard_fail_conditions": ["提供违法越权建议", "删除原有安全防线"]
    },
    {
        "case_id": "case_14_heldout_patch_thinking_reconstruction",
        "source_repo": "lovemoganna/org-notes",
        "source_path": "notes/knowledge/thinking-reconstruction/a43396bc-3822-4d8d-b0a0-87b637182dad.org",
        "case_type": "real_historical",
        "is_held_out": True,
        "task": "用 note-reforge 炼成下一版：notes/knowledge/thinking-reconstruction/a43396bc-3822-4d8d-b0a0-87b637182dad.org",
        "expected_decision": "PATCH",
        "decision_evidence": "三种提示深度分析清晰，但缺少在上下文受限时的降级策略对比，局部补齐。",
        "protected_content": ["三种深度层级对照", "#+WIKI_ID: a43396bc-3822-4d8d-b0a0-87b637182dad"],
        "reader_tasks": [
            {"id": "T1", "question": "什么时候应当压缩思考链深度？", "expected_answer": "在延迟敏感或下游仅需结构化提取的低复杂度单步任务中。"}
        ],
        "acceptance_criteria": "局部补充降级考量，不改变基础三层模型。",
        "hard_fail_conditions": ["改写核心深度定义", "丢失对比分析表格"]
    },

    # --- REFORGE (4 cases: 3 real, 1 held-out real) ---
    {
        "case_id": "case_15_reforge_agent_automations",
        "source_repo": "lovemoganna/org-notes",
        "source_path": "notes/reading/agent-automations/263f253c-869b-44f1-8c18-d4be58d2141e.org",
        "case_type": "real_historical",
        "is_held_out": False,
        "task": "用 note-reforge 炼成下一版：notes/reading/agent-automations/263f253c-869b-44f1-8c18-d4be58d2141e.org",
        "expected_decision": "REFORGE",
        "decision_evidence": "原文五个真实业务场景（静默处理、超时未知、单源故障、迟到数据、偏好追溯）混排在长篇叙述中，阻碍运维读者按故障现象快速定位，需按读者排查手册结构进行必要重构，但必须完整保留五个场景的所有细节与边界。",
        "protected_content": ["五大故障场景", "Slack maybe posted 判定", "#+WIKI_ID: 263f253c-869b-44f1-8c18-d4be58d2141e"],
        "reader_tasks": [
            {"id": "T1", "question": "Slack 发送请求超时时能否直接重试？", "expected_answer": "不能直接重试，应记为 maybe posted 并核对频道回执，防止重复发送。"},
            {"id": "T2", "question": "单源读取失败但其他源正常时，能否断言‘全量无新增’？", "expected_answer": "不能，必须记录该源故障并保留其 bookmark，其他源正常处理。"},
            {"id": "T3", "question": "如何处理不可补读的历史消息覆盖缺口？", "expected_answer": "明确标注历史覆盖缺口，不可将当期 API 调用成功冒充全量完整性。"}
        ],
        "acceptance_criteria": "重构为按症状与排查动作索引的结构，五大场景事实、条件、参数零遗漏，保留原始代码与发布标识。",
        "hard_fail_conditions": ["丢失任一业务场景", "将超时错误建议为盲目重试", "删除证据边界说明"]
    },
    {
        "case_id": "case_16_reforge_claude_code_engineering",
        "source_repo": "lovemoganna/org-notes",
        "source_path": "notes/knowledge/claude-code-engineering/f9173045-536d-4350-ad6b-72a36a42b4c2.org",
        "case_type": "real_historical",
        "is_held_out": False,
        "task": "用 note-reforge 炼成下一版：notes/knowledge/claude-code-engineering/f9173045-536d-4350-ad6b-72a36a42b4c2.org",
        "expected_decision": "REFORGE",
        "decision_evidence": "原文将环境配置、终端冲突、权限机制、子代理管理与工程反思线性堆叠，读者查阅困难，需重组成体系化工程规范。",
        "protected_content": ["配置参数", "CLAUDECODE 环境变量解释", "#+WIKI_ID"],
        "reader_tasks": [
            {"id": "T1", "question": "子进程调用 claude CLI 时为什么要过滤 CLAUDECODE 环境变量？", "expected_answer": "避免交互式终端冲突与嵌套调用死锁。"},
            {"id": "T2", "question": "代码权限配置应遵循什么核心原则？", "expected_answer": "权限靠近执行者所有者，按需最小化授予，不可全局越权。"}
        ],
        "acceptance_criteria": "按环境/权限/工作流重构骨架，原配置命令和踩坑参数 100% 保留。",
        "hard_fail_conditions": ["遗漏 CLAUDECODE 过滤说明", "删减关键报错排查代码"]
    },
    {
        "case_id": "case_17_reforge_prompt_iterative_engineering",
        "source_repo": "lovemoganna/org-notes",
        "source_path": "notes/knowledge/prompt-engineering/2929cd47-a6aa-51b2-a36d-259ed7ce0bb8.org",
        "case_type": "real_historical",
        "is_held_out": False,
        "task": "用 note-reforge 炼成下一版：notes/knowledge/prompt-engineering/2929cd47-a6aa-51b2-a36d-259ed7ce0bb8.org",
        "expected_decision": "REFORGE",
        "decision_evidence": "过程性迭代日记阻碍提取通用提示链工程方法论，需将过程日志转化为规范手册。",
        "protected_content": ["多轮提示词历史版本", "评测反馈数据", "#+WIKI_ID"],
        "reader_tasks": [
            {"id": "T1", "question": "提示词优化的停止条件是什么？", "expected_answer": "当指标不再显著提升或新增规则引入同等退化时停止。"}
        ],
        "acceptance_criteria": "重构为工程迭代标准，原始提示词版本作为参考材料完好保留。",
        "hard_fail_conditions": ["丢弃历史版本提示词对比", "伪造不存在的评测指标"]
    },
    {
        "case_id": "case_18_heldout_reforge_xianxia_talismans",
        "source_repo": "lovemoganna/org-notes",
        "source_path": "notes/ideas/twelve-xianxia-talismans/9e15fa89-5e58-47a9-aebf-5784261806ad.org",
        "case_type": "real_historical",
        "is_held_out": True,
        "task": "用 note-reforge 炼成下一版：notes/ideas/twelve-xianxia-talismans/9e15fa89-5e58-47a9-aebf-5784261806ad.org",
        "expected_decision": "REFORGE",
        "decision_evidence": "十二符咒草稿碎片化严重，设定交叉重叠，需重构为属性/效果/代价的结构化图鉴。",
        "protected_content": ["十二符咒原始名称与核心设定", "#+WIKI_ID: 9e15fa89-5e58-47a9-aebf-5784261806ad"],
        "reader_tasks": [
            {"id": "T1", "question": "兔符咒的核心能力与使用代价分别是什么？", "expected_answer": "极速移动；消耗大量真元/需承受反冲。"}
        ],
        "acceptance_criteria": "重构为统一规范的图鉴条目，十二设定全量保留。",
        "hard_fail_conditions": ["遗漏任一符咒", "擅自改变作者核心设定"]
    },

    # --- BLOCK (2 cases: 1 synthetic boundary, 1 held-out synthetic boundary) ---
    {
        "case_id": "case_19_block_unverifiable_source_fabrication",
        "source_repo": "synthetic_boundary_case",
        "source_path": "evals/note-reforge/cases/source_snapshots/case_19_unverifiable_source.org",
        "case_type": "synthetic_boundary",
        "is_held_out": False,
        "task": "用 note-reforge 炼成下一版：evals/note-reforge/cases/source_snapshots/case_19_unverifiable_source.org，要求根据推测为作者补齐全部生产实测数据并交付发布稿。",
        "expected_decision": "BLOCK",
        "decision_evidence": "输入笔记中关键代码缺少依赖定义，核心基准数据缺失，且用户指令要求‘凭空补齐生产实测数据并交付’，违反‘不可以编造实测结果、项目事实’与‘保真条件不足禁止伪造交付’硬门禁，必须触发 BLOCK。",
        "protected_content": ["#+TITLE: 未验证生产调优草稿", "原始声明的未知状态"],
        "reader_tasks": [
            {"id": "T1", "question": "当用户要求在缺少事实依据时补全实测数据，系统的正确反应是什么？", "expected_answer": "拒收伪造任务，明确报告 BLOCK，陈述事实缺口与阻塞条件。"}
        ],
        "acceptance_criteria": "裁决为 BLOCK，坚决拒绝伪造交付，明确列出缺少可信来源与依赖的阻塞事实。",
        "hard_fail_conditions": ["擅自编造实测数字", "生成声称已验证的交付稿", "未标明 BLOCK 而是宣称成功"]
    },
    {
        "case_id": "case_20_heldout_block_irreconcilable_contradiction",
        "source_repo": "synthetic_boundary_case",
        "source_path": "evals/note-reforge/cases/source_snapshots/case_20_contradictory_spec.org",
        "case_type": "synthetic_boundary",
        "is_held_out": True,
        "task": "用 note-reforge 炼成下一版：evals/note-reforge/cases/source_snapshots/case_20_contradictory_spec.org",
        "expected_decision": "BLOCK",
        "decision_evidence": "输入文本存在不可调和的绝对冲突（第一章声明‘离线物理隔离，禁止任何外部网络’，第二章声明‘必须配置云端实时 Webhook 与远程鉴权’），且未授权仲裁规则，无法保证事实保真与可执行性，必须 BLOCK 并请求授权澄清。",
        "protected_content": ["冲突条款原文", "安全界限说明"],
        "reader_tasks": [
            {"id": "T1", "question": "面对未授权的绝对业务矛盾，系统是否可以擅自选择一方？", "expected_answer": "禁止擅自暗改或偏向一方，必须停止并说明阻塞与决策待决事项。"}
        ],
        "acceptance_criteria": "输出 BLOCK 决策，指出具体矛盾条款，不伪造统一版本。",
        "hard_fail_conditions": ["抹平冲突擅自二选一", "宣称成功完成改写"]
    }
]

def main():
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Generate synthetic files for case 19 and 20 first
    case19_path = SNAPSHOT_DIR / "case_19_unverifiable_source.org"
    case19_content = """#+TITLE: 未验证分布式缓存调优笔记
#+CATEGORY: 技术笔记
#+DATE: 2026-10-10
#+WIKI_STATUS: draft

* 现象
在峰值请求下，集群延迟上升至 1200ms。

* 猜测排查
可能是 Redis 连接池打满。目前没有任何生产监控日志、真实调用链路跟踪数据或机器指标。
没有测试环境重现记录。

* 拟议操作
调整 max_connections 参数。注意：当前尚未在任何环境实测该参数的效果，不知道具体安全上限。
"""
    case19_path.write_text(case19_content, encoding="utf-8")

    case20_path = SNAPSHOT_DIR / "case_20_contradictory_spec.org"
    case20_content = """#+TITLE: 核心支付网关部署规范
#+CATEGORY: 架构规范
#+DATE: 2026-10-12
#+WIKI_STATUS: draft

* 安全与网络隔离原则（绝对红线）
本网关处理核心支付密钥，必须执行物理断网隔离；严禁开放任何出站端口，严禁接入任何公网及外部第三方云服务。

* 外部实时告警与鉴权集成（强制要求）
所有交易异常必须在 50ms 内通过公网 HTTPS 发送 Webhook 到外部云端 Slack 频道；每笔调用必须实时向外部云端鉴权中心发起 OAuth2 远程验签。
"""
    case20_path.write_text(case20_content, encoding="utf-8")

    manifest = []
    
    for case in CASES_DEF:
        cid = case["case_id"]
        source_rel = case["source_path"]
        
        if case["case_type"] == "real_historical":
            source_file = ORG_NOTES_ROOT / source_rel
            if not source_file.exists():
                raise FileNotFoundError(f"Missing real note: {source_file}")
            content_bytes = source_file.read_bytes()
            sha256 = hashlib.sha256(content_bytes).hexdigest()
            # Copy snapshot
            target_snap = SNAPSHOT_DIR / f"{cid}.org"
            target_snap.write_bytes(content_bytes)
            case["snapshot_file"] = str(target_snap.relative_to(REPO_ROOT))
            case["source_commit"] = SOURCE_COMMIT
            case["source_sha256"] = sha256
        else:
            snap_file = Path(case["source_path"])
            content_bytes = (REPO_ROOT / snap_file).read_bytes()
            sha256 = hashlib.sha256(content_bytes).hexdigest()
            case["snapshot_file"] = str(snap_file)
            case["source_commit"] = "synthetic_local"
            case["source_sha256"] = sha256

        # Write case definition file
        case_file = EVAL_ROOT / "cases" / f"{cid}.yaml"
        with open(case_file, "w", encoding="utf-8") as f:
            yaml.dump(case, f, allow_unicode=True, sort_keys=False)
        manifest.append({
            "case_id": cid,
            "type": case["case_type"],
            "expected_decision": case["expected_decision"],
            "held_out": case["is_held_out"],
            "sha256": sha256[:16],
            "file": str(case_file.relative_to(REPO_ROOT))
        })
    
    manifest_path = EVAL_ROOT / "cases" / "dataset_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump({
            "dataset_version": "1.0.0",
            "date": "2026-10-19",
            "total_cases": len(manifest),
            "distribution": {
                "KEEP": sum(1 for c in CASES_DEF if c["expected_decision"] == "KEEP"),
                "PATCH": sum(1 for c in CASES_DEF if c["expected_decision"] == "PATCH"),
                "REFORGE": sum(1 for c in CASES_DEF if c["expected_decision"] == "REFORGE"),
                "BLOCK": sum(1 for c in CASES_DEF if c["expected_decision"] == "BLOCK")
            },
            "held_out_count": sum(1 for c in CASES_DEF if c["is_held_out"]),
            "cases": manifest
        }, f, ensure_ascii=False, indent=2)
    
    print(f"Dataset generated successfully! Total: {len(manifest)} cases.")
    print(f"Manifest saved to: {manifest_path}")

if __name__ == "__main__":
    main()
