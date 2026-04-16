# A ChRIS plugin to run an `ollama` server

[![Version](https://img.shields.io/docker/v/fnndsc/pl-ollama_infer?sort=semver)](https://hub.docker.com/r/fnndsc/pl-ollama_infer)
[![MIT License](https://img.shields.io/github/license/fnndsc/pl-ollama_infer)](https://github.com/FNNDSC/pl-ollama_infer/blob/main/LICENSE)
[![ci](https://github.com/FNNDSC/pl-ollama_infer/actions/workflows/ci.yml/badge.svg)](https://github.com/FNNDSC/pl-ollama_infer/actions/workflows/ci.yml)

`pl-ollama_infer` is a ChRIS plugin that starts a local Ollama server, runs model inference using a provided prompt, and optionally keeps the server running for service mode usage.

---

## Abstract

This plugin launches an Ollama server inside a ChRIS container environment, executes inference using a specified model and prompt, and optionally keeps the server active for continued interaction.

It is intended for workflows requiring lightweight LLM inference within containerized pipelines, including structured text generation and data interpretation tasks.

---

## Features

- Starts `ollama serve` inside the container
- Executes inference using configurable model and prompt
- Supports persistent server mode via `--serviceMode`
- Logs runtime environment for debugging and reproducibility

---

## Installation

`pl-ollama_infer` is a ChRIS plugin and can be executed either within the ChRIS platform or via container runtimes.

---

## Local Usage

Using Apptainer:

```shell
apptainer exec docker://fnndsc/pl-ollama_infer ollama_infer [--args values...] input/ output/
To print its available options, run:

```shell
apptainer exec docker://fnndsc/pl-ollama_infer ollama_infer --help
```
| Argument        | Default  | Description                                |
| --------------- | -------- | ------------------------------------------ |
| `--prompt`      | `test`   | Input prompt for the model                 |
| `--model`       | `llama3` | Ollama model to use                        |
| `--serviceMode` | `False`  | Keep Ollama server running after inference |
| `--version`     | -        | Show plugin version                        |

## Examples

`ollama_infer` requires two positional arguments: a directory containing
input data, and a directory where to create output data.
First, create the input directory and move input data into it.

```shell
mkdir incoming/ outgoing/
mv some.dat other.dat incoming/
apptainer exec docker://fnndsc/pl-ollama_infer ollama_infer \
    --prompt "Explain pulmonary embolism briefly" \
    --model llama3 \
    incoming/ outgoing/
```

Using a larger model

```shell
apptainer exec docker://fnndsc/pl-ollama_infer ollama_infer \
    --prompt "Summarize CT chest findings" \
    --model llama3:70b \
    incoming/ outgoing/
```

Service mode

```shell
apptainer exec docker://fnndsc/pl-ollama_infer ollama_infer \
    --serviceMode \
    incoming/ outgoing/
```

## Development

Instructions for developers.

### Building

Build a local container image:

```shell
docker build -t localhost/fnndsc/pl-ollama_infer .
```

### Running

Mount the source code `ollama_infer.py` into a container to try out changes without rebuild.

```shell
docker run --rm -it --userns=host -u $(id -u):$(id -g) \
    -v $PWD/ollama_infer.py:/usr/local/lib/python3.12/site-packages/ollama_infer.py:ro \
    -v $PWD/in:/incoming:ro -v $PWD/out:/outgoing:rw -w /outgoing \
    localhost/fnndsc/pl-ollama_infer ollama_infer /incoming /outgoing
```

### Testing

Run unit tests using `pytest`.
It's recommended to rebuild the image to ensure that sources are up-to-date.
Use the option `--build-arg extras_require=dev` to install extra dependencies for testing.

```shell
docker build -t localhost/fnndsc/pl-ollama_infer:dev --build-arg extras_require=dev .
docker run --rm -it localhost/fnndsc/pl-ollama_infer:dev pytest
```

## Release

Steps for release can be automated by [Github Actions](.github/workflows/ci.yml).
This section is about how to do those steps manually.

### Increase Version Number

Increase the version number in `setup.py` and commit this file.

### Push Container Image

Build and push an image tagged by the version. For example, for version `1.2.3`:

```
docker build -t docker.io/fnndsc/pl-ollama_infer:1.2.3 .
docker push docker.io/fnndsc/pl-ollama_infer:1.2.3
```

### Get JSON Representation

Run [`chris_plugin_info`](https://github.com/FNNDSC/chris_plugin#usage)
to produce a JSON description of this plugin, which can be uploaded to _ChRIS_.

```shell
docker run --rm docker.io/fnndsc/pl-ollama_infer:1.2.3 chris_plugin_info -d docker.io/fnndsc/pl-ollama_infer:1.2.3 > chris_plugin_info.json
```

Intructions on how to upload the plugin to _ChRIS_ can be found here:
https://chrisproject.org/docs/tutorials/upload_plugin

