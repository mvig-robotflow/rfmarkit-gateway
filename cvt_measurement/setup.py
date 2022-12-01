from setuptools import setup

requirements = [
    'numpy',
    'tqdm',
]

setup(
    name="cvt_measurement",
    version="1.4",
    author="davidliyutong",
    author_email="davidliyutong@sjtu.edu.cn",
    description="Toolkit to convert IMU measurement",
    packages=["cvt_measurement", "cvt_measurement.common", "cvt_measurement.functional"],
    python_requires=">=3.6",
    install_requires=requirements
)
