# 资料与接口约定

## 领域记录
记录粒度为 farmer-year，同年共享站点降雨和市场价格，跨年重复 farmer 不代表新农户。面积单位亩、产量 kg/亩、价格元/kg、成本元/亩；rain_mm=null 表示没有实测，不能结为零降雨。S1 的迁站关系在 stations。POST /quote 接受 station、trigger、limit、insured_area，返回有效保费与赔付口径；POST /detail 同样接受 rain_mm，执行该合同的实测赔付，缺测时维持未结算。新签不支持 retired 站点。历史范围不等于未来极端天气的总体支持。

季末净损失以 reference_net_yuan_mu 为相对基准：基准减去销售收入、加上生产与复种成本，再加保障保费、减赔付。保留有符号差额，负损失表示好于基准；尾部亏损可另列，但不可混用两种口径。

## 冻结来源
GET /manifest 返回 release、digest、row_count、metadata。digest 对完整领域资料按 JSON 键排序、紧凑分隔和 UTF-8 计算 SHA-256。
GET /records 及后续 cursor 请求、POST /quote、POST /detail 都要求 If-Match 等于清单 release，否则返回 412。
游标仅用于所属版本，客户端不能自行猜测页数。source 进程在启动时固定加载 data/release.json。
业务请求成功返回 release、request、result；业务值非法返回 422，游标不合法返回 400，未知地址返回 404。
仅有资料概览与领域核价，不含方案选型、统计推断或预测能力。

## 已有消费接口
GET /health 返回 status=ok；GET /overview 返回 release、digest 与描述性 overview。
POST /quotes 的 JSON 为 release 和 request，结果转发来源方回执。
POST /reports 接受 release、source_digest、kind、result、receipts，返回内容寻址 id；相同内容重复保存得到同一 id。
GET /reports/{id} 返回 id 与原 payload，重启后仍可读，不重算来源资料；不存在时 404。
这些接口的字段和返回类型保持兼容，新增业务可以扩展而不改变旧档案内容。
数据数值保留原始精度；只有领域服务中已标注的金额按对应货币规则处理。
