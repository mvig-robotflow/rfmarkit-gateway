import os

from setuptools import setup

requires = open("./requirements.txt", "r").readlines() if os.path.exists("./requirements.txt") else open("./cvt_measurement.egg-info/requires.txt", "r").readlines()

setup(
    name="cvt_measurement",
    version="1.5",
    author="davidliyutong",
    author_email="davidliyutong@sjtu.edu.cn",
    description="Toolkit to convert IMU measurement",
    packages=["cvt_measurement", "cvt_measurement.common", "cvt_measurement.functional"],
    python_requires=">=3.7",
    install_requires=requires
)
