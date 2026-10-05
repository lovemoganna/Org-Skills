# Exploratory Test — Tangle Directory Regression

## Source

真实 Emacs 31.1 失败样本：Python Block 使用 `:dir _org-babel-test`，目标目录不存在时，Babel 在启动 Python 前因设置工作目录失败。

同时发现：`:tangle` 只声明生成目标，`org-babel-execute-buffer` 不会自动完成 Tangle。

## Goal

验证 `org-literate-engineering` 对“生成文件 + 下游工作目录”场景是否明确处理目录创建、Tangle 执行依赖和写入副作用。

## Checks

```text
missing-dir-negative=PASS
mkdirp-contract=PASS
explicit-tangle-dependency=PASS
tangle-write-gate=PASS
runtime-equivalent-module-import=PASS
negative-input-contract=PASS
historical-list-comprehension-default=PASS
historical-list-comprehension-generalization=PASS
native-org-babel=BLOCKED_NO_EMACS
```

## Expected execution order

```text
Org source
→ :mkdirp yes
→ explicit Tangle
→ confirm Artifact exists
→ downstream Block with :dir
→ Assertions
```

## Skill Lab classification

```text
Skill defect: YES
Case-only defect: NO
Test defect: NO
Generalizable: YES
```

Patch required: add `:mkdirp yes` guidance, make Tangle an explicit dependency when downstream code consumes its artifact, and classify Tangle as WRITE.
