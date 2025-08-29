from __future__ import annotations

import datetime

from boilerplate_client import BailoBoilerplateClient, LazyStream

MODEL_ID_ENV_VAR = "MANY_RELEASES_WITH_FILES_MODEL_ID"

FILE_COUNT = 100
MAX_FILE_SIZE_EXPONENT = 10


if __name__ == "__main__":
    boilerplate_client = BailoBoilerplateClient()
    client = boilerplate_client.client
    experiment_model = boilerplate_client.get_or_create_model(
        MODEL_ID_ENV_VAR, "many-releases-with-files-test", "A simple model for testing many releases with files."
    )
    model_id = experiment_model.model_id

    existing_file_sizes = [f["size"] for f in client.get_files(model_id)["files"]]
    for file_index in range(FILE_COUNT):
        # exponential increase, with each file size guaranteed to be unique
        file_size = int(10 ** (MAX_FILE_SIZE_EXPONENT * (file_index) / FILE_COUNT) + file_index)
        if file_size not in existing_file_sizes:
            print(f"Uploading file {file_index} size {file_size:_}")
            res = client.simple_upload(
                model_id,
                f"blob-{file_size:_}.blob",
                LazyStream(total_size=file_size),
            )
        else:
            print(f"Skip existing file {file_index} size {file_size:_}")

    all_files_by_size = [
        file["id"] for file in sorted(client.get_files(model_id)["files"], key=lambda file: file["size"])
    ]
    for release_index in range(len(all_files_by_size) + 1):
        new_release_version = boilerplate_client.get_next_model_version(experiment_model, "next_patch")

        notes = f"Uploaded using the Bailo Python client at {datetime.datetime.now():%Y-%m-%d %H:%M:%S%z}"
        files = all_files_by_size[:release_index]
        print(f"Creating new release {new_release_version} with {len(files)} files")
        experiment_model.create_release(
            new_release_version,
            notes,
            files=files,
        )
