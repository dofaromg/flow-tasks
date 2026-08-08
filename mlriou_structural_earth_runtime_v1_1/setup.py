"""
Setup configuration for MRLiou Structural Earth Runtime v1.1
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="mlriou-structural-earth-runtime",
    version="1.1.0",
    author="MR.Liou",
    author_email="mrliou@example.com",
    description="MRLiou Structural Earth Runtime - 中心不變的骨架定義與壓力場映射",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dofaromg/flow-tasks",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
    install_requires=[
        # No external dependencies required
    ],
    entry_points={
        "console_scripts": [
            "mlriou-earth=mlriou_earth.cli:main",
        ],
    },
)
