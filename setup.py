#!/usr/bin/env python

import codecs

try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages


setup(
    name='python-doublescript',
    version='1.0.0',
    author='Frankie Dintino',
    author_email='fdintino@gmail.com',
    url='https://github.com/fdintino/python-doublescript',
    description=(
        'allows changing the value of "2 + 2" (generally to equal "5") at runtime'),
    long_description=codecs.open('README.rst', encoding='utf-8').read(),
    packages=find_packages(),
    zip_safe=True,
    install_requires=[
        'six>=1.7.0',
    ],
    include_package_data=True,
    license="BSD",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ])
