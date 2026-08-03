#!/usr/bin/env bash
# Diagnose an error via the Reyvin Developer API.
#
# Usage:
#   scripts/diagnose.sh [error_file]     # file contains the stack trace
#   scripts/diagnose.sh -                # read the stack trace from stdin
#
# Env overrides: API (base URL), PROJECT, MODEL

set -euo pipefail

API=${API:-http://127.0.0.1:8000/api/v1}
PROJECT=${PROJECT:-default}
MODEL=${MODEL:-qwen}
SOURCE=${1:-/tmp/reyvin-error.txt}

if [ "$SOURCE" = "-" ]; then
  ERROR_TEXT=$(cat)
elif [ -f "$SOURCE" ]; then
  ERROR_TEXT=$(cat "$SOURCE")
else
  echo "usage: scripts/diagnose.sh [error_file | -]" >&2
  echo "env:   API, PROJECT, MODEL" >&2
  exit 1
fi

PAYLOAD=$(ERROR_TEXT="$ERROR_TEXT" PROJECT="$PROJECT" MODEL="$MODEL" python3 -c "
import json, os
print(json.dumps({
    'error': os.environ['ERROR_TEXT'],
    'file': '',
    'model': os.environ['MODEL'],
    'project': os.environ['PROJECT'],
}))
")

curl -s -X POST "$API/diagnose-error" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD" \
  | python3 -c "
import json, sys

try:
    data = json.load(sys.stdin)
except json.JSONDecodeError:
    print(sys.stdin.read())
    sys.exit(1)

if 'detail' in data:
    print('API error:', data['detail'])
    sys.exit(1)

for frame in data.get('frames', []):
    match = ('-> ' + frame['symbol']) if frame.get('symbol') else '-> no symbol match'
    print('FRAME  %s:%s  %s' % (frame['file'], frame.get('line', 0), match))

diagnosis = data.get('diagnosis', {})
print()
print('ROOT CAUSE:', diagnosis.get('root_cause'))
print('LOCATION:  ', diagnosis.get('location'))
print()
print('EXPLANATION:')
print((diagnosis.get('explanation') or '').strip())
print()
print('FIXES:')
fixes = diagnosis.get('fixes') or []
if not fixes:
    print('  (none)')
for fix in fixes:
    print('  - %s' % fix.get('description'))
    print('    file: %s  symbol: %s' % (fix.get('file'), fix.get('symbol')))
    print('    suggestion: %s' % (fix.get('suggestion') or ''))
print()
print('model: %s  elapsed_ms: %s' % (data.get('model'), data.get('elapsed_ms')))
"
