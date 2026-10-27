"""Project entry point; delegates to the original sw-agent CAD modules."""
import json
import os
from pathlib import Path
import pythoncom
from jsonschema import validate
from solidworks import (SolidWorksConnection, StateTracker, SketchingTools,
    ModelingTools, FeatureTools, CutFeatureTools, AppliedFeatureTools,
    PatternTools, HoleFeatureTools, ReferenceGeometryTools, GeometryQueryTools,
    StateQueryTools, DocumentManagerTools, AssemblyTools, ConfigurationTools,
    FeatureTreeTools)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'output'

class Runtime:
    def __init__(self):
        pythoncom.CoInitialize()
        config_path = ROOT / 'config.local.json'
        if config_path.exists():
            config = json.loads(config_path.read_text(encoding='utf-8-sig'))
            for key in ['SW_PART_TEMPLATE', 'SW_ASSEMBLY_TEMPLATE', 'SW_FEATUREWORKS_DLL']:
                if config.get(key) and not os.environ.get(key):
                    os.environ[key] = config[key]
        self.connection = SolidWorksConnection()
        self.tracker = StateTracker()
        self.sketching = SketchingTools(self.connection, self.tracker)
        self.modeling = ModelingTools(self.connection, self.tracker)
        self.modules = [self.sketching, self.modeling,
            FeatureTools(self.connection,self.tracker), CutFeatureTools(self.connection,self.tracker),
            AppliedFeatureTools(self.connection,self.tracker), PatternTools(self.connection,self.tracker),
            HoleFeatureTools(self.connection,self.tracker), ReferenceGeometryTools(self.connection,self.tracker),
            GeometryQueryTools(self.connection,self.tracker), StateQueryTools(self.tracker,self.connection),
            DocumentManagerTools(self.connection,self.tracker), AssemblyTools(self.connection,self.tracker),
            ConfigurationTools(self.connection,self.tracker), FeatureTreeTools(self.connection,self.tracker)]
        self.routes = {}
        self.tools = {}
        for module in self.modules:
            for tool in module.get_tool_definitions():
                self.routes[tool.name] = module
                self.tools[tool.name] = tool

    def call(self, name, args=None):
        args = dict(args or {})
        if name not in self.routes:
            raise ValueError('Unknown tool: ' + name)
        validate(args, self.tools[name].inputSchema)
        # Original file operations take absolute paths; resolve project-relative
        # inputs here so Codex need not know the installation directory.
        for key in ['path', 'outputDir']:
            if key in args:
                p = Path(args[key])
                args[key] = str((ROOT / p).resolve() if not p.is_absolute() else p.resolve())
        self.connection.ensure_connection()
        module = self.routes[name]
        if module is self.modeling:
            result = module.execute(name, args, self.sketching)
        else:
            result = module.execute(name, args)
        if result.startswith('IMAGE_FILE:'):
            return {'image': result.splitlines()[0][11:], 'detail': result.split('\n',1)[-1]}
        return json.loads(result)
