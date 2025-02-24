# bailo-tests-and-experiments

Various bits and bobs used for checking specific functionality within Bailo.

This repo is intended for programmatic one-time experiments so files may not be maintained in the future.

## Experiments

- `many_models_with_tags.py`: create lots of models with predefined tags, but randomly mutate the case of some of the tags. Used for testing case sensitive searches.
- `scanners.py`: upload various files from the local machine to a model to test the performance of the AV scanners.

## Setup

Setup and use a python `venv`:

```bash
python3 -m venv experiments-venv
source experiments-venv/bin/activate
```

Install required packages:

```bash
pip install -r requirements.txt
pip install -e </path/to/Bailo/lib/python>
```

Install pre-commit:

```bash
pre-commit install
```

Create and populate your dotenv file(s) e.g. `.local.env`. You can get your `ACCESS_KEY` and `SECRET_KEY` from the Authentication tab within Bailo's Settings.
`URL` points to a Bailo instance you wish to connect to for running the scripts.

```console
$ cat .local.env
ACCESS_KEY=BBB_ABCD1234
SECRET_KEY=BBB_ABCDEF123456
URL=http://localhost:8080
```

## Usage

Utilise [BailoBoilerplateClient](./boilerplate_client.py) to quickly connect to a running Bailo instance in Python.

For example:

```python
from boilerplate_client import BailoBoilerplateClient

boilerplate_client = BailoBoilerplateClient()
client = boilerplate_client.client
```
