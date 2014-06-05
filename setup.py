#!/usr/bin/env python
# Copyright (C) 2014 SEE AUTHORS FILE
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys

from distutils.core import setup


setup(
    name='reworkerjuicer',
    version='0.0.1',
    description='',
    author='See AUTHORS file',
    author_email='inception@redhat.com',
    url='https://github.com/rhinception/re-worker-juicer',
    license='AGPLv3',
    package_dir={'replugin': 'replugin'},
    packages=['replugin', 'replugin.juicerworker']
)
