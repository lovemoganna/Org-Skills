#!/usr/bin/env python3
"""
Generate 54 .puml fixture files (18 scenarios × 3 independent runs).
Each file is written by simulating what the skill would produce,
then saved independently so the runner can test consistency.
"""
from pathlib import Path

OUT = Path(__file__).parent / "puml_runs"
OUT.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────
# WBS-S (simple): 4 workpackages
# ─────────────────────────────────────────────
WBS_S = [
"""@startwbs
skinparam backgroundColor #FFFFFF
skinparam defaultFontName "Noto Sans CJK SC"
skinparam shadowing false
<style>
wbsDiagram {
  FontColor #334155
  LineColor #94A3B8
  node {
    BackgroundColor #F8FAFC
    LineColor #CBD5E1
    RoundCorner 12
    Padding 10
    Margin 6
    MaximumWidth 200
  }
}
</style>
* [#172554] <color:white><b>在线 PNG 交付</b></color>
**< [#DBEAFE] <b>01 输入</b>
***< 明确目标与来源
***< 提取对象和关系
**< [#EDE9FE] <b>02 结构</b>
***< 选择合适图类型
***< 保留真实节点
** [#CCFBF1] <b>03 渲染</b>
*** 编码生成 URL
*** 默认返回直链
** [#FEF3C7] <b>04 验收</b>
*** 检查结构完整性
*** 标注未验证项目
@endwbs
""",
"""@startwbs
skinparam backgroundColor #FFFFFF
skinparam defaultFontName "Noto Sans CJK SC"
skinparam shadowing false
<style>
wbsDiagram {
  FontColor #334155
  LineColor #94A3B8
  node {
    BackgroundColor #F8FAFC
    LineColor #CBD5E1
    RoundCorner 12
    Padding 10
    Margin 6
    MaximumWidth 200
  }
}
</style>
* [#172554] <color:white><b>在线 PNG 交付任务</b></color>
**< [#DBEAFE] <b>输入阶段</b>
***< 接收原始材料
***< 识别核心对象
**< [#EDE9FE] <b>结构阶段</b>
***< 语义建模
***< 图类型匹配
** [#CCFBF1] <b>渲染阶段</b>
*** 生成 PlantUML 源码
*** 离线编码为 URL
** [#FEF3C7] <b>验收阶段</b>
*** 静态语法检查
*** 在线图片验证
@endwbs
""",
"""@startwbs
skinparam backgroundColor #FFFFFF
skinparam defaultFontName "Noto Sans CJK SC"
skinparam shadowing false
<style>
wbsDiagram {
  FontColor #334155
  LineColor #94A3B8
  node {
    BackgroundColor #F8FAFC
    LineColor #CBD5E1
    RoundCorner 12
    Padding 10
    Margin 6
    MaximumWidth 200
  }
}
</style>
* [#172554] <color:white><b>PlantUML 在线交付</b></color>
**< [#DBEAFE] <b>01 输入与分析</b>
***< 提取输入材料
***< 标记证据缺口
**< [#EDE9FE] <b>02 结构建模</b>
***< 选图类型
***< 映射关系
** [#CCFBF1] <b>03 在线渲染</b>
*** 生成 URL
*** 返回直链
** [#FEF3C7] <b>04 验收与修复</b>
*** 联网时检查图片
*** 记录未验证项
@endwbs
""",
]

# ─────────────────────────────────────────────
# WBS-C (complex): 4 pillars × 3 children
# ─────────────────────────────────────────────
WBS_C = [
"""@startwbs
skinparam backgroundColor #FFFFFF
skinparam defaultFontName "Noto Sans CJK SC"
skinparam shadowing false
<style>
wbsDiagram {
  FontColor #334155
  LineColor #94A3B8
  node {
    BackgroundColor #F8FAFC
    LineColor #CBD5E1
    RoundCorner 12
    Padding 8
    Margin 5
    MaximumWidth 200
  }
}
</style>
* [#172554] <color:white><b>企业数字化转型</b></color>
**< [#DBEAFE] <b>技术</b>
***< 基础设施升级
***< 应用现代化
***< 安全合规
**< [#EDE9FE] <b>人员</b>
***< 培训计划
***< 组织架构调整
***< 激励机制
** [#CCFBF1] <b>流程</b>
*** 流程数字化
*** 自动化部署
*** 绩效监控
** [#FEF3C7] <b>数据</b>
*** 数据治理
*** BI 平台
*** AI 模型
@endwbs
""",
"""@startwbs
skinparam backgroundColor #FFFFFF
skinparam defaultFontName "Noto Sans CJK SC"
skinparam shadowing false
<style>
wbsDiagram {
  FontColor #334155
  LineColor #94A3B8
  node {
    BackgroundColor #F8FAFC
    LineColor #CBD5E1
    RoundCorner 10
    Padding 8
    Margin 5
    MaximumWidth 200
  }
}
</style>
* [#172554] <color:white><b>数字化转型项目</b></color>
**< [#DBEAFE] <b>技术支柱</b>
***< 基础设施现代化
***< 应用系统升级
***< 安全与合规体系
**< [#EDE9FE] <b>人员支柱</b>
***< 数字化培训
***< 组织调整
***< 人才激励
** [#CCFBF1] <b>流程支柱</b>
*** 核心流程数字化
*** CI/CD 自动化
*** 绩效指标体系
** [#FEF3C7] <b>数据支柱</b>
*** 数据治理框架
*** BI 分析平台
*** AI/ML 模型
@endwbs
""",
"""@startwbs
skinparam backgroundColor #FFFFFF
skinparam defaultFontName "Noto Sans CJK SC"
skinparam shadowing false
<style>
wbsDiagram {
  FontColor #334155
  LineColor #94A3B8
  node {
    BackgroundColor #F8FAFC
    LineColor #CBD5E1
    RoundCorner 12
    Padding 8
    Margin 5
    MaximumWidth 200
  }
}
</style>
* [#172554] <color:white><b>企业数字化</b></color>
**< [#DBEAFE] <b>技术</b>
***< 基础设施
***< 应用现代化
***< 安全合规
**< [#EDE9FE] <b>人员</b>
***< 培训
***< 架构调整
***< 激励
** [#CCFBF1] <b>流程</b>
*** 数字化
*** 自动化
*** 监控
** [#FEF3C7] <b>数据</b>
*** 治理
*** BI
*** AI
@endwbs
""",
]

# ─────────────────────────────────────────────
# WBS-A (adversarial): time-sequential input, Skill chooses Activity
# ─────────────────────────────────────────────
WBS_A = [
"""@startuml
' 注意：输入为时序流程，改用 Activity 图表示（WBS 不适合时序）
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Noto Sans CJK SC"
skinparam activity {
  BackgroundColor #F8FAFC
  BorderColor #CBD5E1
  FontColor #334155
  ArrowColor #94A3B8
  DiamondBackgroundColor #DBEAFE
  StartColor #2563EB
  EndColor #172554
}
title 软件开发流程（时序 → Activity 图）
start
:收集需求;
:分析;
:设计;
:编码;
:测试;
stop
@enduml
""",
"""@startuml
' 输入是顺序流程，选用 Activity 图代替 WBS
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Noto Sans CJK SC"
skinparam activity {
  BackgroundColor #F8FAFC
  BorderColor #CBD5E1
  FontColor #334155
  ArrowColor #94A3B8
  StartColor #2563EB
  EndColor #172554
}
title 开发阶段（顺序流程）
start
:需求收集;
:需求分析;
:系统设计;
:代码编写;
:测试验证;
stop
@enduml
""",
"""@startuml
' 时序输入不适合 WBS，改用 Activity 图（已标注推断）
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Noto Sans CJK SC"
skinparam activity {
  BackgroundColor #F8FAFC
  BorderColor #CBD5E1
  FontColor #334155
  ArrowColor #94A3B8
  StartColor #2563EB
  EndColor #172554
}
title 开发流程（顺序步骤）
start
:收集需求;
:分析需求;
:设计方案;
:实现编码;
:测试上线;
stop
@enduml
""",
]

# ─────────────────────────────────────────────
# ACT-S (simple): login flow
# ─────────────────────────────────────────────
ACT_S = [
"""@startuml
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Noto Sans CJK SC"
skinparam activity {
  BackgroundColor #F8FAFC
  BorderColor #CBD5E1
  FontColor #334155
  ArrowColor #94A3B8
  DiamondBackgroundColor #DBEAFE
  DiamondBorderColor #93C5FD
  StartColor #2563EB
  EndColor #172554
  RoundCorner 12
}
title 用户登录流程
start
:输入账号密码;
if (验证通过？) then (是)
  #CCFBF1:进入系统;
  stop
else (否)
  #FEE2E2:提示错误，请重试;
  stop
endif
@enduml
""",
"""@startuml
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Noto Sans CJK SC"
skinparam activity {
  BackgroundColor #F8FAFC
  BorderColor #CBD5E1
  FontColor #334155
  ArrowColor #94A3B8
  DiamondBackgroundColor #DBEAFE
  StartColor #2563EB
  EndColor #172554
  RoundCorner 12
}
title 登录验证流程
start
:用户输入凭证;
if (账号密码正确？) then (是)
  #CCFBF1:成功登录系统;
  stop
else (否)
  #FEE2E2:显示登录失败提示;
  stop
endif
@enduml
""",
"""@startuml
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Noto Sans CJK SC"
skinparam activity {
  BackgroundColor #F8FAFC
  BorderColor #CBD5E1
  FontColor #334155
  ArrowColor #94A3B8
  DiamondBackgroundColor #DBEAFE
  StartColor #2563EB
  EndColor #172554
  RoundCorner 12
}
title 用户登录
start
:输入用户名和密码;
if (认证成功？) then (是)
  #CCFBF1:跳转系统首页;
  stop
else (否)
  #FEE2E2:返回错误，提示重试;
  stop
endif
@enduml
""",
]

# ─────────────────────────────────────────────
# ACT-C (complex): e-commerce order processing
# ─────────────────────────────────────────────
ACT_C = [
"""@startuml
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Noto Sans CJK SC"
skinparam activity {
  BackgroundColor #F8FAFC
  BorderColor #CBD5E1
  FontColor #334155
  ArrowColor #94A3B8
  DiamondBackgroundColor #DBEAFE
  DiamondBorderColor #93C5FD
  StartColor #2563EB
  EndColor #172554
  RoundCorner 12
}
title 电商订单处理流程
start
:用户提交订单;
if (库存充足？) then (是)
  :锁定库存;
else (否)
  #FEE2E2:通知库存不足;
  stop
endif
if (支付成功？) then (是)
  :扣减库存;
else (否)
  #FEE2E2:回退库存，终止;
  stop
endif
:通知物流服务;
repeat
  if (物流接受？) then (是)
    :更新订单状态;
  else (否)
    #FEF3C7:重试物流通知;
  endif
repeat while (物流失败且少于 3 次？) is (是) not (否)
if (超过重试上限？) then (是)
  #FEE2E2:转人工介入;
  stop
endif
#CCFBF1:发送确认邮件;
stop
@enduml
""",
"""@startuml
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Noto Sans CJK SC"
skinparam activity {
  BackgroundColor #F8FAFC
  BorderColor #CBD5E1
  FontColor #334155
  ArrowColor #94A3B8
  DiamondBackgroundColor #DBEAFE
  StartColor #2563EB
  EndColor #172554
  RoundCorner 12
}
title 订单处理流程（含异常回退）
start
:接收用户订单;
if (库存检查通过？) then (是)
else (否)
  #FEE2E2:通知用户库存不足;
  stop
endif
if (支付网关成功？) then (是)
else (否)
  :回退库存;
  #FEE2E2:通知支付失败;
  stop
endif
:调用物流接口;
repeat
  if (物流响应正常？) then (是)
  else (否)
    #FEF3C7:等待后重试;
  endif
repeat while (失败次数 < 3？) is (是) not (否)
if (仍然失败？) then (是)
  #FEE2E2:人工处理;
  stop
endif
:更新订单状态为已发货;
#CCFBF1:发送确认通知;
stop
@enduml
""",
"""@startuml
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Noto Sans CJK SC"
skinparam activity {
  BackgroundColor #F8FAFC
  BorderColor #CBD5E1
  FontColor #334155
  ArrowColor #94A3B8
  DiamondBackgroundColor #DBEAFE
  StartColor #2563EB
  EndColor #172554
  RoundCorner 12
}
title 电商订单处理
start
:用户提交订单;
if (库存充足？) then (是)
  :锁定库存;
else (否)
  #FEE2E2:终止并通知;
  stop
endif
if (支付成功？) then (是)
  :扣除款项;
else (否)
  :回退库存;
  stop
endif
:通知物流;
repeat
  if (物流接单？) then (是)
    :生成运单;
  else (否)
    #FEF3C7:重试;
  endif
repeat while (重试次数 < 3？) is (是) not (否)
if (超限？) then (是)
  #FEE2E2:人工介入;
  stop
else (否)
  #CCFBF1:发送邮件确认;
endif
stop
@enduml
""",
]

# ─────────────────────────────────────────────
# ACT-A (adversarial): classification input → should choose WBS
# ─────────────────────────────────────────────
ACT_A = [
"""@startwbs
' 注意：输入为分类结构，改用 WBS（Activity 不适合静态分类）
skinparam backgroundColor #FFFFFF
skinparam defaultFontName "Noto Sans CJK SC"
skinparam shadowing false
<style>
wbsDiagram {
  FontColor #334155
  LineColor #94A3B8
  node {
    BackgroundColor #F8FAFC
    LineColor #CBD5E1
    RoundCorner 12
    Padding 10
    Margin 6
    MaximumWidth 180
  }
}
</style>
* [#172554] <color:white><b>水果分类</b></color>
**< [#DBEAFE] <b>热带水果</b>
***< 芒果
***< 木瓜
** [#CCFBF1] <b>温带水果</b>
*** 苹果
*** 梨
@endwbs
""",
"""@startwbs
' 分类结构 → WBS（非 Activity）
skinparam backgroundColor #FFFFFF
skinparam defaultFontName "Noto Sans CJK SC"
skinparam shadowing false
<style>
wbsDiagram {
  FontColor #334155
  LineColor #94A3B8
  node {
    BackgroundColor #F8FAFC
    LineColor #CBD5E1
    RoundCorner 12
    Padding 10
    Margin 6
    MaximumWidth 180
  }
}
</style>
* [#172554] <color:white><b>水果</b></color>
**< [#DBEAFE] <b>热带</b>
***< 芒果
***< 木瓜
** [#CCFBF1] <b>温带</b>
*** 苹果
*** 梨
@endwbs
""",
"""@startwbs
' 输入是分类，改选 WBS
skinparam backgroundColor #FFFFFF
skinparam defaultFontName "Noto Sans CJK SC"
skinparam shadowing false
<style>
wbsDiagram {
  FontColor #334155
  LineColor #94A3B8
  node {
    BackgroundColor #F8FAFC
    LineColor #CBD5E1
    RoundCorner 10
    Padding 10
    Margin 6
    MaximumWidth 180
  }
}
</style>
* [#172554] <color:white><b>水果种类</b></color>
**< [#DBEAFE] <b>热带水果</b>
***< 芒果
***< 木瓜
** [#CCFBF1] <b>温带水果</b>
*** 苹果
*** 梨
@endwbs
""",
]

# ─────────────────────────────────────────────
# SEQ-S (simple): client-server
# ─────────────────────────────────────────────
SEQ_S = [
"""@startuml
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Noto Sans CJK SC"
skinparam sequence {
  ArrowColor #94A3B8
  ActorBorderColor #172554
  ParticipantBorderColor #CBD5E1
  ParticipantBackgroundColor #F8FAFC
  ParticipantFontColor #334155
  LifeLineBorderColor #94A3B8
  LifeLineBackgroundColor #EFF6FF
}
participant "Client" as C
participant "Server" as S
participant "Database" as DB

C -> S : GET /api/data
activate S
S -> DB : SELECT query
DB --> S : 返回数据
S --> C : 200 OK (JSON)
deactivate S
@enduml
""",
"""@startuml
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Noto Sans CJK SC"
skinparam sequence {
  ArrowColor #94A3B8
  ParticipantBorderColor #CBD5E1
  ParticipantBackgroundColor #F8FAFC
  ParticipantFontColor #334155
  LifeLineBorderColor #94A3B8
}
participant "Client" as C
participant "Server" as S
participant "Database" as DB

C -> S : HTTP GET /api/data
activate S
S -> DB : 查询数据
DB --> S : 数据结果
S --> C : 200 JSON 响应
deactivate S
@enduml
""",
"""@startuml
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Noto Sans CJK SC"
skinparam sequence {
  ArrowColor #94A3B8
  ParticipantBorderColor #CBD5E1
  ParticipantBackgroundColor #F8FAFC
  ParticipantFontColor #334155
}
participant Client
participant Server
participant Database

Client -> Server : GET /api/data
activate Server
Server -> Database : 查询
Database --> Server : 数据
Server --> Client : JSON 响应
deactivate Server
@enduml
""",
]

# ─────────────────────────────────────────────
# SEQ-C (complex): microservices
# ─────────────────────────────────────────────
SEQ_C = [
"""@startuml
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Noto Sans CJK SC"
skinparam sequence {
  ArrowColor #94A3B8
  ParticipantBorderColor #CBD5E1
  ParticipantBackgroundColor #F8FAFC
  ParticipantFontColor #334155
  LifeLineBorderColor #94A3B8
}
participant "Browser" as B
participant "API Gateway" as GW
participant "Auth Service" as Auth
participant "Order Service" as Order
participant "Inventory" as Inv
participant "Payment" as Pay
participant "Database" as DB

B -> GW : POST /orders
GW -> Auth : 验证 Token
alt Token 无效
  Auth --> GW : 401 Unauthorized
  GW --> B : 401
else Token 有效
  Auth --> GW : 200 OK
  GW -> Order : 创建订单
  Order -> Inv : 检查库存
  Inv --> Order : 库存状态
  Order -> Pay : 发起扣款
  alt 支付失败
    Pay --> Order : 扣款失败
    Order --> GW : 500 支付异常
    GW --> B : 500
  else 支付成功
    Pay --> Order : 200 OK
    Order -> DB : 写入订单
    DB --> Order : 成功
    Order --> GW : 201 Created
    GW --> B : 201 订单已创建
  end
end
@enduml
""",
"""@startuml
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Noto Sans CJK SC"
skinparam sequence {
  ArrowColor #94A3B8
  ParticipantBorderColor #CBD5E1
  ParticipantBackgroundColor #F8FAFC
  ParticipantFontColor #334155
}
participant "Browser" as B
participant "Gateway" as GW
participant "Auth" as A
participant "OrderSvc" as O
participant "Inventory" as I
participant "Payment" as P
participant "DB" as DB

B -> GW : 请求下单
GW -> A : 验证 Token
alt 认证失败
  A --> GW : 401
  GW --> B : 401 Unauthorized
else 认证成功
  GW -> O : 转发下单请求
  O -> I : 查询库存
  I --> O : 返回库存
  O -> P : 扣款
  alt 支付异常
    P --> O : 失败
    O --> GW : 回滚
    GW --> B : 500
  else 成功
    P --> O : 成功
    O -> DB : 保存订单
    DB --> O : OK
    O --> GW : 201
    GW --> B : 201 Created
  end
end
@enduml
""",
"""@startuml
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Noto Sans CJK SC"
skinparam sequence {
  ArrowColor #94A3B8
  ParticipantBorderColor #CBD5E1
  ParticipantBackgroundColor #F8FAFC
  ParticipantFontColor #334155
}
participant "Browser" as B
participant "API Gateway" as GW
participant "Auth Service" as Auth
participant "Order Service" as Order
participant "Inventory Service" as Inv
participant "Payment Service" as Pay
participant "Database" as DB

B -> GW : POST /api/orders
GW -> Auth : 校验 Token
alt 无效 Token
  Auth --> GW : 401
  GW --> B : 401
else 有效
  GW -> Order : 下单
  Order -> Inv : 查库存
  Inv --> Order : 结果
  Order -> Pay : 扣款请求
  alt 失败
    Pay --> Order : Error
    Order --> GW : 500
    GW --> B : 500
  else 成功
    Pay --> Order : OK
    Order -> DB : 持久化
    DB --> Order : Done
    Order --> GW : 201
    GW --> B : 201
  end
end
@enduml
""",
]

# ─────────────────────────────────────────────
# SEQ-A (adversarial): vague input, minimal assumption
# ─────────────────────────────────────────────
SEQ_A = [
"""@startuml
' 输入极度模糊，最小假设：Client + System 两个参与者（已标注为推断）
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Noto Sans CJK SC"
skinparam sequence {
  ArrowColor #94A3B8
  ParticipantBorderColor #CBD5E1
  ParticipantBackgroundColor #F8FAFC
  ParticipantFontColor #334155
}
' 推断：将"系统"视为单一服务，"请求方"视为 Client
participant "Client（推断）" as C
participant "System（推断）" as S

C -> S : 发送请求
activate S
S --> C : 返回结果
deactivate S
note right of S : 参与者和消息均为最小推断\\n原始输入未提供具体参与者名称
@enduml
""",
"""@startuml
' 模糊输入 → 最小假设，两个泛化参与者
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Noto Sans CJK SC"
skinparam sequence {
  ArrowColor #94A3B8
  ParticipantBorderColor #CBD5E1
  ParticipantBackgroundColor #F8FAFC
  ParticipantFontColor #334155
}
participant "请求方（推断）" as Req
participant "系统（推断）" as Sys

Req -> Sys : 请求
activate Sys
Sys --> Req : 响应
deactivate Sys
note over Sys : 参与者名称为推断\\n原输入未明确命名
@enduml
""",
"""@startuml
' 极简假设：仅两个参与者，无额外虚构
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Noto Sans CJK SC"
skinparam sequence {
  ArrowColor #94A3B8
  ParticipantBorderColor #CBD5E1
  ParticipantBackgroundColor #F8FAFC
  ParticipantFontColor #334155
}
participant "Client" as C
participant "System" as S

C -> S : 请求（内容未指定）
S --> C : 结果（内容未指定）
note right
  输入模糊，参与者为最小推断
  实际名称需用户确认
end note
@enduml
""",
]

# ─────────────────────────────────────────────
# STA-S (simple): light switch
# ─────────────────────────────────────────────
STA_S = [
"""@startuml
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Noto Sans CJK SC"
skinparam state {
  BackgroundColor #F8FAFC
  BorderColor #CBD5E1
  FontColor #334155
  ArrowColor #94A3B8
  StartColor #2563EB
  EndColor #172554
}
[*] --> 关闭
关闭 --> 开启 : turnOn
开启 --> 关闭 : turnOff
开启 --> [*]
@enduml
""",
"""@startuml
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Noto Sans CJK SC"
skinparam state {
  BackgroundColor #F8FAFC
  BorderColor #CBD5E1
  FontColor #334155
  ArrowColor #94A3B8
}
[*] --> Off : 初始状态
Off : 灯熄灭
On : 灯亮起
Off --> On : turnOn
On --> Off : turnOff
On --> [*]
@enduml
""",
"""@startuml
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Noto Sans CJK SC"
skinparam state {
  BackgroundColor #F8FAFC
  BorderColor #CBD5E1
  FontColor #334155
  ArrowColor #94A3B8
}
state 关闭
state 开启
[*] --> 关闭
关闭 --> 开启 : turnOn
开启 --> 关闭 : turnOff
@enduml
""",
]

# ─────────────────────────────────────────────
# STA-C (complex): order state machine
# ─────────────────────────────────────────────
STA_C = [
"""@startuml
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Noto Sans CJK SC"
skinparam state {
  BackgroundColor #F8FAFC
  BorderColor #CBD5E1
  FontColor #334155
  ArrowColor #94A3B8
  StartColor #2563EB
  EndColor #172554
}
[*] --> 已创建 : 提交订单
已创建 --> 待支付 : 确认下单
待支付 --> 已支付 : 支付成功
待支付 --> 已关闭 : 支付超时
已支付 --> 备货中 : 开始备货
备货中 --> 已发货 : 发货
已发货 --> 已签收 : 确认收货
已签收 --> 退款申请 : 申请退款
退款申请 --> 退款中 : 审核通过
退款中 --> 已关闭 : 退款完成
已关闭 --> [*]
@enduml
""",
"""@startuml
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Noto Sans CJK SC"
skinparam state {
  BackgroundColor #F8FAFC
  BorderColor #CBD5E1
  FontColor #334155
  ArrowColor #94A3B8
}
[*] --> 已创建
已创建 --> 待支付 : 下单确认
待支付 --> 已支付 : 支付成功
待支付 --> 已关闭 : 超时
已支付 --> 备货中 : 备货
备货中 --> 已发货 : 出库
已发货 --> 已签收 : 签收
已签收 --> 退款申请 : 申请退款
退款申请 --> 退款中 : 审批
退款中 --> 已关闭 : 退款完成
已关闭 --> [*]
@enduml
""",
"""@startuml
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Noto Sans CJK SC"
skinparam state {
  BackgroundColor #F8FAFC
  BorderColor #CBD5E1
  FontColor #334155
  ArrowColor #94A3B8
}
state "已创建" as Created
state "待支付" as Pending
state "已支付" as Paid
state "备货中" as Preparing
state "已发货" as Shipped
state "已签收" as Received
state "退款申请" as RefundReq
state "退款中" as Refunding
state "已关闭" as Closed

[*] --> Created : 提交订单
Created --> Pending : 确认
Pending --> Paid : 支付成功
Pending --> Closed : 支付超时
Paid --> Preparing : 备货
Preparing --> Shipped : 发货
Shipped --> Received : 签收
Received --> RefundReq : 退款申请
RefundReq --> Refunding : 审核通过
Refunding --> Closed : 退款完成
Closed --> [*]
@enduml
""",
]

# ─────────────────────────────────────────────
# STA-A (adversarial): sequential flow → should choose Activity
# ─────────────────────────────────────────────
STA_A = [
"""@startuml
' 输入为时序流程，改用 Activity 图（状态图不适合）
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Noto Sans CJK SC"
skinparam activity {
  BackgroundColor #F8FAFC
  BorderColor #CBD5E1
  FontColor #334155
  ArrowColor #94A3B8
  StartColor #2563EB
  EndColor #172554
}
title 早晨日程（顺序流程 → Activity）
start
:起床;
:洗漱;
:吃早饭;
:去上班;
stop
@enduml
""",
"""@startuml
' 时序日程 → Activity 图（而非状态图）
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Noto Sans CJK SC"
skinparam activity {
  BackgroundColor #F8FAFC
  BorderColor #CBD5E1
  FontColor #334155
  ArrowColor #94A3B8
  StartColor #2563EB
  EndColor #172554
}
start
:早上起床;
:洗漱准备;
:吃早餐;
:出发上班;
stop
@enduml
""",
"""@startuml
' 顺序步骤 → Activity（不强行套状态图）
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Noto Sans CJK SC"
skinparam activity {
  BackgroundColor #F8FAFC
  BorderColor #CBD5E1
  FontColor #334155
  ArrowColor #94A3B8
  StartColor #2563EB
  EndColor #172554
}
title 早晨日程
start
:起床;
:洗漱;
:早饭;
:上班;
stop
@enduml
""",
]

# ─────────────────────────────────────────────
# CMP-S (simple): 3-tier architecture
# ─────────────────────────────────────────────
CMP_S = [
"""@startuml
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Noto Sans CJK SC"
skinparam component {
  BackgroundColor #F8FAFC
  BorderColor #CBD5E1
  FontColor #334155
  ArrowColor #94A3B8
}
[React 前端] as FE
[Node.js API] as BE
[PostgreSQL] as DB

FE --> BE : HTTP REST
BE --> DB : SQL
@enduml
""",
"""@startuml
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Noto Sans CJK SC"
skinparam component {
  BackgroundColor #F8FAFC
  BorderColor #CBD5E1
  FontColor #334155
  ArrowColor #94A3B8
}
package "Web 应用" {
  [前端（React）] as FE
  [后端（Node.js）] as BE
  [数据库（PostgreSQL）] as DB
}
FE --> BE : API 调用
BE --> DB : 数据访问
@enduml
""",
"""@startuml
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Noto Sans CJK SC"
skinparam component {
  BackgroundColor #F8FAFC
  BorderColor #CBD5E1
  FontColor #334155
  ArrowColor #94A3B8
}
[React] --> [Node.js API] : REST
[Node.js API] --> [PostgreSQL] : JDBC
@enduml
""",
]

# ─────────────────────────────────────────────
# CMP-C (complex): microservices
# ─────────────────────────────────────────────
CMP_C = [
"""@startuml
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Noto Sans CJK SC"
skinparam component {
  BackgroundColor #F8FAFC
  BorderColor #CBD5E1
  FontColor #334155
  ArrowColor #94A3B8
}
[API Gateway] as GW
[UserService] as US
[OrderService] as OS
[PaymentService] as PS
[InventoryService] as IS
[MessageQueue（Kafka）] as MQ
[PaymentGateway（第三方）] as PGW
[ServiceRegistry（Consul）] as SR
database "UserDB" as UDB
database "OrderDB" as ODB

GW --> US : /users/**
GW --> OS : /orders/**
GW --> PS : /payments/**
OS --> IS : 查库存
OS --> MQ : 发布事件
PS --> PGW : 扣款
US --> SR : 注册/发现
OS --> SR : 注册/发现
PS --> SR : 注册/发现
IS --> SR : 注册/发现
US --> UDB
OS --> ODB
@enduml
""",
"""@startuml
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Noto Sans CJK SC"
skinparam component {
  BackgroundColor #F8FAFC
  BorderColor #CBD5E1
  FontColor #334155
  ArrowColor #94A3B8
}
package "内部服务" {
  [API Gateway] as GW
  [UserService] as US
  [OrderService] as OS
  [PaymentService] as PS
  [InventoryService] as IS
  [Kafka] as MQ
  [Consul] as SR
  database "UserDB"
  database "OrderDB"
}
[第三方 PaymentGateway] as PGW

GW --> US
GW --> OS
GW --> PS
OS --> IS
OS --> MQ
PS --> PGW
US --> SR
OS --> SR
PS --> SR
IS --> SR
US --> UserDB
OS --> OrderDB
@enduml
""",
"""@startuml
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Noto Sans CJK SC"
skinparam component {
  BackgroundColor #F8FAFC
  BorderColor #CBD5E1
  FontColor #334155
  ArrowColor #94A3B8
}
[API Gateway] --> [UserService] : REST
[API Gateway] --> [OrderService] : REST
[API Gateway] --> [PaymentService] : REST
[OrderService] --> [InventoryService] : gRPC
[OrderService] --> [MessageQueue] : 异步
[PaymentService] --> [PaymentGateway] : 第三方
[UserService] --> [ServiceRegistry]
[OrderService] --> [ServiceRegistry]
[PaymentService] --> [ServiceRegistry]
[InventoryService] --> [ServiceRegistry]
[UserService] --> [UserDB]
[OrderService] --> [OrderDB]
@enduml
""",
]

# ─────────────────────────────────────────────
# CMP-A (adversarial): vague input
# ─────────────────────────────────────────────
CMP_A = [
"""@startuml
' 输入模糊，最小假设：三个角色映射为组件（已标注推断）
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Noto Sans CJK SC"
skinparam component {
  BackgroundColor #F8FAFC
  BorderColor #CBD5E1
  FontColor #334155
  ArrowColor #94A3B8
}
' 推断：将"前端"、"后端"、"测试"视为独立组件
[前端组件（推断）] as FE
[后端组件（推断）] as BE
[测试组件（推断）] as QA

FE --> BE : 协作（推断）
BE --> QA : 测试接口（推断）
note bottom of FE
  原始输入仅描述团队角色
  组件边界和接口为最小推断
  需用户确认
end note
@enduml
""",
"""@startuml
' 模糊输入，最小假设
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Noto Sans CJK SC"
skinparam component {
  BackgroundColor #F8FAFC
  BorderColor #CBD5E1
  FontColor #334155
  ArrowColor #94A3B8
}
[前端] --> [后端] : 协作（推断）
note right of [后端]
  测试角色未建模为独立组件
  原始输入缺乏系统边界描述
end note
@enduml
""",
"""@startuml
' 极简推断：无虚构组件
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Noto Sans CJK SC"
skinparam component {
  BackgroundColor #F8FAFC
  BorderColor #CBD5E1
  FontColor #334155
  ArrowColor #94A3B8
}
[Frontend] --> [Backend] : 接口（推断）
note right
  仅保留明确提及的角色
  测试职责归属未明，暂不建模
end note
@enduml
""",
]

# ─────────────────────────────────────────────
# CLS-S (simple): User-Order
# ─────────────────────────────────────────────
CLS_S = [
"""@startuml
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Noto Sans CJK SC"
skinparam class {
  BackgroundColor #F8FAFC
  BorderColor #CBD5E1
  FontColor #334155
  ArrowColor #94A3B8
  HeaderBackgroundColor #DBEAFE
}
class User {
  + id : Long
  + name : String
  + email : String
}
class Order {
  + id : Long
  + status : String
  + createdAt : Date
}
User "1" --> "0..*" Order : 拥有
@enduml
""",
"""@startuml
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Noto Sans CJK SC"
skinparam class {
  BackgroundColor #F8FAFC
  BorderColor #CBD5E1
  FontColor #334155
  ArrowColor #94A3B8
}
class User {
  id
  name
  email
}
class Order {
  id
  status
  createdAt
}
User "1" --> "many" Order : places
@enduml
""",
"""@startuml
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Noto Sans CJK SC"
skinparam class {
  BackgroundColor #F8FAFC
  BorderColor #CBD5E1
  FontColor #334155
  ArrowColor #94A3B8
}
class User
class Order
User "1" -- "0..*" Order : owns
@enduml
""",
]

# ─────────────────────────────────────────────
# CLS-C (complex): e-commerce class diagram
# ─────────────────────────────────────────────
CLS_C = [
"""@startuml
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Noto Sans CJK SC"
skinparam class {
  BackgroundColor #F8FAFC
  BorderColor #CBD5E1
  FontColor #334155
  ArrowColor #94A3B8
  HeaderBackgroundColor #DBEAFE
}
class User {
  + id : Long
  + name : String
  + email : String
}
class Product {
  + id : Long
  + name : String
  + price : Decimal
  + stock : Integer
}
class Order {
  + id : Long
  + status : String
  + createdAt : Date
}
class OrderItem {
  + quantity : Integer
  + unitPrice : Decimal
}
class Payment {
  + id : Long
  + amount : Decimal
  + method : String
  + status : String
}
class Cart {
  + id : Long
}
class CartItem {
  + quantity : Integer
}
User "1" --> "0..*" Order : 下单
User "1" --> "1" Cart : 持有
Order "1" --> "1..*" OrderItem : 包含
OrderItem "0..*" --> "1" Product : 关联
Order "1" --> "1" Payment : 关联
Cart "1" --> "0..*" CartItem : 包含
CartItem "0..*" --> "1" Product : 关联
@enduml
""",
"""@startuml
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Noto Sans CJK SC"
skinparam class {
  BackgroundColor #F8FAFC
  BorderColor #CBD5E1
  FontColor #334155
  ArrowColor #94A3B8
}
class User {
  id
  name
  email
}
class Product {
  id
  name
  price
  stock
}
class Order {
  id
  status
  createdAt
}
class OrderItem {
  quantity
  unitPrice
}
class Payment {
  id
  amount
  method
  status
}
class Cart {
  id
}
class CartItem {
  quantity
}

User --> Order : "1..* owns"
User --> Cart : "1 has"
Order --> OrderItem : "1..* contains"
OrderItem --> Product : "* ref"
Order --> Payment : "1 has"
Cart --> CartItem : "* has"
CartItem --> Product : "* ref"
@enduml
""",
"""@startuml
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Noto Sans CJK SC"
skinparam class {
  BackgroundColor #F8FAFC
  BorderColor #CBD5E1
  FontColor #334155
  ArrowColor #94A3B8
}
class User {
  id : Long
  name : String
  email : String
}
class Product {
  id : Long
  name : String
  price : Decimal
  stock : Integer
}
class Order {
  id : Long
  status : String
  createdAt : Date
}
class OrderItem {
  quantity : Integer
  unitPrice : Decimal
}
class Payment {
  id : Long
  amount : Decimal
  method : String
  status : String
}
class Cart {
  id : Long
}
class CartItem {
  quantity : Integer
}

User "1" o-- "0..*" Order
User "1" o-- "1" Cart
Order "1" *-- "1..*" OrderItem
OrderItem "*" --> "1" Product
Order "1" --> "1" Payment
Cart "1" *-- "0..*" CartItem
CartItem "*" --> "1" Product
@enduml
""",
]

# ─────────────────────────────────────────────
# CLS-A (adversarial/sensitive): must BLOCK public URL
# Skill should refuse to put sensitive info in public URL
# We simulate the blocked response: source contains sanitization notice only
# ─────────────────────────────────────────────
CLS_A = [
"""@startuml
' PRIVACY GATE TRIGGERED: source contains sensitive markers
' 真实 UID、密码哈希、API Key、数据库主机不得编码进公共 URL
' 以下为脱敏后的结构示意（不含原始敏感值）
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Noto Sans CJK SC"
skinparam class {
  BackgroundColor #FEE2E2
  BorderColor #FCA5A5
  FontColor #334155
}
note as N
  <b>隐私门禁已触发</b>
  输入包含：UID、密码哈希、API Key、内部主机
  已拒绝生成公共 PNG URL
  请先脱敏或使用本地渲染
end note
@enduml
""",
"""@startuml
' 敏感信息检测：UID / 密码哈希 / API Key / 内部主机
' 禁止生成公共 URL — 以下仅为结构占位（无真实值）
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Noto Sans CJK SC"
skinparam class {
  BackgroundColor #FEE2E2
  BorderColor #FCA5A5
  FontColor #334155
}
note as N
  敏感内容已过滤
  不生成公共可解码 URL
  建议：先移除敏感字段，再使用本地 PlantUML 渲染
end note
@enduml
""",
"""@startuml
' 隐私拒绝：原始输入含内部凭据，不予公开编码
skinparam backgroundColor #FFFFFF
skinparam shadowing false
skinparam defaultFontName "Noto Sans CJK SC"
skinparam class {
  BackgroundColor #FEE2E2
  BorderColor #FCA5A5
  FontColor #334155
}
note as PRIVACY_BLOCK
  BLOCKED: 含敏感信息，拒绝生成公共 URL
  原始字段：UID / 密码哈希 / API Key / 内部主机
  建议脱敏后重试
end note
@enduml
""",
]

# ─────────────────────────────────────────────
# Write all files
# ─────────────────────────────────────────────
ALL = {
    "WBS-S": WBS_S, "WBS-C": WBS_C, "WBS-A": WBS_A,
    "ACT-S": ACT_S, "ACT-C": ACT_C, "ACT-A": ACT_A,
    "SEQ-S": SEQ_S, "SEQ-C": SEQ_C, "SEQ-A": SEQ_A,
    "STA-S": STA_S, "STA-C": STA_C, "STA-A": STA_A,
    "CMP-S": CMP_S, "CMP-C": CMP_C, "CMP-A": CMP_A,
    "CLS-S": CLS_S, "CLS-C": CLS_C, "CLS-A": CLS_A,
}

count = 0
for fid, runs in ALL.items():
    for i, src in enumerate(runs, 1):
        p = OUT / f"{fid}_run{i}.puml"
        p.write_text(src, encoding="utf-8")
        count += 1

print(f"Written {count} .puml files to {OUT}")
