#
# tzxtools - a collection for processing tzx files
#
# Copyright (C) 2018 Richard "Shred" Körber
#   https://codeberg.org/shred/tzxtools
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from setuptools import setup

def readme():
    with open('README.md') as f:
        return f.read()

setup(
    name='tzxtools',
    version='1.9.3',
    description='A tool collection for processing tzx files',
    long_description=readme(),
    long_description_content_type='text/markdown',
    url='https://codeberg.org/shred/tzxtools',
    keywords='ZX-Spectrum tzx wav',
    license='GPLv3+',

    python_requires='>=3',

    author='Richard Körber',
    author_email='dev@shredzone.de',

    project_urls={
        'Source': 'https://codeberg.org/shred/tzxtools',
        'Tracker': 'https://codeberg.org/shred/tzxtools/issues',
    },

    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: System :: Archiving',
        'Topic :: System :: Emulators',
        'Topic :: Utilities'
    ],

    packages=['tzxtools', 'tzxlib'],

    install_requires=[
        'numpy >= 1.20.0',
        'pypng >= 0.0.20',
        'sounddevice >= 0.4.0',
    ],

    entry_points={
        'console_scripts': [
            'tzxcat=tzxtools.tzxcat:main',
            'tzxcleanup=tzxtools.tzxcleanup:main',
            'tzxcut=tzxtools.tzxcut:main',
            'tzxls=tzxtools.tzxls:main',
            'tzxmerge=tzxtools.tzxmerge:main',
            'tzxplay=tzxtools.tzxplay:main',
            'tzxsplit=tzxtools.tzxsplit:main',
            'tzxtap=tzxtools.tzxtap:main',
            'tzxwav=tzxtools.tzxwav:main',
        ],
    },
)
