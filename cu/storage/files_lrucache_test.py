#
# This file is part of the celery-utils (https://github.com/e.sovetkin/celery-utils).
# Copyright (c) 2022 Jenya Sovetkin.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#


import re
import os
import shutil

from .files_lrucache import Files_LRUCache


def touch(fname, times=None, size = 1024):
    with open(fname, 'wb') as f:
        f.seek(size - 1)
        f.write(b'\0')


def list_files(path, regex = r'.*'):
    regex = re.compile(regex)
    res = []
    for dp, dn, filenames in os.walk(path):
        for f in filenames:
            fn = os.path.join(dp,f)
            if regex.match(fn):
                res += [fn]

    return res


def test_Files_LRUCache(N = 10):
    path="test_Files_LRUCache"
    try:
        os.makedirs(path, exist_ok = True)
        cache = Files_LRUCache(maxsize = (N*1024)/(1024**3), path = path)

        for i in range(2*N):
            p = os.path.join(path, str(i) + "_test_file")
            touch(p)
            cache.add(p)

        assert N == len(cache)
        assert N*1024 == cache.size()
        assert N == len(list_files(path, regex=r'.*_test_file'))
    finally:
        shutil.rmtree(path)


def test_Files_LRUCache_smaller_cache():
    path="test_Files_LRUCache_smaller_cache"
    try:
        os.makedirs(path, exist_ok = True)
        cache = Files_LRUCache(maxsize = 1024/(1024**3), path = path)

        p = os.path.join(path, str(0) + "_test_file")
        cache.add(p)
        assert 0 == cache.size()
        assert 1 == len(cache)

        touch(p)
        assert True == (p in cache)
        assert 1024 == cache.size()

        p = os.path.join(path, str(1) + "_test_file")
        cache.add(p)
        assert 0 == cache.size()
        assert 1 == len(cache)

        touch(p, size = 2048)
        assert True == (p in cache)
        assert 2048 == cache.size()
    finally:
        shutil.rmtree(path)


def test_Files_LRUCache_removed_files():
    path="test_Files_LRUCache_removed_files"
    try:
        os.makedirs(path, exist_ok = True)
        cache = Files_LRUCache(maxsize = 1024/(1024**3), path = path)

        p = os.path.join(path, str(0) + "_test_file")
        touch(p)
        cache.add(p)

        assert 1024 == cache.size()
        assert 1 == len(cache)

        os.remove(p)
        assert False == (p in cache)
        assert 0 == cache.size()
        assert 0 == len(cache)

        touch(p)
        cache.add(p)
        assert 1024 == cache.size()
        assert 1 == len(cache)

        os.remove(p)
        cache.check_content()
        assert 0 == cache.size()
        assert 0 == len(cache)
    finally:
        shutil.rmtree(path)


def test_Files_LRUCache_contains():
    path="test_Files_LRUCache_contains"
    try:
        os.makedirs(path, exist_ok = True)
        cache = Files_LRUCache(maxsize = (2*1024)/(1024**3), path = path)

        a = os.path.join(path, "a")
        touch(a)
        cache.add(a)

        b = os.path.join(path, "b")
        touch(b)
        cache.add(b)

        # here "one" is the first to evict
        assert False == (a not in cache)

        # after checking if "one" was there it should be "two"
        assert b == cache.popleft()
    finally:
        shutil.rmtree(path)


def test_Files_LRUCache_changed_inode():
    path="test_Files_LRUCache_changed_inode"
    try:
        os.makedirs(path, exist_ok = True)
        cache = Files_LRUCache(maxsize = 2*1024/(1024**3), path = path)

        p = os.path.join(path, str(0) + "_test_file")
        touch(p)
        cache.add(p)

        assert 1024 == cache.size()
        assert 1 == len(cache)

        p1 = os.path.join(path, str(1) + "_test_file")
        touch(p1, size=2048)
        os.replace(p1, p)

        assert 1024 == cache.size()
        assert 1 == len(cache)
        assert True == (p in cache)
        assert 2048 == cache.size()
        assert 1 == len(cache)
    finally:
        shutil.rmtree(path)


def test_Files_LRUCache_hardlinks():
    path="test_Files_LRUCache_hardlinks"
    try:
        os.makedirs(path, exist_ok = True)
        cache = Files_LRUCache(maxsize = 2*1024/(1024**3), path = path)

        p = os.path.join(path, str(0) + "_test_file")
        touch(p)
        cache.add(p)

        assert 1024 == cache.size()
        assert 1 == len(cache)

        pl = os.path.join(path, str(1) + "_test_file")
        os.link(p, pl)
        cache.add(pl)

        assert 1024 == cache.size()
        assert 2 == len(cache)
    finally:
        shutil.rmtree(path)


def test_Files_LRUCache_hardlinks_little_space():
    path="test_Files_LRUCache_hardlinks_little_space"
    try:
        os.makedirs(path, exist_ok = True)
        cache = Files_LRUCache(maxsize = 1*1024/(1024**3), path = path)

        p = os.path.join(path, str(0) + "_test_file")
        touch(p)
        cache.add(p)

        assert 1024 == cache.size()
        assert 1 == len(cache)

        pl = os.path.join(path, str(1) + "_test_file")
        os.link(p, pl)
        cache.add(pl)

        assert 1024 == cache.size()
        assert 1 == len(cache)
    finally:
        shutil.rmtree(path)


def test_Files_LRUCache_hardlinks_changing_size(N=100):
    path="test_Files_LRUCache_hardlinks_changing_size"
    try:
        os.makedirs(path, exist_ok = True)
        cache = Files_LRUCache(maxsize = 2*1024/(1024**3), path = path)

        p = os.path.join(path, str(0) + "_test_file")
        touch(p)
        cache.add(p)

        for i in range(1,N):
            pl = os.path.join(path, str(i) + "_test_file")
            os.link(p, pl)
            cache.add(pl)

        assert 1024 == cache.size()
        assert N == len(cache)

        touch(p, size=2048)
        # as cache not updated
        assert 1024 == cache.size()
        assert N == len(cache)

        # the following updates the cache
        assert True == (p in cache)
        assert 2048 == cache.size()
        assert N == len(cache)
    finally:
        shutil.rmtree(path)


def test_Files_LRUCache_large_number_of_files(N=100):
    path="test_Files_LRUCache_large_number_of_files"
    try:
        os.makedirs(path, exist_ok = True)
        cache = Files_LRUCache(maxsize = (2*N*1024)/(1024**3), path = path)

        for i in range(N):
            p = os.path.join(path, str(i) + "_test_file")
            touch(p, size = 1024)
            cache.add(p)

        assert N == len(cache)
        assert N*1024 == cache.size()
    finally:
        shutil.rmtree(path)
