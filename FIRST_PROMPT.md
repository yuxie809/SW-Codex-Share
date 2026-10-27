# 接收者首次打开 Codex 的提示词

复制以下内容到在本项目根目录打开的 Codex 本地聊天：

```text
请读取本项目 AGENTS.md、README.md、docs/CAPABILITIES.md 和 docs/TEST_RESULTS.md。
我授权你为本项目创建独立 Python 虚拟环境并安装 requirements.txt 中的依赖。
先检查本机 Python、SolidWorks COM 和模板；必要时运行 setup.ps1 和 test_connection.py。
优先复用本项目 src/solidworks 中现有的 COM 建模接口，不重新开发框架。
先运行已经验证的 plate_with_hole 示例：80×50×10 mm 矩形板，中心 Ø10 mm 通孔。
将所有成果保存到项目 output 的独立目录，验证原生文件保存并重新打开、尺寸、实体及特征，并查看四视图。
保留我原来打开的文档，不修改全局 Codex 配置或系统注册表。
明确报告通过、失败和未验证内容；若本机有权限、软件许可或模板问题，请给出具体原因。
此后我会直接用自然语言描述零件或装配体需求，请继续使用本项目现有接口执行。
```
