#!/usr/bin/env python3
import setuptools
from distutils.core import setup

setup(
    name="hyperYAML",
    version="0.0.1",
    description="Extensions to YAML syntax for better python interaction",
    author="Peter Plantinga, Aku Rouhe",
    author_email="speechbrain@gmail.com",
    packages=["hyper"],
    install_requires=["pyyaml", "ruamel.yaml"],
)
