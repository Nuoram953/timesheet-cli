from setuptools import setup, find_packages

setup(
    name="timesheet-cli",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "click>=8.1",
        "requests>=2.31",
        "PyYAML>=6.0",
    ],
    entry_points={
        "console_scripts": [
            "timesheet=timesheet.cli:main",
        ],
    },
    python_requires=">=3.9",
)
