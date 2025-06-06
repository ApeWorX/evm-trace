#!/usr/bin/env python
from setuptools import find_packages, setup

extras_require = {
    "test": [  # `test` GitHub Action jobs uses this
        "pytest>=6.0",  # Core testing package
        "pytest-xdist",  # Multi-process runner
        "pytest-cov",  # Coverage analyzer plugin
        "hypothesis>=6.2.0,<7.0",  # Strategy-based fuzzer
        "eth-hash[pysha3]",  # For eth-utils address checksumming
    ],
    "lint": [
        "black>=25.1.0,<26",  # Auto-formatter and linter
        "mypy>=1.15.0,<2",  # Static type analyzer
        "types-setuptools",  # Needed for mypy type shed
        "flake8>=7.2.0,<8",  # Style linter
        "flake8-breakpoint>=1.1.0,<2",  # Detect breakpoints left in code
        "flake8-print>=4.0.1,<5",  # Detect print statements left in code
        "flake8-pydantic",  # For detecting issues with Pydantic models
        "flake8-type-checking",  # Detect imports to move in/out of type-checking blocks
        "isort>=5.10.1,<6",  # Import sorting linter
        "mdformat>=0.7.22",  # Auto-formatter for markdown
        "mdformat-gfm>=0.3.5",  # Needed for formatting GitHub-flavored markdown
        "mdformat-frontmatter>=0.4.1",  # Needed for frontmatters-style headers in issue templates
        "mdformat-pyproject>=0.0.2",  # Allows configuring in pyproject.toml
    ],
    "release": [  # `release` GitHub Action job uses this
        "setuptools>=75.6.0",  # Installation tool
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
        "cchecksum>=0.0.3,<1",
        "eth-pydantic-types>=0.2.0,<0.3",
        "eth-utils>=2.3.1,<6",
        "msgspec>=0.8",
        "pydantic>=2.5.2,<3",
        "py-evm>=0.10.1b1,<0.13",
    ],
    python_requires=">=3.9,<4",
    extras_require=extras_require,
    py_modules=["evm_trace"],
    license="Apache-2.0",
    zip_safe=False,
    keywords="ethereum",
    packages=find_packages(exclude=["tests", "tests.*"]),
    package_data={"evm_trace": ["py.typed"]},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Operating System :: MacOS",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
)
