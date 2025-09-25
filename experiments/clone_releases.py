"""Copy the format of the releases in one model to another model.
Loads a dumped source model `GET /api/v2/model/{modelId}/releases` which can be manually edited for additional testing purposes.
This will not copy the File and Image contents but does copy the File size and approximate Image size for all Releases.
Additionally, Scanner results are not copied across.
Requires docker installed on the host OS."""

from __future__ import annotations

import json
import math
import os
import subprocess
import time

from bailo.core.exceptions import BailoException, ResponseException
from bailo.helper.model import Model
from bailo.helper.release import Release
from boilerplate_client import BailoBoilerplateClient, LazyStream
from dotenv import set_key

SOURCE_MODEL_ID_ENV_VAR = "CLONE_RELEASES_SOURCE_MODEL_ID"
DESTINATION_MODEL_ID_ENV_VAR = "CLONE_RELEASES_DESTINATION_MODEL_ID"
DUMPED_FILE_ENV_VAR = "CLONE_RELEASES_ENDPOINT_DUMP"


if __name__ == "__main__":
    boilerplate_client = BailoBoilerplateClient()
    client = boilerplate_client.client
    experiment_model = boilerplate_client.get_or_create_model(
        DESTINATION_MODEL_ID_ENV_VAR,
        "Clone Releases Test",
        "A model with releases matching those of a model's releases endpoint response.",
    )
    model_id = experiment_model.model_id

    # read file from path if possible, else GET then dump
    # allows for loading edited JSON files if wanted
    dumped_file_path = os.getenv(DUMPED_FILE_ENV_VAR)
    clone_releases_template = None
    try:
        # try to load from an existing file
        with open(dumped_file_path, encoding="utf-8") as dumped_file:
            clone_releases_template = json.load(dumped_file)
    except OSError:
        # get source model
        source_model_id = os.getenv(SOURCE_MODEL_ID_ENV_VAR)
        source_model = Model.from_id(client, model_id)
        print(f"Found model {source_model.model_id}")
        # get releases
        clone_releases_template = source_model.get_releases()
        # dump releases
        dumped_file_path = f"tmp/{source_model.model_id}_releases.json"
        with open(dumped_file_path, "w", encoding="utf-8") as dumped_file:
            dumped_file.write(clone_releases_template)
        set_key(boilerplate_client.dotenv_file, DUMPED_FILE_ENV_VAR, dumped_file_path)

    trimmed_client_url = client.url.removeprefix("http://").removeprefix("https://").removesuffix("/api")
    subprocess.run(
        ["docker", "login", trimmed_client_url, "-u", os.getenv("ACCESS_KEY"), "-p", os.getenv("SECRET_KEY")],
        check=True,
    )

    # create releases
    for release_counter, source_release in enumerate(clone_releases_template["releases"]):
        print(f"Release {release_counter+1}/{len(clone_releases_template["releases"])} {source_release["semver"]}")
        # skip already made releases
        try:
            experiment_model.get_release(source_release["semver"])
            print(f"Skipping existing semver {source_release["semver"]}")
            continue
        except (ResponseException, BailoException) as e:
            print(f"Generating new semver {source_release["semver"]}")

        release_files = []
        for file_counter, source_file in enumerate(source_release["files"]):
            print(
                f"Uploading file {file_counter+1}/{len(source_release["files"])} {source_file["name"]} size {source_file["size"]:_}"
            )

            # retry loop in case the endpoint fails temporarily (prevents needing to re-upload everything again)
            res = None
            retry_count = 1
            while res is None:
                try:
                    res = client.simple_upload(
                        model_id, source_file["name"], LazyStream(total_size=source_file["size"])
                    ).json()
                except (ResponseException, BailoException) as e:
                    print("Temporary failure:")
                    print(e)
                    print(f"Pausing for {2**retry_count} seconds.")
                    # exponential backoff
                    time.sleep(2**retry_count)
                    retry_count += 1
            release_files.append(res["file"]["_id"])

        release_images = []
        for image_counter, source_image in enumerate(source_release["images"]):
            image_name_short = f"{source_image["name"]}:{source_image["tag"]}"
            print(f"Getting image metadata {image_counter+1}/{len(source_release["images"])} for {image_name_short}")
            source_image_name_full = f"{trimmed_client_url}/{source_image["repository"]}/{image_name_short}"
            data = None
            # try to read the manifest
            try:
                # read from bailo instance
                data = json.loads(
                    subprocess.run(
                        ["docker", "manifest", "inspect", "-v", source_image_name_full],
                        text=True,
                        check=True,
                        capture_output=True,
                    ).stdout
                )
                print("Got full path")
            except subprocess.CalledProcessError:
                # read from other source e.g. docker hub
                # useful as getting the manifest requires image pull permission, so this is just a backup
                data = json.loads(
                    subprocess.run(
                        ["docker", "manifest", "inspect", "-v", image_name_short],
                        text=True,
                        check=True,
                        capture_output=True,
                    ).stdout
                )
                print("Got other sourced path")
            # handle fat manifests
            manifests = data if isinstance(data, list) else [data]
            items = []
            for manifest in manifests:
                # Skip if architecture is unknown
                arch = manifest.get("Descriptor", {}).get("platform", {}).get("architecture")
                if arch == "unknown":
                    continue

                # Get layers sizes
                layers = manifest.get("OCIManifest", manifest.get("SchemaV2Manifest", {})).get("layers", [])
                total_size = sum(layer.get("size", 0) for layer in layers)

                items.append(total_size)
            # only get max file size (in MB)
            image_size = math.ceil(max(items) / (1024**2))
            print(f"Generating new docker image size {image_size=}")
            # size is approximate due to how docker layers & metadata works
            image_name_full = f"{trimmed_client_url}/{model_id}/{image_name_short}"
            subprocess.run(
                [
                    "docker",
                    "build",
                    "--build-arg",
                    f"IMG_SIZE_MB={image_size}",
                    "--build-arg",
                    f"CACHEBUST={time.time()}",
                    "-f",
                    "Dockerfile.fixedSize",
                    "-t",
                    image_name_full,
                    ".",
                ],
                check=True,
            )
            print(f"Pushing docker image {image_name_full=}")
            subprocess.run(["docker", "push", image_name_full], check=True)
            print(f"Untagging docker image {image_name_full=}")
            subprocess.run(["docker", "rmi", image_name_full], check=True)
            release_images.append({"repository": model_id, "name": source_image["name"], "tag": source_image["tag"]})

        print(
            f"Creating release {source_release["semver"]} with {len(release_files)} files and {len(release_images)} images."
        )
        Release.create(
            client,
            model_id,
            source_release["semver"],
            source_release["notes"],
            experiment_model.model_card_version,
            images=release_images,
            files=release_files,
            minor=source_release["minor"],
            draft=source_release["draft"],
        )
