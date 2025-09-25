"""Concurrently upload multiple files to a specific Bailo instance.
Useful for stress testing how the server will respond when under a heavy load.
Uses env var `CONCURRENCY_MODEL_ID` to save and load the same model for testing."""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from itertools import repeat
from os import getenv

from bailo import Model
from bailo.core.exceptions import BailoException
from boilerplate_client import BailoBoilerplateClient, LazyStream
from dotenv import set_key


def upload_file(
    process_count: int,
    file_size: int,
    model_id_env_var: str = "CONCURRENCY_MODEL_ID",
    dotenv_file: str = ".local.env",
) -> int:
    """Thread/process safe way to upload a BytesIO object of `file_size` bytes.

    :param process_count: ID of this process
    :param file_size: the size of the BytesIO object to create
    :param random_bytes: whether to randomise the byte values in the BytesIO object, defaults to False (uses all 0s)
    :param model_id_env_var: Env var to read to get the model ID, defaults to "CONCURRENCY_MODEL_ID"
    :param dotenv_file: dotenv filename to load for the boilerplate client, defaults to ".local.env"
    :return: ID of the process
    """
    print(f"Starting {process_count}")
    # pylint: disable=redefined-outer-name
    boilerplate_client = BailoBoilerplateClient(dotenv_file=dotenv_file)
    client = boilerplate_client.client
    model_id = getenv(model_id_env_var)
    # pylint: enable=redefined-outer-name

    client.simple_upload(
        model_id,
        "test" + str(process_count),
        LazyStream(total_size=file_size),
    )
    print(f"Finished {process_count}")
    return process_count


if __name__ == "__main__":
    # IMPORTANT: be careful balancing these numbers others your machine may run out of RAM
    MAX_WORKERS = 8
    FILE_SIZE = 1024 * 1024 * 20  # 20MB
    UPLOAD_COUNT = 64
    MODEL_ID_ENV_VAR = "CONCURRENCY_MODEL_ID"
    DOTENV_FILE = ".local.env"

    # check if a model already exists, and if not then create it
    boilerplate_client = BailoBoilerplateClient(dotenv_file=DOTENV_FILE)
    client = boilerplate_client.client
    model_id = getenv(MODEL_ID_ENV_VAR)
    try:
        # try to load from an existing model
        Model.from_id(client, model_id)
    except BailoException:
        # create a new model
        test_model = Model.create(
            client, "Concurrent-uploads-test", "A simple model for testing uploading many files simultaneously."
        )
        set_key(boilerplate_client.dotenv_file, MODEL_ID_ENV_VAR, test_model.model_id)
        test_model.card_from_schema()
    # cleanup no-longer required objects
    del boilerplate_client, client, model_id

    # main upload loop
    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for x in executor.map(
            upload_file,
            range(UPLOAD_COUNT),
            repeat(FILE_SIZE, UPLOAD_COUNT),
            repeat(MODEL_ID_ENV_VAR, UPLOAD_COUNT),
            repeat(DOTENV_FILE, UPLOAD_COUNT),
        ):
            print(f"Process {x} returned")
