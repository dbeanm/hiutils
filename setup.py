import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="hiutils",
    version="0.2.2",
    author="Dan Bean",
    author_email="daniel.bean@kcl.ac.uk",
    description="Utilities for health informatics",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dbeanm/hiutils",
    packages=setuptools.find_packages(),
    install_requires=[
        "numpy~=1.21.4",
        "pandas~=1.3.4",
        "scipy~=1.7.2",
        "statsmodels~=0.13.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)