"""Validated rectangle + centered through-hole workflow, dimensions in mm."""
import argparse
import json
import math
from pathlib import Path
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from runtime import Runtime, OUTPUT
from session_support import OwnedDocuments, TrackingApplication
from solidworks.com_utils import com_prop
from verification import measure


def run(width=80.0, height=50.0, thickness=10.0, diameter=10.0):
    values = [width,height,thickness,diameter]
    if not all(math.isfinite(v) and v > 0 for v in values) or diameter >= min(width,height):
        raise ValueError('尺寸必须是有限正数，孔径必须小于板宽和板高。')
    folder = OUTPUT/('plate_'+uuid4().hex[:8])
    folder.mkdir(parents=True, exist_ok=False)
    part = folder/(folder.name+'.SLDPRT')
    step = folder/(folder.name+'.step')
    runtime = Runtime()
    runtime.connection.ensure_connection()
    app = runtime.connection.app
    owner = OwnedDocuments(app)
    runtime.connection.app = TrackingApplication(owner)
    report = {'status':'running','dimensions_mm':values,
              'solidworks_revision':runtime.connection.get_sw_version(), 'steps':[]}
    completed = False

    def call(tool, args=None):
        result = runtime.call(tool,args)
        report['steps'].append(tool)
        return result

    def check(stage):
        actual = measure(runtime.connection.get_active_doc())
        report[stage] = actual
        expected_bounds = [-width/2,-height/2,0,width/2,height/2,thickness]
        expected_volume = (width*height-math.pi*(diameter/2)**2)*thickness
        assert actual['rebuild_ok'], actual['rebuild_issues']
        assert actual['body_count'] == 1
        assert len(actual['bounds_mm']) == 6
        assert all(abs(a-b) < 0.02 for a,b in zip(actual['bounds_mm'],expected_bounds)), actual
        assert abs(actual['volume_mm3']-expected_volume) < max(0.05,expected_volume*1e-6), actual
        assert len(actual['cylinders']) == 1, actual
        hole = actual['cylinders'][0]
        assert abs(hole['radius_mm']-diameter/2)<0.01
        assert all(abs(v)<0.01 for v in hole['center_mm'][:2])
        assert abs(abs(hole['axis'][2])-1)<1e-6
        assert abs(hole['length_mm']-thickness)<0.02

    try:
        call('solidworks_new_part')
        call('solidworks_create_sketch',{'plane':'Front'})
        call('solidworks_sketch_rectangle',{'centerX':0,'centerY':0,'width':width,'height':height})
        call('solidworks_exit_sketch')
        boss = call('solidworks_create_extrusion',{'depth':thickness})
        call('solidworks_create_sketch',{'plane':'Front'})
        call('solidworks_sketch_circle',{'centerX':0,'centerY':0,'radius':diameter/2})
        call('solidworks_exit_sketch')
        cut = call('solidworks_create_cut_extrusion',{'depth':thickness,'endCondition':'THROUGH_ALL'})
        check('before_save')
        saved = call('solidworks_save_document',{'path':str(part)})
        call('solidworks_save_document',{'path':str(step)})
        call('solidworks_close_document',{'name':saved['title']})
        call('solidworks_open_document',{'path':str(part)})
        check('after_reopen')
        doc = runtime.connection.get_active_doc()
        for feature in [boss,cut]:
            name = feature['id'].split(':',1)[1]
            assert doc.FeatureByName(name) is not None, 'Saved feature missing: '+name
        previews = call('solidworks_capture_views',{'views':['ISOMETRIC','FRONT','TOP','RIGHT'],
                      'outputDir':str(folder/'previews'),'prefix':'plate'})['files']
        for path in [part,step,*map(Path,previews)]:
            assert path.is_file() and path.stat().st_size > 0
        report['files'] = {str(p.relative_to(ROOT)):p.stat().st_size for p in [part,step,*map(Path,previews)]}
        report['features_preserved'] = True
        completed = True
    except Exception as exc:
        report['error'] = str(exc)
        raise
    finally:
        try:
            owner.close_owned()
            owner.assert_originals_open()
            report['original_documents_preserved'] = True
            if owner.original_active is not None:
                runtime.connection.activate_document(str(com_prop(owner.original_active,'GetTitle')))
        except Exception as exc:
            completed = False
            report['cleanup_error'] = str(exc)
            raise
        finally:
            report['status'] = 'pass' if completed else 'fail'
            (folder/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'status':'pass','report':str((folder/'verification.json').relative_to(ROOT))},ensure_ascii=False))
    return part


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name,default in [('width',80),('height',50),('thickness',10),('diameter',10)]:
        parser.add_argument('--'+name,type=float,default=default)
    run(**vars(parser.parse_args()))
