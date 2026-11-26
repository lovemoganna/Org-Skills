# E01 · 原生模型交接

固定输入和验收条件分别见 [原始任务](task.txt) 和 [验收条件](acceptance.json)。任务没有写出两个 Skill 的名字。

从仓库根目录重放：
```sh
node skills/loop/router_v2/evidence/natural-host/e01/baseline.cjs
sha256sum -c skills/loop/router_v2/evidence/natural-host/e01/frozen.sha256
```

基线从 Git 对象 26b4049ee110e2860243c095e5bf1a76cf7f6ae5 加载。两次推进的完整状态和工具不可用对照见 [基线记录](baseline.json)。

正式运行由 workLegion(tools, config).run(task) 启动。当前 Work 模型处理选择和两个待办；分别保存了每个请求和模型原始回复。GitHub 读取的原始回执、步骤依赖与完整分析保存在 [执行轨迹](session/session.json) 中。工作进程和独立评审进程由本次 Work 宿主调起。

首次执行曾使用临时目录；宿主环境切换后目录消失，未取得最终核验回执。保留相同冻结输入，从头做了一次只读重跑，把请求和 checkpoint 存进工作区。本例没有远端写入。可审查的运行以本目录的原始文件为准。

[独立验收结果](result.json) 为 VERIFIED。评审者重新运行固定基线并得到 SHA-256 0aaa32f842c15c711a6016e3744303d83e56bae1d314b871b96b5f019df29edb，逐字比对因果分析与下游输入，检验了替代解释、反证条件和方法适用范围。调度器原始状态仍按约定记录为 COMPLETED_UNVERIFIED。
