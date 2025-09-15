"""Create releases with an increasing number of associated images (triangular numbers)."""

from __future__ import annotations

import datetime

from boilerplate_client import BailoBoilerplateClient

MODEL_ID_ENV_VAR = "MANY_RELEASES_WITH_EXISTING_IMAGES_MODEL_ID"


if __name__ == "__main__":
    boilerplate_client = BailoBoilerplateClient()
    client = boilerplate_client.client
    experiment_model = boilerplate_client.get_or_create_model(
        MODEL_ID_ENV_VAR,
        "many-releases-with-existing-images-test",
        "A simple model for testing many releases with user created images.",
    )
    model_id = experiment_model.model_id

    all_images = client.get_all_images(model_id)["images"]
    # image names formatted as ["no1-1024", "no2-2048", "no3-1024", ...]
    all_images_sorted = sorted(all_images, key=lambda image: int(image["name"].removeprefix("no").split("-")[0]))

    triangular_limit = 1
    counter = 0
    all_images_grouped = {}
    for image in all_images_sorted:
        if counter >= triangular_limit:
            triangular_limit += 1
            counter = 0
        counter += 1

        image_singular_tag = image
        image_singular_tag["tag"] = image_singular_tag["tags"][0]
        del image_singular_tag["tags"]
        # append-if-exists-else-create-list
        all_images_grouped.setdefault(triangular_limit, []).append(image_singular_tag)
    all_images_grouped_sorted = dict(sorted(all_images_grouped.items()))

    for image_group in all_images_grouped_sorted.values():
        new_release_version = boilerplate_client.get_next_model_version(experiment_model, "next_patch")
        notes = f"Uploaded using the Bailo Python client at {datetime.datetime.now():%Y-%m-%d %H:%M:%S%z}"
        print(f"Creating new release {new_release_version} with {len(image_group)} images")
        experiment_model.create_release(
            new_release_version,
            notes,
            images=image_group,
        )
