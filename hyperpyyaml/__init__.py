"""HyperPyYAML -- an extended yaml syntax for use with python.

Authors:
 * Peter Plantinga 2020, 2021
 * Aku Rouhe 2020
"""
from .core import (
    load_hyperpyyaml,
    resolve_references,
    RefTag,
    Placeholder,
    dump_hyperpyyaml,
)


class TestThing:
    # Purely for test purposes.
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    @classmethod
    def from_keys(cls, args, kwargs):
        obj = cls()
        obj.specific_key = kwargs["thing1"]
        obj.args = args
        obj.kwargs = kwargs
        return obj
