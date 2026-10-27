# SW-Codex-Share

用自然语言让 Codex 在本机通过 COM API 控制 SolidWorks。复用既有 sw-agent 建模执行层，包含初始化、连接诊断、零件示例、基本装配示例和可选本地 MCP。核心代码采用原项目 MIT 许可证，见 LICENSE。

## 1. 准备软件

需要 Windows 64 位、可正常启动并已授权的桌面 SolidWorks、64 位 Python 3.10+，以及能运行本地命令的 Codex。首次安装 Python 依赖需要联网。本轮实测软件版本和边界见 [测试结果](docs/TEST_RESULTS.md)；没有在另一台电脑完成兼容性验收。

自行安装 Python（[官网](https://www.python.org/downloads/windows/)）、SolidWorks 和 Codex（[官方入口](https://developers.openai.com/codex/app/)）。首次手动打开 SolidWorks，完成许可/首次启动向导，确认可以正常新建一个零件。请使用自己的软件许可和 Codex 登录账号，本项目不提供、不需要原作者的账号、API 密钥或聊天记录。

## 2. 解压并初始化

把完整目录解压到有写入权限的本地文件夹。保留 src、examples 等子目录。用 PowerShell 打开该目录，执行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1
.\.venv\Scripts\python.exe -X utf8 .\test_connection.py
```

setup.ps1 只创建本项目虚拟环境并安装 requirements.txt；不安装 SolidWorks、不改系统 COM 注册、不改全局 Codex 配置。不必激活虚拟环境。PowerShell 的 Bypass 只针对本次脚本进程。

若 Python 自动识别失败，指定自己电脑的解释器：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1 -Python '你的Python安装目录\python.exe'
```

`test_connection.py` 成功输出 `status: pass`，并报告 Python 位数、COM 注册、SolidWorks 内部修订号及模板是否找到。它会优先连接运行中的 SolidWorks，否则尝试启动已注册版本。多版本并存时以 COM 当前注册/运行实例为准，不根据目录名称猜版本。零件模板缺失时失败；装配体模板缺失会明确报告，需配置后才能运行装配示例。

## 3. 首次运行

```powershell
.\.venv\Scripts\python.exe -X utf8 .\examples\plate_with_hole.py
```

默认创建 80×50×10 mm、中心 Ø10 mm 通孔的板，保存 SLDPRT、导出 STEP，关闭并重开原生零件，检查实体、尺寸、孔和特征，生成四视图与 verification.json。所有成果在 `output/plate_随机编号/`，不会覆盖之前的模型。

尺寸可以直接调整：

```powershell
.\.venv\Scripts\python.exe -X utf8 .\examples\plate_with_hole.py --width 100 --height 60 --thickness 12 --diameter 8
.\.venv\Scripts\python.exe -X utf8 .\examples\two_component_assembly.py
```

装配示例创建自己的零件、插入两个实例并保存/重开装配体；包含所有引用文件，未添加机械配合。参数化代码有范围检查，但本轮验证范围以测试结果为准，不代表任意尺寸和复杂形状都已验收。

## 4. 在 Codex 中直接用自然语言

在 Codex 中把解压后的 **SW-Codex-Share 根目录**打开为本地项目，启动聊天，粘贴 [FIRST_PROMPT.md](FIRST_PROMPT.md) 中的提示词。项目 AGENTS.md 会指引 Codex 调用本地 API。默认使用 Python 命令入口，**无需 MCP、全局 Skill 或作者聊天记录**。

例如：“用现有接口创建一个 100×60×12 mm 的矩形板，中间 Ø8 通孔，保存并验证重开。”对装配体也可用自然语言提出需求；Codex 应依据接口和已验证边界执行，不能将存在的接口都当成已验证功能。

接口检查（普通用户无需掌握）：

```powershell
.\.venv\Scripts\python.exe -X utf8 .\sw.py --list
.\.venv\Scripts\python.exe -X utf8 .\sw.py --schema solidworks_create_extrusion
.\.venv\Scripts\python.exe -X utf8 .\sw.py --batch .\plan.json
```

plan.json 是让 Codex 根据任务生成的调用数组，每项格式为 `{"tool":"工具名","args":{}}`；项目未预置这个文件。JSON 计划会在同一进程内顺序执行。更复杂的需求让 Codex 使用 Runtime 编写短脚本，复用现有接口并验证保存重开。框架不内置第二个大模型；自然语言理解由用户自己的 Codex 完成。

## 5. 模板在不同电脑上的处理

优先使用 SolidWorks：工具 → 选项 → 系统选项 → 默认模板中的零件/装配体模板；其次查找当前电脑 ProgramData 下与运行版本匹配的模板。项目不捆绑商业软件模板。

若仍找不到模板，将 config.example.json 复制为 config.local.json，只填写需要覆盖的项目：

```json
{
  "SW_PART_TEMPLATE": "templates/my_part.prtdot",
  "SW_ASSEMBLY_TEMPLATE": "templates/my_assembly.asmdot",
  "SW_FEATUREWORKS_DLL": ""
}
```

路径可以是项目相对路径或自己电脑的绝对路径。把自己有权使用的模板放到相应位置；也可直接填 SolidWorks 安装提供的模板完整路径。环境变量同名设置优先于本地 JSON。无效的显式模板会报错，不会悄悄替换。config.local.json 默认不会进入 Git。

## 6. 可选：重建项目 MCP 配置

默认 Python 入口已经能完成建模。如果希望在 Codex 中使用 MCP 工具，运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup.ps1 -Mcp
```

这会根据**当前解压位置**新建 `.codex/config.toml`，服务名 sw_codex_share，以本项目虚拟环境启动 mcp_server.py。已有配置会停止并提示，不覆盖。配置只属于本项目，按 [OpenAI 官方 MCP 文档](https://learn.chatgpt.com/docs/extend/mcp) 的项目配置方式加载；项目需要得到 Codex 信任。重开该项目聊天后检查 MCP 是否可用。不同客户端可能还需在 MCP 设置中启用该服务。

如果桌面端没有读取项目配置，可在其 MCP 设置中添加本地 stdio 服务：命令填写本项目 `.venv/Scripts/python.exe` 完整路径，参数为 `-X`、`utf8`、本项目 `mcp_server.py` 完整路径。不要导入作者的全局 config.toml。项目移动后，重新生成/更新 MCP 启动路径；虚拟环境也需重建，不要复制另一台电脑的 .venv。

MCP 仅暴露原有 CAD 工具，不暴露任意 Python 执行工具。本轮测试区分“stdio 协议调用通过”与“接收者 Codex 中实际工具发现”，具体见测试结果。

## 7. 常见问题

- `Class not registered`：SolidWorks 未正确安装/COM 未注册。先手动启动，仍失败则用 SolidWorks 官方安装器修复；本项目不会自动更改注册表。
- COM 连接失败：确认 SolidWorks 没有许可证/首次启动/模态对话框阻塞，并使 Codex 与 SolidWorks 使用同一 Windows 登录桌面及相同权限级别。不要仅为解决连接问题盲目提升权限。
- pip 下载失败：检查网络/代理，修复后重跑 setup.ps1。不要使用系统 Python 代替项目虚拟环境运行模型。
- 初始化被中断，虚拟环境不完整：可对本项目环境运行 `python -m venv .venv` 后重跑 setup.ps1；不修改系统环境。
- `PermissionError` 指向临时目录：确认当前进程 TEMP/TMP 可写；若在 Codex 沙箱中，由 Codex 使用项目可写临时目录后重试，不关闭沙箱保护。
- 装配体丢失组件：分享整个任务输出子目录，不能只分享 .SLDASM；保持引用零件的相对目录结构。
- FeatureWorks、复杂曲面、运动、工程图等高级功能：存在接口或原软件支持不等于本发布版已经验证，见能力表。FeatureWorks 可选 DLL 路径覆盖也未在本轮验证。

## 8. 文件与发布

- `src/solidworks/`：原有 COM 执行模块；src/runtime.py 是薄调用入口。
- `setup.ps1`、requirements.txt、test_connection.py：部署与诊断。
- `examples/`：可运行示例；`docs/`：来源、能力和验证边界。
- `output/`：运行产物；ZIP 与 Git 源码不带本机虚拟环境、本地 MCP 配置、聊天记录或账户配置。

可以将此目录中的项目文件上传到自己的 GitHub 仓库，保留 LICENSE 和 THIRD_PARTY_NOTICES.md。此交付没有上传 GitHub。首次部署需要依赖下载，ZIP 不包含 Python、SolidWorks 或离线 wheel 仓库。
