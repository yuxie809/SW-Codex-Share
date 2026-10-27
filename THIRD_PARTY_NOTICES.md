# 代码来源与许可

`src/solidworks/*.py` 来自既有 sw-agent 项目的 CAD 执行层；上游 LICENSE 为 MIT，Copyright (c) 2026 Joseph Robertson，已原样保留在本项目 LICENSE。

`src/session_support.py` 复用该项目 tests/session_support.py；`src/verification.py` 和板件示例依据该项目已运行的 scripts/smoke_modeling.py、model_validation/cad.py 进行独立部署适配。完整图纸识别/采用历史/执行恢复模块不在此发布范围。

发布适配仅调整项目输出目录、模板覆盖和系统目录发现，增加薄 Runtime、stdio MCP、部署与示例入口。原有全局私有配置、账号、聊天及历史模型未复制。

pywin32、MCP Python SDK、Pillow、jsonschema 及其间接依赖由 pip 安装，分别遵循其发布许可。本包不分发 SolidWorks 程序、模板或许可；需用户自行合法安装使用。
