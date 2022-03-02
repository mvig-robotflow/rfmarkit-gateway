from setuptools import setup, find_packages

requirements = [
    'flask',
    'gevent',
]

setup(
    name="tcpbroker",
    version="1.2",
    author="davidliyutong",
    author_email="davidliyutong@sjtu.edu.cn",
    description="IMU message broker",
    packages=["tcpbroker", "tcpbroker.applications", "tcpbroker.tasks"],
    python_requires=">=3.6",
    install_requires=requirements,
    entrypoints={
        'console_scripts': [
            'tcpbroker = tcpbrocker.main:main'
        ]
    }
)
