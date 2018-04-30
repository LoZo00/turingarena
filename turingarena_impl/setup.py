#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name="turingarena_impl",
    entry_points={
        "pytest11": [
            "turingarena=turingarena_impl.pytestplugin",
        ]
    },
)
