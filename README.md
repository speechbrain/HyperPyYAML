Introduction
------------

A crucial element of systems for data-analysis is laying out all the
hyperparameters of that system so they can be easily examined and modified.
We add a few useful extensions to a popular human-readable data-serialization
language known as YAML (YAML Ain't Markup Language). This provides support
for a rather expansive idea of what constitutes a hyperparameter, and cleans
up python files for data analysis to just the bare algorithm.

### Table of Contents
* [YAML basics](#yaml-basics)
* [HyperPyYAML](#hyperpyyaml)
    * [Objects](#objects)
    * [Aliases](#aliases)
    * [Tuples](#tuples)
* [How to use HyperPyYAML](#how-to-use-hyperpyyaml)
* [Conclusion](#conclusion)

YAML basics
-----------

YAML is a data-serialization language, similar to JSON, and it supports
three basic types of nodes: scalar, sequential, and mapping. PyYAML naturally
converts sequential nodes to python lists and mapping nodes to python dicts.

Scalar nodes can take one of the following forms:

```yaml
string: abcd  # No quotes needed
integer: 1
float: 1.3
bool: True
none: null
```

Note that we've used a simple mapping to demonstrate the scalar nodes. A mapping
is a set of `key: value` pairs, defined so that the key can be used to easily
retrieve the corresponding value. In addition to the format above, mappings
can also be specified in a similar manner to JSON:

```yaml
{foo: 1, bar: 2.5, baz: "abc"}
```

Sequences, or lists of items, can also be specified in two ways:

```yaml
- foo
- bar
- baz
```

or

```yaml
[foo, bar, baz]
```

Note that when not using the inline version, YAML uses whitespace to denote
nested items:

```yaml
foo:
    a: 1
    b: 2
bar:
    - c
    - d
```

YAML has a few more advanced features (such as
[aliases](https://pyyaml.org/wiki/PyYAMLDocumentation#aliases) and
[merge keys](https://yaml.org/type/merge.html)) that you may want to explore
on your own. We will briefly discuss one here since it is relevant for our
extensions: [YAML tags](https://pyyaml.org/wiki/PyYAMLDocumentation#tags).

Tags are added with a `!` prefix, and they specify the type of the node. This
allows types beyond the simple types listed above to be used. PyYAML supports a
few additional types, such as:

```yaml
!!set                           # set
!!timestamp                     # datetime.datetime
!!python/tuple                  # tuple
!!python/complex                # complex
!!python/name:module.name       # A class or function
!!python/module:package.module  # A module
!!python/object/new:module.cls  # An instance of a class
```

These can all be quite useful, however we found that this system was a bit
cumbersome, especially with the frequency with which we were using them. So
we decided to implement some shortcuts for these features, which we are
calling "HyperPyYAML".

HyperPyYAML
-----------

We make several extensions to yaml including easier object creation, nicer
aliases, and tuples.

### Objects

Our first extension is to simplify the structure for specifying an instance,
module, class, or function. As an example:

```yaml
model: !new:collections.Counter
```

This tag, prefixed with `!new:`, constructs an instance of the specified class.
If the node is a mapping node, all the items are passed as keyword arguments
to the class when the instance is created. A list can similarly be used to
pass positional arguments. See the following examples:

```yaml
foo: !new:collections.Counter
  - abracadabra
bar: !new: collections.Counter
  a: 2
  b: 1
  c: 5
```

We also simplify the interface for specifying a function or class or other
static Python entity:

```yaml
add: !name:operator.add
```

This code stores the `add` function. It can later be used in the usual way:

```python
>>> loaded_yaml = load_hyperpyyaml("add: !name:operator.add")
>>> loaded_yaml["add"](2, 4)
6
```

### Aliases

Another extension is a nicer alias system that supports things like
string interpolation. We've added a tag written `!ref` that
takes keys in angle brackets, and searches for them inside the yaml
file itself. As an example:

```yaml
folder1: abc/def
folder2: ghi/jkl
folder3: !ref <folder1>/<folder2>

foo: 1024
bar: 512
baz: !ref <foo> // <bar> + 1
```

This allows us to change some values and automatically change the
dependent values accordingly.
You can also refer to other references, and to sub-nodes using brackets.

```yaml
block_index: 1
cnn1:
    out_channels: !ref <block_index> * 64
    kernel_size: (3, 3)
cnn2: 
    out_channels: !ref <cnn1[out_channels]>
    kernel_size: (3, 3)
```

Finally, you can make references to nodes that are objects, not just scalars.

```python
yaml_string = """
foo: !new:collections.Counter
  a: 4
bar: !ref <foo>
baz: !copy <foo>
"""
loaded_yaml = load_hyperpyyaml(yaml_string)
loaded_yaml["foo"].update({"b": 10})
print(loaded_yaml["bar"])
print(loaded_yaml["baz"])
```

This provides the output:
```
Counter({'b': 10, 'a': 4})
Counter({'a': 4})
```

Note that `!ref` makes only a shallow copy, so updating `foo`
also updates `bar`. If you want a deep copy, use the `!copy` tag.

### Tuples

One last minor extension to the yaml syntax we've made is to implicitly
resolve any string starting with `(` and ending with `)` to a tuple.
This makes the use of YAML more intuitive for Python users.


How to use HyperPyYAML
---------------------

All of the listed extensions are available by loading yaml using the
`load_hyperpyyaml` function. This function returns an object in a similar
manner to pyyaml and other yaml libraries.
Also, `load_hyperpyyaml` takes an optional argument, `overrides`
which allows changes to any of the parameters listed in the YAML.
The following example demonstrates changing the `out_channels`
of the CNN layer:

```python
>>> yaml_string = """
... block_index: 1
... cnn1:
...   out_channels: !ref <block_index> * 64
...   kernel_size: (3, 3)
... cnn2: 
...   out_channels: !ref <cnn1[out_channels]>
...   kernel_size: (3, 3)
... """
>>> overrides = {"block_index": 2}
>>> with open("hyperparameters.yaml") as f:
...    hyperparameters = load_hyperpyyaml(f, overrides)
>>> hyperparameters["block_index"]
2
>>> hyperparameters["cnn2"]["out_channels"]
128
```

Conclusion
----------

We've defined a number of extensions to the YAML syntax, designed to
make it easier to use for hyperparameter specification. Feedback is welcome!
