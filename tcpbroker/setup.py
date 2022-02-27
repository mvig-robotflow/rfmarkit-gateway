from setuptools import setup, find_packages

setup(
    name="tcpbroker",
    version="1.0",
    author="davidliyutong",
    author_email="davidliyutong@sjtu.edu.cn",
    description="IMU message broker",
    packages=["tcpbroker", "tcpbroker.applications", "tcpbroker.tasks"],
    python_requires=">=3.6",
    # entrypoints={
    #     'console_scripts': [
    #         'tcpbroker = tcpbrocker.main:main'
    #     ]
    # }
)
