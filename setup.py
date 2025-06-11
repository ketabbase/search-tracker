from setuptools import setup, find_packages

setup(
    name="search-tracker",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "selenium>=4.0.0",
    ],
    entry_points={
        'console_scripts': [
            'search-tracker=search_tracker.main:main',
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="A tool to track and analyze web search behavior",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/search-tracker",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
) 