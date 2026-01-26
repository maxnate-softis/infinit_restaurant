from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

setup(
    name="infinit_restaurant",
    version="0.0.1",
    description="Restaurant Management Module for Infinit Platform",
    author="Maxnate Africa",
    author_email="dev@maxnate.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
)
