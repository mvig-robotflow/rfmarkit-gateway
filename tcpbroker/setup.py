from setuptools import setup

requirements = [
    'flask',
    'gevent',
]

setup(
    name="tcpbroker",
    version="1.3",
    author="davidliyutong",
    author_email="davidliyutong@sjtu.edu.cn",
    description="IMU message broker",
    packages=[
        "tcpbroker",
        "tcpbroker.applications",
        "tcpbroker.tasks",
        "tcpbroker.common",
        "tcpbroker.scripts",
    ],
    python_requires=">=3.6",
    install_requires=requirements,
    entrypoints={
        'console_scripts': [
            'tcpbroker = tcpbrocker.main:main'
        ]
    }
)
