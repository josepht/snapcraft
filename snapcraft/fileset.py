# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright (C) 2017 Canonical Ltd
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os

from snapcraft import file_utils


class Filepath(object):
    def __init__(self, fpath, **kwargs):
        if fpath in ['*', '.']:
            fpath = ''
        self._install_file = fpath
        self._stage_file = kwargs.get('stage_file', fpath)
        self._install_dir = kwargs.get('install_dir', 'install')
        self._stage_dir = kwargs.get('stage_dir', 'stage')
        self._prime_dir = kwargs.get('prime_dir', 'prime')
        self._follow_symlinks = kwargs.get('follow_symlinks', False)

    @property
    def install_path(self):
        return os.path.join(
            self._install_dir,
            self._install_file
        )

    @property
    def install_file(self):
        return self._install_file

    @install_file.setter
    def install_file(self, fpath):
        # set stage fpath if they were the same
        if self._stage_file == self._install_file:
            self._stage_file = fpath
        self._install_file = fpath

    @property
    def stage_path(self):
        return os.path.join(
            self._stage_dir,
            self._stage_file
        )

    @property
    def stage_file(self):
        return self._stage_file

    @stage_file.setter
    def stage_file(self, fpath):
        self._stage_file = fpath

    @property
    def prime_path(self):
        return os.path.join(
            self._prime_dir,
            self._stage_file
        )

    @property
    def install_dir(self):
        return self._install_dir

    @install_dir.setter
    def install_dir(self, dir):
        self._install_dir = dir

    @property
    def stage_dir(self):
        return self._stage_dir

    @stage_dir.setter
    def stage_dir(self, dir):
        self._stage_dir = dir

    @property
    def prime_dir(self):
        return self._prime_dir

    @prime_dir.setter
    def prime_dir(self, dir):
        self._prime_dir = dir

    def link_or_copy(self, src, dst):
        file_utils.link_or_copy_glob(src, dst,
                                     follow_symlinks=self._follow_symlinks)

    def old_link_or_copy(self, src, dst):
        src_dir, src_file = os.path.split(src)
        if src_file == '*':
            src = src_dir
        if os.path.isdir(src):
            file_utils.create_similar_directory(
                src, dst, follow_symlinks=self._follow_symlinks)
            file_utils.link_or_copy_tree(src, dst)
        else:
            file_utils.link_or_copy(
                src, dst, follow_symlinks=self._follow_symlinks)

    def stage(self):
        self.link_or_copy(self.install_path, self.stage_path)

    def prime(self):
        self.link_or_copy(self.stage_path, self.prime_path)

    def organize(self, orig, new):
        parts = os.path.split(orig)
        matches = [self.install_file, '*']
        if orig in matches:
            self.stage_file = new
            if orig == '*':
                self.stage_file = '{}/'.format(new)
        elif len(parts) > 0 and parts[1] in matches:
            if parts[1] == '*':
                self.stage_file = '{}/'.format(new)
                self.install_file = orig

    def __str__(self):
        return str((self.install_path, self.stage_path, self.prime_path))


class Fileset(object):

    def __init__(self):
        self.files = []

    def add(self, filepath):
        self.files.append(filepath)

    def replace(self, index, filepath):
        if len(self.files) < index:
            raise Exception("invalid index: {}".format(index))

        self.files[index] = filepath

    def stage(self):
        for filepath in self.files:
            filepath.stage()

    def organize(self, organize_fs):
        for filepath in self.files:
            filepath.organize(organize_fs)

    def __add__(self, fileset):
        self.files += fileset.files

    def __sub__(self, fileset):
        self.files = [
            fp for fp in self.files if fp not in fileset.files
        ]

    def __str__(self):
        return str([str(f) for f in self.files])
