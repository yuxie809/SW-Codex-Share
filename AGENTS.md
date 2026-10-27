# SolidWorks 自然语言建模

这是 Windows 本地 SolidWorks COM 项目。用户以自然语言描述需求，你负责选择并调用项目内现有接口；无需用户理解 Python 或 COM。先读 README.md、docs/CAPABILITIES.md 和 docs/TEST_RESULTS.md。

- 优先复用 `src/solidworks/` 中已验证的 COM 建模接口，不重写框架、不无故增加 GUI、服务或依赖。所有 CAD 调用串行执行，不同时启动多个脚本或 MCP CAD 会话。
- 使用本项目 `.venv/Scripts/python.exe -X utf8`。未初始化时运行 `powershell -ExecutionPolicy Bypass -File setup.ps1`；安装所需依赖已属于用户部署指令，但仍遵守实际运行权限。
- 首次运行 `test_connection.py`。失败就定位 Python、SolidWorks COM 注册、登录/许可证及模板配置；不得用空文件、改扩展名或截图代替模型。
- 优先调用 `examples/plate_with_hole.py` 的参数化入口；普通三维零件或装配需求用现有工具组合。`sw.py --list` 列出接口，`sw.py --schema TOOL_NAME` 查参数。生成短 Python 脚本时将项目 `src` 加入 sys.path，`from runtime import Runtime`，用 `Runtime().call(name, args)`。
- 跨步骤状态必须在同一 Runtime/同一进程保留。也可生成 JSON 调用数组，再用 `sw.py --batch plan.json` 串行执行。不要用多个独立命令拼接依赖草图/特征 ID 的流程。复杂依赖结果的调用用 Python 保存上一步返回 ID。
- 若已在此项目配置 `sw_codex_share` MCP，可直接使用其工具；不得误调用用户原有的其他 SolidWorks MCP。MCP 和 Python 共用相同核心。没有 MCP 也可完整运行，无需安装全局 Skills。
- 用户尺寸默认毫米、角度默认度。现有工具参数已是毫米/度，内部转换为米/弧度，不要二次除以 1000。仅直接使用 COM 时手动将毫米除以 1000、角度转弧度。
- 输出统一保存到项目 `output/`，为每次任务创建独立目录和唯一文件名。Runtime 中显式相对路径从项目根目录解析；例：`output/task_a/part.SLDPRT`。底层直接调用文档模块时，裸文件名从 output 解析。不要覆盖已有成果。
- 模板优先读取 SolidWorks 默认模板，必要时让用户根据 README 配置 `config.local.json` 中的零件/装配体模板路径；不要写死年份、用户名和安装盘符。
- 创建独立任务文档。记录并保护原来打开的文档；仅关闭自己创建/打开的任务文档，不调用 close_all_docs，不退出 SolidWorks。可复用 src/session_support.py 的 OwnedDocuments/TrackingApplication。
- 保存后检查文件真实存在、大小非零；关闭本次文档并重新打开，重建、检查实体/关键尺寸、特征保留及装配引用。复用 src/verification.py 和原生查询工具。创建标准四视图并实际查看，报告任何几何或视觉问题。STEP 导出成功不等于 STEP 已重导入验证。
- 装配体要连同引用零件一起交付，并验证引用可解析。现有简单示例只验证两组件基本装配，不代表机械配合、自由度或运动算例已通过。
- 已有接口不等于已验证功能。根据 docs/CAPABILITIES.md 清楚报告已验证、仅有接口及未支持能力。遇到现有能力不支持的需求，可在现有架构内最小扩展，查明真实 API 签名并运行验证；无法完成时明确说明，不能假装成功。
- 不自动修改用户全局 Codex 配置、账号或系统 COM 注册。不要复制聊天记录、凭据或 SolidWorks 商业模板进仓库。
