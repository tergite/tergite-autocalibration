import setuptools

with open("requirements.txt", mode="r") as _f:
    REQUIREMENTS = _f.readlines()

setuptools.setup(
    name="tergite_auto_calibration_lite",
    version="0.4.0",
    author="Eleftherios Moschandreou",
    author_email="elemos@chalmers.se",
    description="Communication handling for automatic calibration of multi-qubit devices using Qblox instruments. Minimal experimental version",
    long_description="Minimal version of the automatic calibration under the tergite framework. Communication handling and schedules library for the automatic characterization and tune-up of a multi-qubit device. Designed only for Qblox clusters control instruments.",
    long_description_content_type="text/markdown",
    url="https://bitbucket.org/qtlteam/tergite-autocalibration-lite/src/main/",
    packages=setuptools.find_packages(),
    include_package_data=True,
    license="Apache 2.0",
    install_requires=REQUIREMENTS,
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
    ],
)

