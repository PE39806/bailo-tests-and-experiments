from __future__ import annotations

import datetime
from io import BytesIO
from os import getenv

from bailo import Model
from bailo.core.exceptions import BailoException
from boilerplate_client import BailoBoilerplateClient
from dotenv import set_key
from semantic_version import Version

MODEL_ID_ENV_VAR = "SEVERAL_RELEASES_WITH_FILES_MODEL_ID"

MAX_FILE_COUNT_EXPONENT = 5
MAX_FILE_SIZE_EXPONENT = 1


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
            client,
            "Several Releases With Files Test",
            "A simple model for testing several releases with files that sum up to the same amount of bytes.",
        )
        set_key(boilerplate_client.dotenv_file, MODEL_ID_ENV_VAR, experiment_model.model_id)
        model_id = experiment_model.model_id
        experiment_model.card_from_schema()
        print(f"Created model {experiment_model.id}")

    new_release_version = Version("0.0.0")
    try:
        current_release = experiment_model.get_latest_release()
        # bump
        if current_release:
            new_release_version = current_release.version.next_major()
    except BailoException:
        pass
    print(f"Starting on release {new_release_version}")

    for file_size_exponent in range(MAX_FILE_SIZE_EXPONENT):
        for file_count_exponent in range(MAX_FILE_COUNT_EXPONENT):
            file_count = 2**file_count_exponent
            # each release will have file_count files with summed size (2 ** (MAX_FILE_COUNT_EXPONENT - 1)) * (10**file_size_exponent)
            file_size = int((2 ** (MAX_FILE_COUNT_EXPONENT - 1)) * (10**file_size_exponent) / file_count)

            uploaded_file_ids = []
            for file_counter in range(file_count):
                print(f"Uploading file {file_counter+1} of {file_count} size {file_size:_}")
                blob = BytesIO(b"\x00" * file_size)
                try:
                    res = client.simple_upload(
                        model_id,
                        f"blob-{file_size:_}-{file_count:_}-{file_counter:_}.blob",
                        blob,
                    )
                    uploaded_file_ids.append(res.json()["file"]["id"])
                except Exception as e:
                    try:
                        print(f"Exception!\n{res.text}")
                        print(f"Exception!\n{res}")
                    except NameError:
                        pass
                    raise e
                finally:
                    del blob

            print(f"Creating new release {new_release_version} with {len(uploaded_file_ids)} files")
            notes = f"Uploaded using the Bailo Python client at {datetime.datetime.now():%Y-%m-%d %H:%M:%S%z}"
            experiment_model.create_release(
                new_release_version,
                notes,
                files=uploaded_file_ids,
            )
            new_release_version = new_release_version.next_patch()
        new_release_version = new_release_version.next_minor()
