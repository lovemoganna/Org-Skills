# Dashboard Golden Blueprints

这些文件是结构参考，不是视觉模板。每次只读取与当前 Primary Archetype 对应的一个 Golden；确有独立第二工作流时才读取第二个。

| Archetype | Golden |
|---|---|
| executive | executive-performance.md |
| monitoring | monitoring-state.md |
| investigation | investigation-diagnostic.md |
| operational | operational-queue.md |
| exploration | exploration-comparison.md |
| entity | entity-360.md |

Golden 约束：
- 复用 decision path、viewport hierarchy、interaction pattern；
- 不复制示例字段、阈值、颜色、标题或业务结论；
- 数据不支持的 slot 必须删除，不得填充；
- 同一数据集因任务不同，应允许选择不同 Golden 并得到不同结构。