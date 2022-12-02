import os

from setuptools import setup

requires = open("./requirements.txt", "r").readlines() if os.path.exists("./requirements.txt") else open("./tcpbroker.egg-info/requires.txt", "r").readlines()

setup(
    name="tcpbroker",
    version="1.5",
    author="davidliyutong",
    author_email="davidliyutong@sjtu.edu.cn",
    description="IMU message broker",
    packages=[
        "tcpbroker",
        "tcpbroker.cmd",
        "tcpbroker.tasks",
        "tcpbroker.common",
        "tcpbroker.scripts",
    ],
    python_requires=">=3.7",
    install_requires=requires,
    entrypoints={
        'console_scripts': [
            'tcpbroker = tcpbrocker.main:main'
        ]
    }
)
