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

extras_require = {
    "dev": ["jupyter>=1.0.0,<2.0.0", "black>=24.10.0,<25.0.0", "isort>=5.12.0,<6.0.0"],
    "test": ["pytest>=8.3.3,<9.0.0", "requests-mock>=1.11.0,<2.0.0"],
}
extras_require["all"] = extras_require["dev"] + extras_require["test"]


setup(
    name="tergite-autocalibration",
    version="2025.03.0",
    description="Commandline application to calibrate the WACQT quantum computers automatically",
    author="Eleftherios Moschandreou, Liangyu Chen, Stefan Hill, Amr Osman, Tong Liu, Joel Sandås, Pontus Vikstål, Michele Faucci Giannelli",
    author_email="contact@quantum.chalmersnextlabs.se",
    maintainer="Chalmers Next Labs AB",
    maintainer_email="contact@quantum.chalmersnextlabs.se",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    license="Apache-2.0",
    packages=find_packages(
        include=["tergite_autocalibration", "tergite_autocalibration.*"]
    ),
    python_requires=">=3.10,<3.11",
    install_requires=[
        "colorama==0.4.6",
        "h5netcdf==1.4.0",
        "h5py==3.7.0",
        "Jinja2==3.1.2",
        "numpy>=2.0",
        "qblox-instruments==0.14.2",
        "qcodes==0.49.0",
        "quantify-core==0.7.8",
        "quantify-scheduler==0.21.2",
        "redis==5.0.0",
        "scikit-learn==1.5.2",
        "toml==0.10.2",
        "python-dotenv==1.0.1",
        "requests>=2.32.3,<3.0.0",
        "typer>=0.12.5,<1.0.0",
        "jokeapi==1.0.5",
        "optuna==4.0.0",
        "netcdf4==1.7.1.post2",
        "tomlkit>=0.13.2,<1.0.0",
        "rich>=14.0.0,<15.0.0",
        "click<8.2.0",
        "matplotlib>=3.9.3,<4.0.0",
        "scipy>=1.14.1,<2.0.0",
        "pandas>=2.2.3,<3.0.0",
        "xarray>=2024.11.0,<2025.0.0",
        "filelock>=3.16.1,<4.0.0",
        "pyqtgraph>=0.13.7,<1.0.0",
        "pyqt5>=5.15.11,<6.0.0",
        "pydantic==2.9.2",
    ],
    extras_require=extras_require,
    entry_points={"console_scripts": ["acli=tergite_autocalibration.tools.cli:cli"]},
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    include_package_data=True,
    zip_safe=False,
)
