"""Simple cleanup to delete any files attached to a model that are not in any Releases."""

from __future__ import annotations

import os

from bailo import Model
from boilerplate_client import BailoBoilerplateClient

MODEL_ID_ENV_VAR = "PURGE_ORPHANED_FILES_MODEL_ID"


if __name__ == "__main__":
    boilerplate_client = BailoBoilerplateClient()
    client = boilerplate_client.client
    model_id = os.getenv(MODEL_ID_ENV_VAR)
    experiment_model = Model.from_id(client, model_id)
    all_files = client.get_files(model_id)
    all_releases = client.get_all_releases(model_id)
    all_file_ids = {file["_id"] for file in all_files["files"]}
    all_release_files = {
        file_id for file_ids in [release["fileIds"] for release in all_releases["releases"]] for file_id in file_ids
    }

    print(f"{len(all_file_ids)=}\n{len(all_release_files)=}\n{len(all_file_ids-all_release_files)=}")
    for file_id in all_file_ids - all_release_files:
        print(f"Deleting orphaned file {file_id}")
        client.delete_file(model_id, file_id)
