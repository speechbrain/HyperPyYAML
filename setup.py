#!/usr/bin/env python3
import setuptools

with open("README.md") as f:
    long_description = f.read()

setuptools.setup(
    name="HyperPyYAML",
    version="1.0.0",
    description="Extensions to YAML syntax for better python interaction",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/speechbrain/HyperPyYAML",
    author="Peter Plantinga, Aku Rouhe",
    author_email="speechbrain@gmail.com",
    packages=["hyperpyyaml"],
    install_requires=["pyyaml>=5.1", "ruamel.yaml>=0.15"],
)
