"""Claude Code SessionStart adapter. Loads an existing map; never builds one."""
import json
import sys
from .project_map import ProjectMap


def main():
    try:
        event = json.load(sys.stdin)
        if event.get('hook_event_name') != 'SessionStart':
            return 0
        context = ProjectMap(event['cwd']).overview()
        print(json.dumps({'hookSpecificOutput': {
            'hookEventName': 'SessionStart', 'additionalContext': context,
        }}))
    except (ValueError, KeyError, OSError) as error:
        # A missing map should not prevent the coding client from starting.
        print(f'ReqContext orientation unavailable: {error}', file=sys.stderr)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
