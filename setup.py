#!/usr/bin/env python

from setuptools import setup

setup(
    name='isatools',
    version='0.12.0alpha',
    packages=['isatools',
              'isatools.convert',
              'isatools.create',
              'isatools.errors',
              'isatools.io',
              'isatools.net',
              'isatools.tests'
              ],
    package_data={'isatools': [
        'resources/schemas/cedar/*.json',
        'resources/schemas/isa_model_version_1_0_schemas/core/*.json',
        'resources/schemas/configs/*.json',
        'resources/schemas/configs/schemas/*.json',
        'resources/config/json/default/*.json',
        'resources/config/json/default/schemas/*.json',
        'resources/config/json/sra/*.json',
        'resources/config/json/sra/schemas/*.json',
        'resources/config/xml/*.xml',
        'resources/sra_schemas/*.xsd',
        'resources/sra_templates/*.xml',
        'resources/tab_templates/*.txt',
        'net/resources/biocrates/*',
        'net/resources/sra/*.xsl',
        'net/resources/sra/*.xml',
        'resources/isatools.ini'],
        '': ['LICENSE.txt', 'README.md']},
    description='Metadata tracking tools help to manage an increasingly diverse set of life science, environmental and biomedical experiments',
    author='ISA Infrastructure Team',
    author_email='isatools@googlegroups.com',
    url='https://github.com/ISA-tools/isa-api',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        ],
    install_requires=[
        'numpy~=1.19.4',
        'jsonschema~=3.2.0',
        'pandas~=1.1.4',
        'networkx~=2.5',
        'lxml~=4.6.1',
        'requests~=2.24',
        'chardet~=3.0.4',
        'iso8601~=0.1.13',
        'jinja2~=2.11.2',
        'beautifulsoup4~=4.9.3',
        'mzml2isa==1.0.3',
        'biopython~=1.78',
        'progressbar2~=3.53.1',
        'deepdiff~=5.0.2',
        'PyYAML~=5.3.1'
    ],
    test_suite='tests'
)
