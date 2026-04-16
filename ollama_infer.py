#!/usr/bin/env python

from pathlib import Path
from argparse import ArgumentParser, Namespace, ArgumentDefaultsHelpFormatter
import subprocess
import requests
import time
from chris_plugin import chris_plugin, PathMapper
from loguru import logger
import sys
import os
import socket

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

__version__ = '1.0.0'

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
    """
    *ChRIS* plugins usually have two positional arguments: an **input directory** containing
    input files and an **output directory** where to write output files. Command-line arguments
    are passed to this main method implicitly when ``main()`` is called below without parameters.

    :param options: non-positional arguments parsed by the parser given to @chris_plugin
    :param inputdir: directory containing (read-only) input files
    :param outputdir: directory where to write output files
    """

    preamble_show(options)
    ip_address = socket.gethostbyname(socket.gethostname())
    LOG(f"Container IP: {ip_address}")
    subprocess.Popen(
        ["ollama", "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True
    )
    # wait
    time.sleep(2)

    # test
    result = subprocess.run(
        ["ollama", "run", options.model, options.prompt],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        LOG("Error:", result.stderr)
    else:
        LOG(result.stdout)

    # serve
    # This prevents the Python script (and the container) from exiting
    try:
        while options.serviceMode:
            LOG(f"Server in now running: {ip_address} and ready to serve")
            time.sleep(1)
    except KeyboardInterrupt:
        LOG("Stopping...")


if __name__ == '__main__':
    main()
