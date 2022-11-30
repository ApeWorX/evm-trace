#!/usr/bin/env python
from setuptools import find_packages, setup

extras_require = {
    "test": [  # `test` GitHub Action jobs uses this
        "pytest>=6.0",  # Core testing package
        "pytest-xdist",  # multi-process runner
        "pytest-cov",  # Coverage analyzer plugin
        "hypothesis>=6.2.0,<7.0",  # Strategy-based fuzzer
        "eth-hash[pysha3]",  # For eth-utils address checksumming
    ],
    "lint": [
        "black>=22.10.0",  # auto-formatter and linter
        "mypy>=0.991",  # Static type analyzer
        "types-setuptools",  # Needed due to mypy typeshed
        "flake8>=5.0.4",  # Style linter
        "isort>=5.10.1",  # Import sorting linter
    ],
    "release": [  # `release` GitHub Action job uses this
        "setuptools",  # Installation tool
        "wheel",  # Packaging tool
        "twine",  # Package upload tool
    ],
    "dev": [
        "commitizen",  # Manage commits and publishing releases
        "pre-commit",  # Ensure that linters are run prior to committing
        "pytest-watch",  # `ptw` test watcher/runner
        "IPython",  # Console for interacting
        "ipdb",  # Debugger (Must use `export PYTHONBREAKPOINT=ipdb.set_trace`)
    ],
}

# NOTE: `pip install -e .[dev]` to install package
extras_require["dev"] = (
    extras_require["test"]
    + extras_require["lint"]
    + extras_require["release"]
    + extras_require["dev"]
)

with open("./README.md") as readme:
    long_description = readme.read()


setup(
    name="evm-trace",
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
    description="""evm-trace: Ethereum Virtual Machine transaction tracing tool""",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="ApeWorX Ltd.",
    author_email="admin@apeworx.io",
    url="https://github.com/ApeWorX/evm-trace",
    include_package_data=True,
    install_requires=[
        "pydantic>=1.10.1,<2",
        "py-evm>=0.6.0a1",
        "hexbytes>=0.2.3,<1",
        "eth-utils>=2",
        "ethpm-types>=0.3.7,<0.4",
        "msgspec>=0.8",
    ],
    python_requires=">=3.8,<4",
    extras_require=extras_require,
    py_modules=["evm_trace"],
    license="Apache-2.0",
    zip_safe=False,
    keywords="ethereum",
    packages=find_packages(exclude=["tests", "tests.*"]),
    package_data={"evm_trace": ["py.typed"]},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Operating System :: MacOS",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
