from setuptools import setup, find_packages
from setuptools.command.install import install
import subprocess
import sys
import os

class CustomInstall(install):
    """Custom installation to build bloom filter."""
    def run(self):
        # Run the original install
        install.run(self)

        # Build and bloom filter
        #print("Building bloom filter...")
        #subprocess.check_call([sys.executable, "build_bloom_filter.py"])


setup(
    name="aiterm",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    package_data={
        "aiterm": ["ignore_commands.txt", "ignore_commands_bloom.pkl"],
    },
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
        "mmh3>=3.0",
        "bitarray>=2.0",
    ],
    author="AI Terminal Team",
    description="AI-powered terminal command assistant",
    python_requires=">=3.8",
    cmdclass={
        'install': CustomInstall,
    },
)
