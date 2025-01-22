#!/usr/bin/env python3

import argparse
import os
import sys
import time
import shutil
from tracetools_analysis.loading import load_file

try:
    from ros2_tools.util import *
except ImportError:
    sys.path.append(os.path.join(os.path.dirname(__file__), "."))
    from util import *
    from trace_converter import *

SESSION_NAME = "ros2_tracer"
START_TRACER_COMMAND = f"ros2 trace start {SESSION_NAME}"
# START_TRACER_COMMAND = f"ros2 trace start {SESSION_NAME} --ust function_entry --ust function_exit --ust callback_entry --ust callback_exit"
STOP_TRACER_COMMAND = f"ros2 trace stop {SESSION_NAME}"
TRACING_DIRECTORY = os.environ["ROS_HOME"] + "/tracing/"
OUTPUT_DIRECTORY = TRACING_DIRECTORY + SESSION_NAME
LTTNG_OUTPUT_DIRECTORY = OUTPUT_DIRECTORY + "/lttng-traces"
TRACE_LOG_FILE = f"trace.log"
OUTPUT_JSON_FILE = f"{OUTPUT_DIRECTORY}/trace.json"
BABEL_TRACE_CONVERT_COMMAND = (
    f"cd {OUTPUT_DIRECTORY} && babeltrace2 . > {TRACE_LOG_FILE}"
)
BABEL_TRACE_CONVERT_COMMAND_LTTNG = (
    f"cd {OUTPUT_DIRECTORY} && babeltrace2 ./lttng-traces > {TRACE_LOG_FILE}"
)
TRACE_LOG_FILE = f"{OUTPUT_DIRECTORY}/{TRACE_LOG_FILE}"
BABEL_TRACE_CONVERT_CTF_COMMAND = f"cd {OUTPUT_DIRECTORY} && babeltrace2 convert --output-format=ctf  --output trace.ctf ."
BABEL_TRACE_LTTNG_CONVERT_CTF_COMMAND = f"cd {OUTPUT_DIRECTORY} && babeltrace2 convert --output-format=ctf  --output trace.ctf ."
ROS2_TRACE_ANALYSIS_COMMAND = f"ros2 trace-analysis process {OUTPUT_DIRECTORY}"

check_command_installed("babeltrace2")
check_command_installed("ros2")


def start_tracing():
    if os.path.exists(OUTPUT_DIRECTORY):
        raise Exception(
            f"ERROR: The tracing output directory: {OUTPUT_DIRECTORY} already exists!"
        )
    run_command(START_TRACER_COMMAND)
    print("Tracing started")

def start_live_trace(session_name, output_dir):
    """Starts a live trace session using LTTng, with a specified output directory."""
    if not session_name:
        print("Provide trace session name")
        return

    if not output_dir:
        print("Provide output directory")
        return

    hostname = subprocess.getoutput("hostname")

    run_command(f"mkdir -p {output_dir}")
    run_command("lttng-relayd --daemonize || true")
    time.sleep(1)
    run_command(f"lttng create {session_name} --live", echo=True, echo_out=True)
    run_command("lttng enable-channel -u ros --subbuf-size=8M", echo=True, echo_out=True)
    run_command("lttng enable-event -c ros -u 'ros2:*'", echo=True, echo_out=True)
    run_command("lttng add-context -u -t vtid -t vpid -t procname", echo=True, echo_out=True)
    run_command("lttng start", echo=True, echo_out=True)
    time.sleep(2)
    run_command("babeltrace2 --input-format=lttng-live net://localhost", echo=True, echo_out=True)
    print(f"\nLive trace URI: net://localhost/host/{hostname}/{session_name}")
    print(f"\n    To monitor this trace use: 'babeltrace2 --input-format=lttng-live net://localhost/host/{hostname}/{session_name}'")
    print("Press any key to stop & destroy")
    input()
    run_command("lttng stop")
    run_command("lttng destroy")
    run_command(f"cp -r ~/lttng-traces {output_dir}")
    run_command(f"rm -rf ~/lttng-traces")

def stop_tracing():
    run_command(STOP_TRACER_COMMAND)
    print("Tracing stopped")
    process_trace()


def timed_trace(seconds):
    start_tracing()
    for remaining in range(seconds, 0, -1):
        print(f"Tracer will stop in {remaining} seconds...")
        time.sleep(1)
    stop_tracing()


def process_trace():
    print(f"Post processing trace in: {OUTPUT_DIRECTORY}")
    run_command(ROS2_TRACE_ANALYSIS_COMMAND)
    run_command(BABEL_TRACE_CONVERT_COMMAND)
    run_command(BABEL_TRACE_CONVERT_CTF_COMMAND)
    write_json_file(OUTPUT_JSON_FILE, trace_log_to_dict(f"{TRACE_LOG_FILE}"))

def process_live_trace():
    print(f"Post processing trace in: {OUTPUT_DIRECTORY}")
    run_command(BABEL_TRACE_CONVERT_COMMAND)
    run_command(BABEL_TRACE_CONVERT_CTF_COMMAND)
    write_json_file(OUTPUT_JSON_FILE, trace_log_to_dict(f"{TRACE_LOG_FILE}"))

def main():

    description = f"""
    ROS 2 Tracer

    The ROS 2 tracer is a session management tool that invokes the `ros2 trace`
    command. It provides basic management of live and fixed-time tracing 
    sessions and auto-conversion of tracing output to json (via procedural 
    parsing) and CTF using `babeltrace2`.

    All tracing output will be placed in the ROS_HOME directory: {OUTPUT_DIRECTORY}
    
    USAGE:
        Before running the ROS2 tracing session first start your ROS2 nodes and
        programs.

        To start a ROS2 tracing session:
            ros2-tracer --start

        To stop a currently active ROS2 tracing session:
            ros2-tracer --stop

        Run a 5 second tracing session, overwrite the last output trace:
            ros2-tracer -t 5 -o
       
       Run a live trace with lttng-live:
           ros2-tracer --live -o

    For more info on the ros2 trace commmand use: `ros2 trace --help`

    """

    parser = argparse.ArgumentParser(description=description, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "-s",
        "--start",
        action="store_true",
        help="Start the ros2 tracer with the session name: {SESSION_NAME}",
    )
    parser.add_argument(
        "-l",
        "--live",
        action="store_true",
        help="Start the ros2 trace with the session name: {SESSION_NAME} as a live session",
    )
    parser.add_argument(
        "-S", "--stop", action="store_true", help="Stop the ros2 tracer"
    )
    parser.add_argument(
        "-o",
        "--overwrite-last-trace",
        action="store_true",
        help="Enable overwite of the last trace, otherwise if a trace exists ros2-tracer will exit with an error.",
    )
    parser.add_argument(
        "-t", "--time", type=int, help="Time in seconds to run the tracer"
    )

    args = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    if args.overwrite_last_trace:
        if os.path.exists(OUTPUT_DIRECTORY) and os.path.isdir(OUTPUT_DIRECTORY):
            shutil.rmtree(OUTPUT_DIRECTORY)
            print(f"Directory {OUTPUT_DIRECTORY} has been deleted.")
    else:
        print(f"ERROR: Output trace directory: {OUTPUT_DIRECTORY} alread exists.", file=sys.stderr)
        print(f"  Delete the output directory: {OUTPUT_DIRECTORY} or rerun the `ros2-tracer` with the `-o` flag.", file=sys.stderr)
        exit(1)


    if args.start:
        try:
            start_tracing()
            print(f"Started tracing with session name: {SESSION_NAME}")
        except Exception as e:
            print(e)
    elif args.time:
        if args.time:
            timed_trace(args.time)

    if args.live:
        try:
            print(f"Starting tracing with session name: {SESSION_NAME}")
            start_live_trace(SESSION_NAME, OUTPUT_DIRECTORY)
            process_live_trace()
            sys.exit(0)
        except Exception as e:
            print(e)
 

    if args.stop:
        stop_tracing()
        print("Stopped tracing.")


if __name__ == "__main__":
    main()
