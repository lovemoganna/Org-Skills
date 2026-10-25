# suno-songwriting

从《Suno 音乐创作元提示体系统 v2.0》与后续《不喜欢》双语 R&B 迭代要求提炼的独立 Skill。

## 安装到 Org-Skills
将此 `suno-songwriting/` 文件夹放入 `Org-Skills/skills/`，读取 `skills/suno-songwriting/SKILL.md`；以远程仓库版本为唯一事实源。

## 典型调用
- `用 suno-songwriting 写一首讽刺音乐工业化的歌，男声，怀旧风格。`
- `用 suno-songwriting 把《不喜欢》升级到 v1.1：国语+英文，强化情绪绩效化讽刺。`
- `只把这段 Suno Style Prompt 压缩到 1000 字符以内。`

## 质量检查
```bash
python3 scripts/validate.py examples/buxihuan-v1.1.md --title 不喜欢
python3 scripts/validate.py examples/style-only.md --mode style-only
```

纯文本和结构可自动检查，旋律、演唱自然度与生成音乐质量须实听，不能由静态测试证明。