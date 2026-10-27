"""Inspect Python, COM registration, running SW version and template discovery."""
import json, platform, struct, sys, winreg
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / 'src'))
from runtime import Runtime

def main():
    with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r'SldWorks.Application\CLSID') as key:
        clsid = winreg.QueryValueEx(key, None)[0]
    with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, 'CLSID\\' + clsid + r'\LocalServer32') as key:
        command = winreg.QueryValueEx(key, None)[0]
    runtime = Runtime()
    runtime.connection.ensure_connection()
    part = runtime.connection.find_template()
    assembly = runtime.connection.find_assembly_template()
    if not part:
        raise RuntimeError('找不到零件模板。请在 SolidWorks 设置默认模板或填写 config.local.json。')
    print(json.dumps({'status':'pass','python':platform.python_version(),
        'bits':struct.calcsize('P')*8, 'com_registered':True,
        'solidworks_revision':runtime.connection.get_sw_version(),
        'com_server':command, 'part_template_found':bool(part),
        'assembly_template_found':bool(assembly),
        'assembly_note':'装配体建模需要装配体模板；没有模板时请配置。'},ensure_ascii=False,indent=2))

if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(json.dumps({'status':'fail','error':str(exc)},ensure_ascii=False),file=sys.stderr)
        sys.exit(1)
