"""
Package configuration.
"""

from setuptools import setup

setup(
    name='proflow',
    version='0.1.0',
    packages=['proflow'],
    include_package_data=True,
    install_requires=[
        'Flask',
    ],
    python_requires='>=3.8',
)
