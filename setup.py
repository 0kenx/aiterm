from setuptools import setup, find_packages

setup(
    name="aiterm",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    entry_points={
        "console_scripts": [
            "at=aiterm.main:main",
        ],
    },
    install_requires=[
        "click>=8.0",
        "rich>=10.0",
        "pyyaml>=5.0",
        "requests>=2.0",
        "openai>=1.0.0",
    ],
    author="AI Terminal Team",
    description="AI-powered terminal command assistant",
    python_requires=">=3.8",
)
