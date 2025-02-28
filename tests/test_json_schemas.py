"""
Tests that JSON files are correct according to schemas.

 Please do not put the *unittest* in the tests/unittest GitHub action.
 It is only for local use.
HOWEVER,
 Please keep the raw python script, so it can be run by the GitHub action.
"""

import json
import jsonschema
from pathlib import Path
from referencing import Registry
from referencing.jsonschema import DRAFT7
import unittest

ROOT_DIR = Path(__file__).parent.parent
SCHEMA_DIR = ROOT_DIR / "schemas"
RESOURCES_DIR = ROOT_DIR / "resources" / "dicts"

COMMON_SCHEMA = json.loads((SCHEMA_DIR / "common.schema.json").read_text())
THOUGHT_SCHEMA = json.loads((SCHEMA_DIR / "thought.schema.json").read_text())
PATROL_SCHEMA = json.loads((SCHEMA_DIR / "patrol.schema.json").read_text())

THOUGHT_DIR = RESOURCES_DIR / "thoughts"
PATROL_DIR = RESOURCES_DIR / "patrols"

registry = Registry().with_resources(
    [
        ("common.schema.json", DRAFT7.create_resource(COMMON_SCHEMA)),
        ("thought.schema.json", DRAFT7.create_resource(THOUGHT_SCHEMA)),
        ("patrol.schema.json", DRAFT7.create_resource(PATROL_SCHEMA))
    ]
)

def all_thought_files():
    """
    Iterator for Paths for all thought files
    """
    yield from THOUGHT_DIR.glob("**/*.json")

def all_patrol_files():
    """
    Iterator for Paths for all patrol files
    """
    EXCLUSIONS = [
        PATROL_DIR / "explicit_patrol_art.json"
    ]
    for filename in PATROL_DIR.glob("**/*.json"):
        if filename not in EXCLUSIONS:
            yield filename

def test_thoughts_schema():
    """Test that all thought JSONs are correct according to the JSON schema"""
    for thought_file in all_thought_files():
        data = json.loads(thought_file.read_text())
        jsonschema.validate(data, THOUGHT_SCHEMA, cls=jsonschema.Draft7Validator,
                            registry=registry)

def test_patrols_schema():
    """Test that all patrol JSONs are correct according to the JSON schema"""
    for patrol_file in all_patrol_files():
        data = json.loads(patrol_file.read_text())
        jsonschema.validate(data, PATROL_SCHEMA, cls=jsonschema.Draft7Validator,
                            registry=registry)

class TestJsonSchemas(unittest.TestCase):
    """Unittest for local use to test that JSON files
       are correct according to schemas."""

    def test_thoughts_schema(self):
        """Unittest for local use to test that all
           thought JSONs are correct according to the JSON schema."""
        test_thoughts_schema()

    def test_patrols_schema(self):
        """Unittest for local use to test that all
           patrol JSONs are correct according to the JSON schema."""
        test_patrols_schema()

if __name__ == "__main__":
    test_thoughts_schema()
    test_patrols_schema()
