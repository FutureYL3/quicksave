from setuptools import setup, find_packages
import pathlib

setup(
    name="quicksave",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "psutil>=5.9.0",
        "PyQt6>=6.4.0",
    ],
    entry_points={
        "console_scripts": [
            "quicksave=quicksave.core.cli:main",
            "quicksave-gui=quicksave.gui.main:main",
        ],
    },
    python_requires=">=3.8",
    author="Your Name",
    author_email="your.email@example.com",
    description="进程快照和恢复工具",
    long_description=open("README.md").read() if pathlib.Path("README.md").exists() else "",
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/quicksave",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
) 