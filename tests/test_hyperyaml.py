import pytest


def test_load_hyperpyyaml(tmpdir):
    from hyperpyyaml import (
        load_hyperpyyaml,
        RefTag,
        Placeholder,
        dump_hyperpyyaml,
    )

    # Basic functionality
    yaml = """
    a: 1
    thing: !new:collections.Counter {}
    """
    things = load_hyperpyyaml(yaml)
    assert things["a"] == 1
    from collections import Counter

    assert things["thing"].__class__ == Counter

    overrides = {"a": 2}
    things = load_hyperpyyaml(yaml, overrides=overrides)
    assert things["a"] == 2
    overrides = "{a: 2}"
    things = load_hyperpyyaml(yaml, overrides=overrides)
    assert things["a"] == 2
    overrides = "{thing: !new:collections.Counter {b: 3}}"
    things = load_hyperpyyaml(yaml, overrides=overrides)
    assert things["thing"]["b"] == 3

    # String replacement
    yaml = """
    a: abc
    b: !ref <a>
    thing: !new:collections.Counter
        a: !ref <a>
    thing2: !new:zip
        - !ref <a>
        - abc
    """
    things = load_hyperpyyaml(yaml)
    assert things["thing"]["a"] == things["a"]
    assert things["a"] == things["b"]
    assert next(things["thing2"]) == ("a", "a")

    # String interpolation
    yaml = """
    a: "a"
    b: !ref <a>/b
    """
    things = load_hyperpyyaml(yaml)
    assert things["b"] == "a/b"

    # Substitution with string conversion
    yaml = """
    a: 1
    b: !ref <a>/b
    """
    things = load_hyperpyyaml(yaml)
    assert things["b"] == "1/b"

    # Nested structures:
    yaml = """
    constants:
        a: 1
    thing: !new:collections.Counter
        other: !new:collections.Counter
            a: !ref <constants[a]>
    """
    things = load_hyperpyyaml(yaml)
    assert things["thing"]["other"].__class__ == Counter
    assert things["thing"]["other"]["a"] == things["constants"]["a"]

    # Positional arguments
    yaml = """
    a: hello
    thing: !new:collections.Counter
        - !ref <a>
    """
    things = load_hyperpyyaml(yaml)
    assert things["thing"]["l"] == 2

    # Invalid class
    yaml = """
    thing: !new:abcdefg.hij
    """
    with pytest.raises(ImportError):
        things = load_hyperpyyaml(yaml)

    # Invalid reference
    yaml = """
    constants:
        a: 1
        b: !ref <constants[c]>
    """
    with pytest.raises(ValueError):
        things = load_hyperpyyaml(yaml)

    # Anchors and aliases
    yaml = """
    thing1: !new:collections.Counter &thing
        a: 3
        b: 5
    thing2: !new:collections.Counter
        <<: *thing
        b: 7
    """
    things = load_hyperpyyaml(yaml)
    assert things["thing1"]["a"] == things["thing2"]["a"]
    assert things["thing1"]["b"] != things["thing2"]["b"]

    # Test references point to same object
    yaml = """
    thing1: !new:collections.Counter
        a: 3
        b: 5
    thing2: !ref <thing1>
    thing3: !new:hyperpyyaml.TestThing
        - !ref <thing1>
        - abc
    """
    things = load_hyperpyyaml(yaml)
    assert things["thing2"]["b"] == things["thing1"]["b"]
    things["thing2"]["b"] = 7
    assert things["thing2"]["b"] == things["thing1"]["b"]
    assert things["thing3"].args[0] == things["thing1"]

    # Copy tag
    yaml = """
    thing1: !new:collections.Counter
        a: 3
        b: 5
    thing2: !copy <thing1>
    """
    things = load_hyperpyyaml(yaml)
    assert things["thing2"]["b"] == things["thing1"]["b"]
    things["thing2"]["b"] = 7
    assert things["thing2"]["b"] != things["thing1"]["b"]

    # Name tag
    yaml = """
    Counter: !name:collections.Counter
    """
    things = load_hyperpyyaml(yaml)
    counter = things["Counter"]()
    assert counter.__class__ == Counter

    # Module tag
    yaml = """
    mod: !module:collections
    """
    things = load_hyperpyyaml(yaml)
    assert things["mod"].__name__ == "collections"

    # Apply tag
    yaml = """
    a: !apply:sum [[1, 2]]
    """
    things = load_hyperpyyaml(yaml)
    assert things["a"] == 3

    # Apply method
    yaml = """
    a: "A STRING"
    common_kwargs:
        thing1: !ref <a.lower>
        thing2: 2
    c: !apply:hyperpyyaml.TestThing.from_keys
        args:
            - 1
            - 2
        kwargs: !ref <common_kwargs>
    """
    things = load_hyperpyyaml(yaml)
    assert things["c"].kwargs["thing1"]() == "a string"
    assert things["c"].specific_key() == "a string"

    # Applyref tag
    yaml = """
    # 1. Pass the positional and keyword arguments at the same time. Like `!!python/object/apply:module.function` in pyyaml
    c: !applyref:sorted
        _args:
            - [3, 4, 1, 2]
        _kwargs:
            reverse: False
    d: !ref <c>-<c>

    # 2. Only pass the keyword arguments
    e: !applyref:random.randint
        a: 1
        b: 3
    f: !ref <e><e>

    # 3. Only pass the positional arguments
    g: !applyref:random.randint
        - 1
        - 3
    h: !ref <g><g>

    # 4. No arguments
    i: !applyref:random.random
    j: !ref <i>
    """
    things = load_hyperpyyaml(yaml)
    assert things["d"] == "[1, 2, 3, 4]-[1, 2, 3, 4]"
    assert things["f"] in [11, 22, 33]
    assert things["h"] in [11, 22, 33]
    assert things["j"] < 1 and things["j"] >= 0

    # Refattr:
    yaml = """
    thing1: "A string"
    thing2: !ref <thing1.lower>
    thing3: !new:hyperpyyaml.TestThing
        - !ref <thing1.lower>
        - abc
    """
    things = load_hyperpyyaml(yaml)
    assert things["thing2"]() == "a string"
    assert things["thing3"].args[0]() == "a string"

    # Placeholder
    yaml = """
    a: !PLACEHOLDER
    """
    with pytest.raises(ValueError) as excinfo:
        things = load_hyperpyyaml(yaml)
    assert str(excinfo.value) == "'a' is a !PLACEHOLDER and must be replaced."

    # Import
    imported_yaml = """
    a: 10
    b: !PLACEHOLDER
    c: !ref <a> // <b>
    """

    import os.path

    test_yaml_file = os.path.join(tmpdir, "test.yaml")
    with open(test_yaml_file, "w") as w:
        w.write(imported_yaml)

    yaml = f"""
    b: !PLACEHOLDER
    import: !include:{test_yaml_file}
        a: 3
        b: !ref <b>
    d: !ref <import[c]>
    """

    things = load_hyperpyyaml(yaml, {"b": 3})
    assert things["import"]["a"] == things["b"]
    assert things["import"]["c"] == 1
    assert things["d"] == things["import"]["c"]

    things = load_hyperpyyaml(yaml, {"import": {"a": 6}, "b": 3})
    assert things["import"]["a"] == 6
    assert things["import"]["c"] == 2

    things = load_hyperpyyaml(yaml, "import:\n  a: 6\nb: 3\nd: 5")
    assert things["import"]["a"] == 6
    assert things["d"] == 5

    # Dumping
    dump_dict = {
        "data_folder": Placeholder(),
        "examples": {"ex1": RefTag(os.path.join("<data_folder>", "ex1.wav"))},
    }

    from io import StringIO

    stringio = StringIO()
    dump_hyperpyyaml(dump_dict, stringio)
    assert stringio.getvalue() == (
        "data_folder: !PLACEHOLDER\nexamples:\n"
        "  ex1: !ref <data_folder>/ex1.wav\n"
    )

    # !include with override
    yaml_1_path = os.path.join(tmpdir, 'f1.yaml')
    yaml_2_path = os.path.join(tmpdir, 'f2.yaml')

    yaml_1_content = f'''
    k1: v1
    k2: !include:{yaml_2_path}
    '''
    yaml_2_content = f'k3: v3'

    with open(yaml_2_path, 'w') as f:
        f.write(yaml_2_content)

    loaded_yaml_1 = load_hyperpyyaml(yaml_1_content, overrides='k1: new_v1')
    print(loaded_yaml_1)

    assert loaded_yaml_1.get('k1') == 'new_v1'  # 'v1' is overridden by 'new_v1
    assert loaded_yaml_1['k2'].get('k1') is None  # no unexpected key inserted to the included yaml file
