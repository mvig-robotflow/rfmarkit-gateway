import os

from setuptools import setup

requires = open("requirements.txt", "r").readlines() if os.path.exists("requirements.txt") else open("./markit_gateway.egg-info/requires.txt", "r").readlines()
print("#-------------------    ", str(os.listdir("./")))
setup(
    name="markit-gateway",
    version="2.0.1",
    author="davidliyutong",
    author_email="davidliyutong@sjtu.edu.cn",
    description="IMU message broker",
    packages=[
        "markit_gateway",
        "markit_gateway.cmd",
        "markit_gateway.common",
        "markit_gateway.functional",
        "markit_gateway.scripts",
        "markit_gateway.tasks",
        "markit_gateway.tasks.obj",
    ],
    python_requires=">=3.7",
    install_requires=requires,
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown"
)
