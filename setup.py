from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="search-tracker",
    version="1.0.0",
    author="Ketabbase Research Team",
    author_email="mahsatorabi515@gmail.com",
    description="A privacy-focused research tool for tracking and analyzing web search behavior",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ketabbase/search-tracker",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Scientific/Engineering",
    ],
    python_requires=">=3.6",
    install_requires=[
        "selenium>=4.0.0",
        "webdriver-manager>=3.8.0",
    ],
    entry_points={
        "console_scripts": [
            "search-tracker=search_tracker.main:main",
        ],
    },
) 