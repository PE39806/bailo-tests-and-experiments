"""Upload various files from the local machine to a model to test the performance of the AV scanners.

This script does *not* download any files for you - they must be supplied yourself. Add these downloaded files to the `PATHS` variable defined later in the script.
"""

from __future__ import annotations

import datetime
import os

from bailo import Model
from bailo.core.exceptions import BailoException
from bailo.helper.release import Release
from boilerplate_client import BailoBoilerplateClient
from dotenv import set_key
from semantic_version import Version


class ScanPath:

    def __init__(self, model: Model, path: str, subpath: bool = False):
        self.model = model
        self.path = path
        self.subpath = subpath
        self.sub_paths = []

    def get_paths(self) -> list[list[str]]:
        if self.subpath:
            self.sub_paths = os.listdir(self.path)
            return [
                [
                    os.path.join(dirpath, filename)
                    for (dirpath, _, filenames) in os.walk(os.path.join(self.path, sub_path))
                    for filename in filenames
                ]
                for sub_path in os.listdir(self.path)
            ]
        return [
            [
                os.path.join(dirpath, filename)
                for (dirpath, _, filenames) in os.walk(self.path)
                for filename in filenames
            ]
        ]

    def create_new_release(self, extra_text: str | None = None) -> Release:
        # fallback version value
        new_release_version = Version("0.0.0")
        try:
            current_release = self.model.get_latest_release()
            # bump
            if current_release:
                new_release_version = current_release.version.next_patch()
        except BailoException:
            pass

        print(f"Creating new release {new_release_version}")
        notes = f"Uploaded using the Bailo Python client at {datetime.datetime.now():%Y-%m-%d %H:%M:%S%z}"
        if extra_text:
            notes = f"{notes}{extra_text}"
        return self.model.create_release(
            new_release_version,
            notes,
        )

    def upload_as_releases(self) -> None:
        for index, path_group in enumerate(self.get_paths()):
            unique_file_names = set()
            if self.subpath:
                new_release = self.create_new_release(extra_text=f" for {self.sub_paths[index]}")
            else:
                new_release = self.create_new_release(extra_text=f" for {self.path}")
            for file_path in path_group:
                file_name = os.path.basename(file_path)
                if file_name not in unique_file_names:
                    unique_file_names.add(file_name)
                    print(f"Uploading file {file_path}")
                    new_release.upload(file_path)


boilerplate_client = BailoBoilerplateClient()
client = boilerplate_client.client

MODEL_ID_ENV_VAR = "SCANNERS_MODEL_ID"
MODEL_ID = os.getenv(MODEL_ID_ENV_VAR)

if MODEL_ID:
    # reuse existing model
    test_model = Model.from_id(client, MODEL_ID)
else:
    # create a new model
    test_model = Model.create(
        client, "File-scanners-test", "A simple model for testing many different file formats, sizes etc."
    )
    set_key(boilerplate_client.dotenv_file, MODEL_ID_ENV_VAR, test_model.model_id)
    test_model.card_from_schema()

# replace this with your own path and relevant files
PATHS_PREFIX = "</path/to.downloaded/model/files>"
PATHS = [
    ScanPath(test_model, f"{PATHS_PREFIX}/KerasModels/"),
    ScanPath(test_model, f"{PATHS_PREFIX}/PyTorchModels/"),
    ScanPath(test_model, f"{PATHS_PREFIX}/TensorFlowModels/", True),
    ScanPath(test_model, f"{PATHS_PREFIX}/XGBoostModels/"),
    ScanPath(test_model, f"{PATHS_PREFIX}/generated/"),
    ScanPath(test_model, f"{PATHS_PREFIX}/big-models/"),
]

for scan_path in PATHS:
    scan_path.upload_as_releases()
