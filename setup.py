import os

from setuptools import setup

requires = open("requirements.txt", "r").readlines() if os.path.exists("requirements.txt") else open("./markit_tcpbroker.egg-info/requires.txt", "r").readlines()
print("#-------------------    ", str(os.listdir("./")))
setup(
    name="markit-tcpbroker",
    version="1.6",
    author="davidliyutong",
    author_email="davidliyutong@sjtu.edu.cn",
    description="IMU message broker",
    packages=[
        "tcpbroker",
        "tcpbroker.cmd",
        "tcpbroker.common",
        "tcpbroker.functional",
        "tcpbroker.scripts",
        "tcpbroker.tasks",
    ],
    python_requires=">=3.7",
    install_requires=requires,
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown"
)
