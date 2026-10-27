# 实现检查与移植说明

检查了本机 Codex 的实际 MCP 启动配置、旧版 monolithic MCP server/client、sw-agent 模块化执行层、工程状态账、已运行的 smoke_modeling.py、会话归属保护和全局 solidworks-automation 技能。

实际调用链有三条，不能混为一套：

1. 既有 Codex 全局 MCP：`server.py → SolidWorksClient → win32com/pythoncom → SolidWorks`，工具名 `sw_*`。它存在固定版本模板目录。
2. 既有 sw-agent：`server.py → solidworks/* Tools → SolidWorksConnection → COM`，工具名 `solidworks_*`；有真实板件保存重开和后续有界执行验收记录。
3. 全局 SolidWorks 技能：代理按 SKILL.md 调用 sw_session/sw_part/sw_assembly 等脚本，另带大型 CAD Studio/其他后端；不是当前全局 MCP 的实际 Python 源。

发布版选择第 2 条已有实机验证的执行层，复制全部相互依赖的核心 Python 模块，保留草图与特征跟踪、基准面本地化、原子中性格式导出和文档管理实现。没有复制完整图纸流程、历史采用数据、GUI、其他 CAD 后端或全局 Skill。

新的可重建调用链：

```text
接收者自己的 Codex + 项目 AGENTS.md
  ├─ Python 示例 / sw.py / Runtime.call
  └─ 可选本地 stdio mcp_server.py
        → 相同的 src/runtime.py
        → src/solidworks 原有 Tools 类
        → SolidWorksConnection + win32com/pythoncom
        → 接收者本机 SolidWorks
```

必要的发布适配：

- connection.py：ProgramData 从当前系统发现；增加显式零件/装配体模板覆盖，保留原默认模板读取。
- document_manager.py、geometry_query.py：默认输出改到项目 output；可选 FeatureWorks 默认安装目录从当前 ProgramFiles 构造。
- state_tracker.py：移除示意注释里的绝对路径。
- runtime.py：复用原有模块分派，为独立发布解析项目相对路径及验证参数。
- mcp_server.py：直接使用同一 Runtime，串行 COM，不引入原 server 对完整图纸/恢复包的依赖。
- examples 与 verification：从已跑通 smoke 流程提取矩形通孔板，加入基本装配验收入口；不复制测试专用的大量上游框架。

保留了原有 API 参数和毫米转换实现，未新写第二套 CAD 内核。原项目代码与全局设置未修改。源文件哈希检查结果、依赖隔离与 ZIP 验证见 TEST_RESULTS.md。
