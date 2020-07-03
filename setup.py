import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="stonks-data",
    version="0.0.1",
    author="Justin van Heek",
    author_email="justin.vanheek@vhsoftware.dev",
    description="A python package for accessing historical stock data. This library was designed with a plugin "
                "framework for easy extendability and the data can optionally be stored in a local cache for quicker "
                "access.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/JVH-Software/Stonks",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
