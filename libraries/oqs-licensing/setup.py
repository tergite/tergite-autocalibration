# This code is part of Tergite
#
# (C) Copyright Chalmers Next Labs 2025
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.


from setuptools import setup, find_packages

setup(
    name="oqs-licensing",
    version="1.0.10",
    description="",
    author="Stefan Hill",
    author_email="stefanhi@chalmers.se",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    python_requires=">=3.9,<4.0",
    packages=find_packages(exclude=["tests*", "docs*", "examples*"]),
    include_package_data=True,
    install_requires=[],
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
)
