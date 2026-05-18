#!/usr/bin/env python

from pathlib import Path
from argparse import ArgumentParser, Namespace, ArgumentDefaultsHelpFormatter
import subprocess
import traceback
import threading
from flask import Flask, jsonify
import time
from chris_plugin import chris_plugin, PathMapper
from loguru import logger
import sys
import os
import socket

shutdown_flag = False
app = Flask(__name__)
LOG             = logger.debug
logger_format = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> │ "
    "<level>{level: <5}</level> │ "
    "<yellow>{name: >28}</yellow>::"
    "<cyan>{function: <30}</cyan> @"
    "<cyan>{line: <4}</cyan> ║ "
    "<level>{message}</level>"
)
logger.remove()
logger.opt(colors = True)
logger.add(sys.stderr, format=logger_format)

__version__ = '1.1.3'

DISPLAY_TITLE = r"""
       _             _ _                         _        __          
      | |           | | |                       (_)      / _|         
 _ __ | |______ ___ | | | __ _ _ __ ___   __ _   _ _ __ | |_ ___ _ __ 
| '_ \| |______/ _ \| | |/ _` | '_ ` _ \ / _` | | | '_ \|  _/ _ \ '__|
| |_) | |     | (_) | | | (_| | | | | | | (_| | | | | | | ||  __/ |   
| .__/|_|      \___/|_|_|\__,_|_| |_| |_|\__,_| |_|_| |_|_| \___|_|   
| |                                         ______                    
|_|                                        |______|                   
"""


parser = ArgumentParser(description='A ChRIS plugin to run an ollama server ',
                        formatter_class=ArgumentDefaultsHelpFormatter)
parser.add_argument('-p', '--prompt', default='test', type=str,
                    help='input prompt for the model')
parser.add_argument('-m', '--model', default='llama3', type=str,
                    help='specify which ollama model to use')
parser.add_argument('-s', '--serviceMode', default=False, action="store_true",
                    help='If specified as true, keep the ollama server running.')
parser.add_argument('-t', '--time', default=5, type=int,
                    help='wait time (in seconds) for the ollama server to be ready for inference')
parser.add_argument('-V', '--version', action='version',
                    version=f'%(prog)s {__version__}')
def preamble_show(options: Namespace) -> None:
    """
    Just show some preamble "noise" in the output terminal
    """
    LOG(DISPLAY_TITLE)
    LOG("plugin arguments...")
    for k,v in options.__dict__.items():
         LOG("%25s:  [%s]" % (k, v))
    LOG("")
    LOG("base environment...")
    for k,v in os.environ.items():
         LOG("%25s:  [%s]" % (k, v))
    LOG("")

# The main function of this *ChRIS* plugin is denoted by this ``@chris_plugin`` "decorator."
# Some metadata about the plugin is specified here. There is more metadata specified in setup.py.
#
# documentation: https://fnndsc.github.io/chris_plugin/chris_plugin.html#chris_plugin
@chris_plugin(
    parser=parser,
    title='A ChRIS plugin to run an `ollama` server ',
    category='',                 # ref. https://chrisstore.co/plugins
    min_memory_limit='100Mi',    # supported units: Mi, Gi
    min_cpu_limit='1000m',       # millicores, e.g. "1000m" = 1 CPU core
    min_gpu_limit=0              # set min_gpu_limit=1 to enable GPU
)
def main(options: Namespace, inputdir: Path, outputdir: Path):

    preamble_show(options)

    # start ollama
    start_ollama(options.time)

    # test ollama server
    inference = test_ollama(options.model, options.prompt)

    # save results to output files
    output_file_path = outputdir / 'inference.txt'
    with open(output_file_path, 'w') as f:
        f.write(inference)

    # keep server alive logic
    if options.serviceMode:

        # expose container ip for client programs to reach ollama server API endpoints for inference
        ip_address = socket.gethostbyname(socket.gethostname())
        LOG(f"Container IP: {ip_address}")

        # start control API
        threading.Thread(target=run_control_server, daemon=True).start()
        try:
            while not shutdown_flag:
                time.sleep(1)
        except KeyboardInterrupt:
            LOG(f"Shutting down...")

def test_ollama(model: str, prompt: str) -> str:
    cmd = ["ollama", "run", model, prompt]

    LOG(f'Running command: {" ".join(cmd)}')

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        output, _ = process.communicate()

        if process.returncode != 0:
            LOG(f"Ollama inference failed (exit code {process.returncode})")
        else:
            LOG(f"Exit code: {process.returncode}")

        LOG(output)

        return output

    except FileNotFoundError:
        msg = "ERROR: Ollama executable not found"
        LOG(msg)
        return msg

    except Exception:
        traceback.print_exc()
        return "ERROR: unexpected exception"


def start_ollama(wait_time: int):
    process = subprocess.Popen(
        ["ollama", "serve"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True
    )
    # wait
    time.sleep(wait_time)
    # check if process already died
    if process.poll() is not None:
        stdout, stderr = process.communicate()

        raise RuntimeError(
            f"Ollama server failed to start.\n\n"
            f"Exit code: {process.returncode}\n\n"
            f"STDOUT:\n{stdout}\n\n"
            f"STDERR:\n{stderr}"
        )
    LOG("Ollama server is running")


@app.route("/kill", methods=["GET", "POST"])
def kill():
    LOG(f"Shutting down ollama server gracefully")
    global shutdown_flag
    shutdown_flag = True
    return jsonify({"status": "ok"})

def run_control_server():
    app.run(host="0.0.0.0", port=5000)

if __name__ == '__main__':
    main()
