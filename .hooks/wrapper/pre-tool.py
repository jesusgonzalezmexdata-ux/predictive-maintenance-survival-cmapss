#!/usr/bin/env python3
import json, sys
payload = json.load(sys.stdin) if not sys.stdin.isatty() else {}
print(json.dumps({'status':'observed','event':'pre-tool','payload_keys':sorted(payload.keys())}))
