from setuptools import setup, find_packages

setup(
    name="autogen_converter",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "autogen>=0.2.0",
        "pyautogen>=0.2.0",
        "ollama>=0.1.6",
        "fix-busted-json>=0.0.1"
    ],
    python_requires=">=3.8",
) 