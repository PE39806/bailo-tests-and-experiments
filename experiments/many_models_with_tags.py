"""Generate lots of models with predefined tags, but randomly mutate the case of some of the tags.
Used for testing case sensitive searches."""

from __future__ import annotations

from random import getrandbits, randint, sample

from bailo import Model
from boilerplate_client import BailoBoilerplateClient

boilerplate_client = BailoBoilerplateClient(dotenv_file=".local.env")
client = boilerplate_client.client

MODEL_NAME_PREFIX = "Many-Models-With-Tags"
MODEL_COUNT = 1000
MODEL_DESCRIPTION = "A simple model for testing case sensitivity of tag searches"
POSSIBLE_TAGS = ["foo-bar", "hello-world", "foo-bar-baz-bat"]

for i in range(MODEL_COUNT):
    model_name = f"{MODEL_NAME_PREFIX}{i}"
    print(f"{model_name=}")
    test_model = Model.create(client, model_name, MODEL_DESCRIPTION)
    test_model.card_from_schema()
    test_model.get_card_latest()
    print(f"{test_model.model_card=}")
    new_card = test_model.model_card.copy() if test_model.model_card else {"overview": {"tags": []}}
    new_card["overview"]["tags"] = [
        tag if bool(getrandbits(1)) else tag.upper() for tag in sample(POSSIBLE_TAGS, k=randint(0, len(POSSIBLE_TAGS)))
    ]
    print(f"{new_card=}")
    test_model.update_model_card(model_card=new_card)
