#!/usr/bin/env bash

set -euo pipefail
echoerr (){ printf "%s" "$@" >&2;}
exiterr (){ printf "%s\n" "$@" >&2; exit 1;}

SCRIPT_DIRECTORY="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

TRACE_DIRECTORY=/opt/trace-compass/tracing_logs/
TRACE_DIRECTORY=$(find "${TRACE_DIRECTORY}" -type f -name metadata -print -quit 2>/dev/null)



./tracecompass --cli --open "${TRACE_DIRECTORY}"
