"""Create a new model and data card with very long names to test how overflowing text appears."""

from __future__ import annotations

import os

from bailo import Datacard, Model
from bailo.core.exceptions import BailoException
from boilerplate_client import BailoBoilerplateClient
from semantic_version import Version


def generate_long_name(infix: str) -> str:
    return f"ThisIsAnOvertlyLongAndVeryVerbose{infix}WithNoSpacesWhichIWouldNeverExpectToSeeInRealityHoweverItIsImportantToProperlyTestWhetherAnyTextOverflowsSoIAmMakingItLookLikeThisWhichIsOverkillButWillWorkToDemonstrateAnyLimitationsWithinTheUIForDisplayingEgregiouslyLongNamesEvenIfTheyAreNotRepresentativeOfRealData"


boilerplate_client = BailoBoilerplateClient()
client = boilerplate_client.client

model_name = generate_long_name("ModelName")
print(f"Creating new model {model_name}")
test_model = Model.create(client, model_name, generate_long_name("ModelDescription"))
test_model.card_from_schema()

new_release_version = Version("0.0.0")
try:
    current_release = test_model.get_latest_release()
    # bump
    if current_release:
        new_release_version = current_release.version.next_patch()
except BailoException:
    pass

print(f"Creating new release {new_release_version}")
test_release = test_model.create_release(new_release_version, generate_long_name("ReleaseDescriptionNotes"))
# truncate long file names to the system limit
file_path = f"./{generate_long_name('FileName')[:(os.pathconf('/', 'PC_NAME_MAX')-4)]}.txt"
with open(file_path, "w+", encoding="utf-8") as f:
    f.write(generate_long_name("FileContents"))
test_release.upload(file_path)

datacard_name = generate_long_name("DataCardName")
print(f"Creating new datacard {datacard_name}")
test_datacard = Datacard.create(client, datacard_name, generate_long_name("DatacardDescription"))
test_datacard.card_from_schema()
