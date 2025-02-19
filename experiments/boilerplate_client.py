"""Boilerplate Bailo Client wrapper for rapid development."""

from __future__ import annotations

import os

from bailo import Agent, Client, TokenAgent
from dotenv import load_dotenv


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

    @property
    def dotenv_file(self):
        return self._dotenv_file

    @property
    def agent(self):
        return self._agent

    @property
    def client(self):
        return self._client
