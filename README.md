# weather-cover-lab

区域降水指数保障的业务资料服务。当前提供资料清单、冻结分页、业务规则查询、描述性概览和咨询档案。

## 环境和运行
Python 3.11，独立镜像按摘要固定为 3.11.14；固定 NumPy 2.2.6、SciPy 1.15.3。当前资料服务仅用标准库，统计计算依赖已在容器中预装。
`python -m pip install --no-index --find-links=vendor/wheels -r requirements.lock` 可在同版本 Linux x86_64 环境离线安装。
所有资料为本地合成记录，不代表真实农户或企业。
`python -m unittest discover -s tests -v` 运行现有回归。
`python -m weather_cover demo` 启动本地来源与咨询服务，读取全部分页、询价、保存并重读一份资料概览；不访问外网，通常数秒结束。
`docker build -t weather-cover-lab:local .` 构建固定 Python 版本环境。
`docker run --rm --network none weather-cover-lab:local` 执行相同的本地浏览流程。

## 持续服务
`python -m weather_cover source --port 8760` 启动业务资料来源。
`python -m weather_cover serve --port 8761 --archive var/reports.sqlite3` 启动咨询与档案服务。
二者可在同一 Linux 容器中运行，通过环回 HTTP 交换资料；无外部服务和数据库要求。

## 内容
`weather_cover/domain.py` 是来源方的业务约束，`provider.py` 和 `client.py` 负责版本化交互。
`overview.py` 仅列出已有资料覆盖，不作效果推断或方案推荐。
`app.py` 提供概览、询价和档案读取，`ledger.py` 以内容标识存档。
数据字段和兼容接口见 `docs/contracts.md`，`data/request.json` 是当前有效的业务查询示例。
