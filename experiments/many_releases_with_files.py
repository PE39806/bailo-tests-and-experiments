from __future__ import annotations

import datetime
from io import BytesIO
from os import getenv

from bailo import Model
from bailo.core.exceptions import BailoException
from boilerplate_client import BailoBoilerplateClient
from dotenv import set_key
from semantic_version import Version

MODEL_ID_ENV_VAR = "MANY_RELEASES_WITH_FILES_MODEL_ID"

FILE_COUNT = 100
MAX_FILE_SIZE_EXPONENT = 10


if __name__ == "__main__":
    boilerplate_client = BailoBoilerplateClient()
    client = boilerplate_client.client
    model_id = getenv(MODEL_ID_ENV_VAR)
    experiment_model = None

    try:
        # try to load from an existing model
        experiment_model = Model.from_id(client, model_id)
        print(f"Found model {experiment_model.id}")
    except BailoException:
        # create a new model
        experiment_model = Model.create(
            client, "many-releases-with-files-test", "A simple model for testing many releases with files."
        )
        set_key(boilerplate_client.dotenv_file, MODEL_ID_ENV_VAR, experiment_model.model_id)
        model_id = experiment_model.model_id
        experiment_model.card_from_schema()
        print(f"Created model {experiment_model.id}")

    existing_file_sizes = [f["size"] for f in client.get_files(model_id)["files"]]
    for file_index in range(FILE_COUNT):
        # exponential increase, with each file size guaranteed to be unique
        file_size = int(10 ** (MAX_FILE_SIZE_EXPONENT * (file_index) / FILE_COUNT) + file_index)
        if file_size not in existing_file_sizes:
            blob = BytesIO(b"\x00" * file_size)

            print(f"Uploading file {file_index} size {file_size:_}")
            res = client.simple_upload(
                model_id,
                f"blob-{file_size:_}.blob",
                blob,
            )
            del blob
        else:
            print(f"Skip existing file {file_index} size {file_size:_}")

    all_files_by_size = [
        file["id"] for file in sorted(client.get_files(model_id)["files"], key=lambda file: file["size"])
    ]
    for release_index in range(len(all_files_by_size) + 1):
        new_release_version = Version("0.0.0")
        try:
            current_release = experiment_model.get_latest_release()
            # bump
            if current_release:
                new_release_version = current_release.version.next_patch()
        except BailoException:
            pass

        notes = f"Uploaded using the Bailo Python client at {datetime.datetime.now():%Y-%m-%d %H:%M:%S%z}"
        files = all_files_by_size[:release_index]
        print(f"Creating new release {new_release_version} with {len(files)} files")
        experiment_model.create_release(
            new_release_version,
            notes,
            files=files,
        )
