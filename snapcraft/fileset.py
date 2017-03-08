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

import glob
import os

from snapcraft import file_utils


"""
A filepath is a path to a file or directory.

it may have a leading '-' which means to exclude the matching files.

for the stage step all filepath files are copied to the stage path

for the prime step all filepath files are copied to the prime path
"""

# Implementation notes (remove before merging)
#
# Filepath
# * each file or directory should have a filepath.
# * convert excludes to Filepaths with out the leading '-' but set is_exclude
# * compare should match based on install_path, stage_path, and prime_path
#   NOTE: an exclude and include for the same file/dir should match
# * organize should determine if it applies to the a file or a directory and
#   if it is a directory
# Organize
# * organize for filepaths should always be a full file or dir name not a glob
#   Use cases
#   * file -> file - simple string match and replace
#   * file -> dir - dir must end in a '/'
#   * dir -> dir - path component string match and replace
#     i.e. tmp -> newtmp -
#       on ('tmp/tmp2/file1', 'tmp/tmp2/file1', 'tmp/tmp2/file1')
#     results in
#       ('tmp/tmp2/file1', 'newtmp/tmp2/file1', 'newtmp/tmp2/file1')
#   * * -> dir - prepends 'dir' to stage and prime paths.
#   * dir1/dir2/* -> newdir - similar to 'dir -> dir'
#
#
# Fileset
# * adding an exclude of a matching include should remove the filepath
# * adding an include of a matching exclude should remove the filepath
# * adding an include or exclude that matches an existing include or
#   or exclude respectively should be a no-op.
# * compining filesets should perform the same operations as adding each
#   file of the new fileset to the existing fileset.
# * adding a glob should expand the glob and create a filepath for each entry.


class Filepath(object):
    is_exclude = False

    def __init__(self, filepath, **kwargs):

        if filepath[0] == '-':
            self.is_exclude = True
            filepath = filepath[1:]
        if filepath[-1] == os.path.sep:
            filepath = filepath[:-1]
        self.install_file = filepath
        self.stage_file = filepath

        self.install_dir = kwargs.get('install_dir', 'install')
        self.stage_dir = kwargs.get('stage_dir', 'stage')
        self.prime_dir = kwargs.get('prime_dir', 'prime')

    def is_dir(self):
        return os.path.isdir(self.install_path)

    @property
    def install_path(self):
        return os.path.join(self.install_dir, self.install_file)

    @property
    def stage_path(self):
        if self.stage_file:
            return os.path.join(self.stage_dir, self.stage_file)
        else:
            return os.path.join(self.stage_dir, self.install_file)

    @property
    def prime_path(self):
        if self.stage_file:
            return os.path.join(self.prime_dir, self.stage_file)
        else:
            return os.path.join(self.prime_dir, self.install_file)

    def _get_prefixes(self):
        prefixes = []

        path = self.install_file
        prefix, base = os.path.split(path)

        while prefix != '':
            prefixes.append(prefix)
            path = prefix
            prefix, base = os.path.split(path)

        return prefixes

    def organize(self, old, new):
        prefixes = self._get_prefixes()

        if self.install_file == old:
            if new[-1] == '/':
                # explicit directory target
                self.stage_file = os.path.join(new, self.install_file)
            else:
                self.stage_file = new
        elif old in prefixes:
            self.stage_file = self.install_file.replace(old, new)

    def stage(self):
        if not self.is_exclude:
            self.link_or_copy(self.install_path, self.stage_path)

    def prime(self):
        if not self.is_exclude:
            self.link_or_copy(self.stage_path, self.prime_path)

    def link_or_copy(self, src, dst):
        if self.is_dir():
            file_utils.link_or_copy_tree(src, dst)
        else:
            file_utils.link_or_copy(src, dst)

    def __str__(self):
        install_file = self.install_file
        stage_file = self.stage_file
        if self.is_exclude:
            install_file = '-{}'.format(install_file)
            stage_file = '-{}'.format(stage_file)
        return "{}, {}".format(install_file, stage_file)

    def __eq__(self, filepath):
        return (self.install_path == filepath.install_path and
                self.stage_path == filepath.stage_path)


class FilepathOld(object):
    _install_file = ''
    _stage_file = ''
    _prime_file = ''

    def __init__(self, fpath, **kwargs):
        self.is_exclude = False
        self.is_wildcard = False

        self.install_file = fpath
        self.stage_file = kwargs.get('stage_file', self.stage_file)
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
        if fpath[0] == '-':
            self.sources = glob.glob(fpath[1:])
        else:
            self.sources = glob.glob(fpath)

        self.is_exclude = (fpath and fpath[0] == '-')
        path_parts = fpath.split(os.path.sep)
        self.is_wildcard = '*' in path_parts

        if self.is_exclude or self.is_wildcard:
            self.stage_file = ''

        # install file will contain exclude and wildcard symbols
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

    def stage(self):
        if self.is_exclude:
            return

        for source in self.sources:
            source_path = os.path.join(self.install_dir, source)
            # stage_file should either be empty or point to a file/directory
            # if there are more than one source file due to globbing then
            # stage_file must be directory and not a file.
            if self.stage_file:
                if len(self.sources) > 0 or self.stage_file[-1] == os.path.sep:
                    dest_path = os.path.join(
                        self.stage_dir, self.stage_file, source)
                else:
                    dest_path = os.path.join(
                        self.stage_dir, self.stage_file
                    )
            else:
                dest_path = os.path.join(self.stage_dir, source)
            self.link_or_copy(source_path, dest_path)

    def prime(self):
        if self.is_exclude:
            return

        for source in self.sources:
            if self.stage_file:
                if len(self.sources) > 0 or self.stage_file[-1] == os.path.sep:
                    source_path = os.path.join(
                        self.stage_dir, self.stage_file, source)
                else:
                    source_path = os.path.join(
                        self.stage_dir, self.stage_file
                    )

            # stage_file should either be empty or point to a file/directory
            # if there are more than one source file due to globbing then
            # stage_file must be directory and not a file.
            if self.prime_file:
                if len(self.sources) > 0 or self.prime_file[-1] == os.path.sep:
                    dest_path = os.path.join(
                        self.prime_dir, self.prime_file, source)
                else:
                    dest_path = os.path.join(
                        self.prime_dir, self.prime_file
                    )
            else:
                dest_path = os.path.join(self.prime_dir, source)
            self.link_or_copy(source_path, dest_path)

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

    def __eq__(self, filepath):
        return (self.install_path == filepath.install_path and
                self.stage_path == filepath.stage_path and
                self.prime_path == filepath.prime_path)

    def __str__(self):
        return str((self.install_path, self.stage_path, self.prime_path))


class Fileset(object):

    def __init__(self, *args):
        self.files = []
        self.install_dir = 'install'
        self.stage_dir = 'stage'
        self.prime_dir = 'prime'

        for arg in args:
            self.add(arg)

    def add(self, filepath):
        """Add a filepath (str) to the fileset."""

        is_exclude = False
        if filepath[0] == '-':
            is_exclude = True
            filepath = filepath[1:]

        path, base = os.path.split(filepath)
        pattern = ''
        if base == '*':
            pattern = path
        matches = glob.glob(os.path.join(self.install_dir, filepath))
        if not matches:
            raise Exception('No files matched {!r}'.format(filepath))
        for match in matches:
            new_filepath = match.replace('{}{}'.format(
                self.install_dir, os.path.sep, pattern), '')
            if is_exclude:
                new_filepath = '-{}'.format(new_filepath)
            fp = Filepath(new_filepath)
            if fp.is_exclude:
                if fp in self.files:
                    self.files.remove(fp)

            # XXX: need to do deduplication here
            if fp not in self.files:
                self.files.append(fp)

    def replace(self, index, filepath):
        if len(self.files) < index:
            raise Exception("invalid index: {}".format(index))

        self.files[index] = filepath

    def stage(self):
        for filepath in self.files:
            filepath.stage()

    def prime(self):
        for filepath in self.files:
            filepath.prime()

    def organize(self, organize_fs):
        for filepath in self.files:
            for orig, new in organize_fs.items():
                filepath.organize(orig, new)

    @property
    def excludes(self):
        return [x.install_file for x in self.files if x.is_exclude]

    @property
    def includes(self):
        return [x.install_file for x in self.files if x.install_file[0] != '-']

    def __add__(self, fileset):
        # If adding a non-excludes fileset with a wildcard one the
        # resulting fileset should be a wildcard

        files = self.files
        for filepath in fileset.files:
            if filepath not in self.files:
                files.append(filepath)

        fs = Fileset()
        fs.files = files

        return fs

    def __contains__(self, filepath):
        return filepath in self.files

    def __sub__(self, fileset):
        files = [
            fp for fp in self.files if fp not in fileset.files
        ]

        fs = Fileset()
        fs.files = files

        return fs

    def __str__(self):
        return str([str(f) for f in self.files])
