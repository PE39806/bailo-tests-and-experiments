from __future__ import annotations

import json
import os
from time import sleep
from typing import Any

from bailo import Model
from bailo.core.exceptions import BailoException
from boilerplate_client import BailoBoilerplateClient
from lorem_text import lorem


def set_list_str_random(l: list[Any], skip_keys: list[str] | None = None) -> list[Any]:
    if skip_keys is None:
        skip_keys = []
    for i, value in enumerate(l):
        if isinstance(value, str):
            l[i] = lorem.words(5)
        elif isinstance(value, dict):
            l[i] = set_dict_str_random(l[i], skip_keys)
        elif isinstance(value, list):
            l[i] = set_list_str_random(l[i], skip_keys)
    return l


def set_dict_str_random(d: dict[str, Any], skip_keys: list[str] | None = None) -> dict[str, Any]:
    if skip_keys is None:
        skip_keys = []
    for key, value in d.items():
        if isinstance(value, str) and key not in skip_keys:
            d[key] = lorem.words(5)
        elif isinstance(value, dict):
            d[key] = set_dict_str_random(d[key], skip_keys)
        elif isinstance(value, list):
            d[key] = set_list_str_random(d[key], skip_keys)
    return d


def revise_model_card(model: Model):
    model.get_card_latest()
    new_card: dict[str, Any] = model._card.copy()
    new_card = set_dict_str_random(new_card)
    try:
        model.update_model_card(new_card)
    except BailoException as e:
        print(f"{e}\n{json.dumps(new_card)}")


if __name__ == "__main__":
    boilerplate_client = BailoBoilerplateClient(".dev.env")
    client = boilerplate_client.client

    MODEL_ID_ENV_VAR = "MODEL_CARD_REVISION_MODEL_ID"
    MODEL_ID = os.getenv(MODEL_ID_ENV_VAR)
    if not MODEL_ID:
        raise Exception("Env var MODEL_CARD_REVISION_MODEL_ID not set")

    model = Model.from_id(client, MODEL_ID)
    for i in range(40):
        print(i)
        revise_model_card(model)
        sleep(1)
