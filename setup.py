#!/usr/bin/env python
import os
import re

from setuptools import setup

# Synchronize version from code.
version = re.findall(r"__version__ = \"(.*?)\"",
                     open(os.path.join("snfpipe", "__init__.py")).read())[0]

setup(name="snfpipe", 
      version=version,
      description="Tools for running the Nearby Supernova Factory pipeline",
      long_description="",
      classifiers = ["Development Status :: 4 - Beta",
                     "Programming Language :: Python :: 2",
                     "Programming Language :: Python :: 3",
                     "License :: OSI Approved :: MIT License",
                     "Topic :: Scientific/Engineering",
                     "Topic :: Scientific/Engineering :: Astronomy",
                     "Intended Audience :: Science/Research"],
      packages=["snfpipe"],
      url="http://github.com/snfactory/pipeline",
      author="Kyle Barbary",
      author_email="kylebarbary@gmail.com")
