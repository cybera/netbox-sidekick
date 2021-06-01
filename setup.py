#!/usr/bin/env python
from setuptools import setup, find_packages

VERSION = "0.0.1"

setup(
    name='sidekick',
    author='Cybera',
    version=VERSION,
    license='Apache 2.0',
    url='https://github.com/cybera/netbox-sidekick',
    description="A sidekick for NetBox to assist with managing an NREN",
    packages=find_packages(),
    install_requires=[],
    include_package_data=True,
)
