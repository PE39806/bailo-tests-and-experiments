# bailo-tests-and-experiments

Various bits and bobs used for checking specific functionality within Bailo.

This repo is intended for programmatic one-time experiments so files may not be maintained in the future.

## Experiments

A collection of standalone python scripts to programmatically run and test Bailo functionality.

- `many_models_with_tags.py`: create lots of models with predefined tags, but randomly mutate the case of some of the tags. Used for testing case sensitive searches.
- `scanners.py`: upload various files from the local machine to a model to test the performance of the AV scanners.
- `long_names.py`: create a model with a release with a file with very long names, and also a data card with a very long name. Used to test overflowing text.
- `concurrent_file_uploads.py`: upload multiple files simultaneously. Used to stress test the backend and AV scanners.
- `model_card_revisions.py`: set random values for each part of a model card. Used to stress test model mirroring with many revisions.
- `many_releases_with_files.py`: create releases with files where the file sizes exponentially increase. Used to stress test model mirroring with releases containing files.
- `several_releases_with_files.py`: create releases with files where the total file size per release sums up to a known figure. Overall this is similar to `many_releases_with_files.py`.
- `many_releases_with_existing_images.py`: create releases from manually uploaded images where each successive release has an increasing number of images (based off triangular numbers). Used to stress test model mirroring with releases containing images.
- `purge_files_without_release.py`: simple cleanup to delete any files attached to a model that are not in any Releases.
- `clone_releases.py`: clone the skeleton releases in one model to another. This does not directly copy the File and Container contents but creates named copies with empty contents of the appropriate size. File size is exact but Container size is only approximate. Useful for testing model mirroring with artefacts on a "fresh" copy of all artefacts.

## Bailo OpenAPI Linter

`openapi_checker.py`

Unlike the each of the experiments, this is a specific integration test to compare the Bailo Python Client's endpoints to the Bailo OpenAPI Specification. It requires Bailo to be running locally at `http://localhost:8080` and will then throw errors for any endpoints found in `client.py` that do not exist in the OpenAPI specification, and warnings for any endpoints found in the OpenAPI specification but not `client.py`

```bash
pylint --load-plugins=bailo_openapi_linter.openapi_checker --disable=all --enable=endpoint-not-covered,endpoint-unknown --jobs=1 <path/to/bailo/lib/python/src/bailo/core/client.py>
```

## Setup

Setup and use a python `venv`:

```bash
python3 -m venv experiments-venv
source experiments-venv/bin/activate
```

Install required packages:

```bash
pip install -r requirements.txt
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

## Development

Utilise [BailoBoilerplateClient](./boilerplate_client.py) to quickly connect to a running Bailo instance in Python.

For example:

```python
from boilerplate_client import BailoBoilerplateClient

boilerplate_client = BailoBoilerplateClient()
client = boilerplate_client.client
```

`BailoBoilerplateClient` also includes some helpful util methods such as `get_or_create_model` and `get_next_model_version`.

[LazyStream](./boilerplate_client.py) is another useful utility that can be used in place of `BytesIO` to have a blob of arbitrary size that is not fully loaded into memory, allowing for stress testing massive files. Example usage:

```python
from boilerplate_client import BailoBoilerplateClient, LazyStream

boilerplate_client = BailoBoilerplateClient()
client = boilerplate_client.client
model = boilerplate_client.get_or_create_model("BIG_FILE_UPLOAD_TEST")
file_size = 10 ** 12  # 1 TB (Terabyte)

client.simple_upload(
    model.model_id,
    f"blob-{file_size:_}.blob",
    LazyStream(total_size=file_size),
)
```
