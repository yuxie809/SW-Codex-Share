"""Create a simple two-component assembly from the verified plate example.

No mates or mechanical motion are claimed by this example.
"""
import json
from pathlib import Path
import sys
from uuid import uuid4
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from plate_with_hole import run as create_plate
from runtime import Runtime, OUTPUT
from session_support import OwnedDocuments, TrackingApplication
from solidworks.com_utils import com_prop, verify_rebuild


def run():
    part = create_plate()
    runtime = Runtime()
    runtime.connection.ensure_connection()
    app = runtime.connection.app
    owner = OwnedDocuments(app)
    runtime.connection.app = TrackingApplication(owner)
    folder = part.parent
    assembly = folder/('assembly_'+uuid4().hex[:8]+'.SLDASM')
    report = {'status':'running','solidworks_revision':runtime.connection.get_sw_version()}
    completed = False

    def check(stage):
        result = runtime.call('solidworks_list_components')
        assert len(result['components']) == 2, result
        assert all(not c['suppressed'] for c in result['components'])
        assert all(Path(c['filePath']).is_file() for c in result['components'])
        ok, issues = verify_rebuild(runtime.connection.get_active_doc())
        assert ok, issues
        report[stage] = {'component_count':2,'references_exist':True,'rebuild_ok':ok}

    try:
        runtime.call('solidworks_new_assembly')
        runtime.call('solidworks_insert_component',{'path':str(part),'x':0,'y':0,'z':0})
        runtime.call('solidworks_insert_component',{'path':str(part),'x':0,'y':80,'z':0})
        check('before_save')
        saved = runtime.call('solidworks_save_document',{'path':str(assembly)})
        assert assembly.is_file() and assembly.stat().st_size>0
        runtime.call('solidworks_close_document',{'name':saved['title']})
        # Close the owned source part too, so reopen must load its reference.
        owner.close_owned()
        runtime.call('solidworks_open_document',{'path':str(assembly)})
        check('after_reopen')
        report['previews'] = [str(Path(p).relative_to(ROOT)) for p in runtime.call(
            'solidworks_capture_views',{'views':['ISOMETRIC','FRONT','TOP','RIGHT'],
            'outputDir':str(folder/'assembly_previews'),'prefix':'assembly'})['files']]
        report['assembly'] = str(assembly.relative_to(ROOT))
        report['source_part'] = str(part.relative_to(ROOT))
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
            (folder/'assembly_verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'status':'pass','report':str((folder/'assembly_verification.json').relative_to(ROOT))},ensure_ascii=False))


if __name__ == '__main__':
    run()
