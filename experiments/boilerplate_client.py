"""Boilerplate Bailo Client wrapper for rapid development."""

from __future__ import annotations

import datetime
import os
import time

from bailo import Agent, Client, Model, TokenAgent
from bailo.core.exceptions import BailoException
from dotenv import load_dotenv, set_key
from semantic_version import Version


class BailoBoilerplateClient:
    """Simple Bailo client wrapper that reads in `ACCESS_KEY`, `SECRET_KEY` and `URL` from a dotenv file.
    Automatically creates a `TokenAgent` if both `ACCESS_KEY` and `SECRET_KEY` are supplied, otherwise uses the default `Agent`.
    """

    def __init__(self, dotenv_file: str = ".local.env"):
        """_summary_

        :param dotenv_file: dotenv file to load in, defaults to ".local.env"
        :raises ValueError: error if `URL` not found.
        """
        self._dotenv_file = dotenv_file
        load_dotenv(self._dotenv_file)

        access_key = os.getenv("ACCESS_KEY")
        secret_key = os.getenv("SECRET_KEY")
        if access_key and secret_key:
            self._agent = TokenAgent(access_key, secret_key)
        else:
            self._agent = Agent()

        client_url = os.getenv("URL")
        if not client_url:
            raise ValueError("Could not get URL from env")

        self._client = Client(client_url, self.agent)

    def get_or_create_model(
        self, model_id_env_var, model_name=None, model_description=None, model_card_schema=None
    ) -> Model:
        """Try to get a model by the ID stored in the env var, and if the model does not exist then create it and set the env var.

        :param model_id_env_var: Name of the env var holding the model ID (in the dotenv file).
        :param model_name: Model name to set if creating, defaults to None in which case `model_id_env_var` is used.
        :param model_description: Model description to set if creating, defaults to None in which case a string with the `model_name` and current datetime is used.
        :param model_card_schema: Model card schema to set if creating, defaults to None.
        :return: The found or created Model object.
        """
        model_id = os.getenv(model_id_env_var)
        try:
            # try to load from an existing model
            model = Model.from_id(self.client, model_id)
            print(f"Found model {model.model_id}")
            return model
        except BailoException:
            if model_name is None:
                model_name = model_id_env_var
            if model_description is None:
                model_description = f"A Bailo Model named {model_name} created by the Bailo Python client at {datetime.datetime.now():%Y-%m-%d %H:%M:%S%z}"
            # create a new model
            model = Model.create(
                self.client,
                model_name,
                model_description,
            )
            set_key(self.dotenv_file, model_id_env_var, model.model_id)
            model.card_from_schema(model_card_schema)
            print(f"Created model {model.model_id} with schema {model_card_schema}")
            return model

    @staticmethod
    def get_next_model_version(model: Model, next_func: str = "next_major") -> Version:
        """Get the next available version for a model. Defaults to 0.0.0 if no releases found.

        :param model: Model to get the latest release from.
        :param next_func: str name of the Version method to call, defaults to "next_major"
        :return: A new major Version.
        """
        version = Version("0.0.0")
        try:
            current_release = model.get_latest_release()
            # bump
            if current_release:
                method = getattr(current_release.version, next_func)
                if not callable(method):
                    raise TypeError(f"Attribute {method} was not callable")
                version = method()
        except BailoException:
            # no release exists
            pass
        return version

    @property
    def dotenv_file(self):
        return self._dotenv_file

    @property
    def agent(self):
        return self._agent

    @property
    def client(self):
        return self._client


class LazyStream:
    """
    A BytesIO-like object that can be uploaded with arbitrary data to Bailo without
    generating a large file in memory.

    Optional rate limiting (bytes/second) can be applied to simulate bandwidth constraints.
    """

    def __init__(self, chunk_size=1024**2, total_size=10**12, rate_limit=None):
        """
        :param chunk_size: Size of chunks to read at a time.
        :param total_size: Total number of bytes in the stream.
        :param rate_limit: Optional rate limit in bytes per second (None = unlimited).
        """
        self.chunk_size = chunk_size
        self.total_size = total_size
        self.position = 0
        self.rate_limit = rate_limit  # bytes/sec or None
        self._last_read_time = time.time()

    def read(self, size=-1):
        if self.position >= self.total_size:
            return b""

        # Adjust size so we don't exceed remaining data
        if size is None or size < 0:
            size = self.total_size - self.position
        else:
            size = min(size, self.total_size - self.position)

        # Apply rate limiting if enabled
        if self.rate_limit is not None and size > 0:
            now = time.time()
            elapsed = now - self._last_read_time
            expected_time = size / self.rate_limit

            # If we are ahead of schedule, sleep
            if elapsed < expected_time:
                time.sleep(expected_time - elapsed)

            self._last_read_time = time.time()

        self.position += size
        return b"\x00" * size

    def tell(self):
        return self.position

    def seek(self, offset, whence=0):
        if whence == 0:
            new_pos = offset
        elif whence == 1:
            new_pos = self.position + offset
        elif whence == 2:
            new_pos = self.total_size + offset
        else:
            raise ValueError(f"Invalid whence: {whence}")

        if new_pos < 0:
            raise ValueError("Negative seek position")

        self.position = min(new_pos, self.total_size)
        return self.position
