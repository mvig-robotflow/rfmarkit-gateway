from setuptools import setup

requirements = [
    'numpy',
    'tqdm',
]

setup(
    name="cvt_measurement",
    version="1.3",
    author="davidliyutong",
    author_email="davidliyutong@sjtu.edu.cn",
    description="Toolkit to convert IMU measurement",
    packages=["cvt_measurement"],
    python_requires=">=3.6",
    install_requires=requirements
)
