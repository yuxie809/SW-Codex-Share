"""List tool schemas or execute a sequential JSON plan in one COM session."""
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / 'src'))
from runtime import Runtime

def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--list', action='store_true')
    group.add_argument('--schema')
    group.add_argument('--batch', type=Path)
    args = parser.parse_args()
    runtime = Runtime()
    if args.list:
        result = sorted(runtime.tools)
    elif args.schema:
        result = runtime.tools[args.schema].model_dump()
    else:
        plan = json.loads(args.batch.read_text(encoding='utf-8-sig'))
        result = []
        for call in plan:
            result.append({'tool':call['tool'], 'result':runtime.call(call['tool'], call.get('args'))})
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(json.dumps({'status':'fail','error':str(exc)},ensure_ascii=False),file=sys.stderr)
        sys.exit(1)
