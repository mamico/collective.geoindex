# -*- coding: utf-8 -*-
"""Installer for the collective.geoindex package."""

from setuptools import find_packages
from setuptools import setup


long_description = "\n\n".join(
    [
        open("README.rst").read(),
        open("CONTRIBUTORS.rst").read(),
        open("CHANGES.rst").read(),
    ]
)


setup(
    name="collective.geoindex",
    version="1.0a1",
    description="An add-on for Plone",
    long_description=long_description,
    # Get more from https://pypi.org/classifiers/
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Zope2',
        'Framework :: Zope :: 4',
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
    ],
    keywords="Python Plone CMS",
    author="Mauro Amico",
    author_email="mauro.amico@gmail.com",
    url="https://github.com/collective/collective.geoindex",
    project_urls={
        "PyPI": "https://pypi.org/project/collective.geoindex/",
        "Source": "https://github.com/collective/collective.geoindex",
        "Tracker": "https://github.com/collective/collective.geoindex/issues",
        # 'Documentation': 'https://collective.geoindex.readthedocs.io/en/latest/',
    },
    license="GPL version 2",
    packages=find_packages("src", exclude=["ez_setup"]),
    namespace_packages=["collective"],
    package_dir={"": "src"},
    include_package_data=True,
    zip_safe=False,
    python_requires=">=3.7",
    install_requires=[
        "setuptools",
        # -*- Extra requirements: -*-
        'Products.ZCatalog',
        'rtree',
    ],
    extras_require={
        "test": [
            "plone.testing",
        ],
    },
)
