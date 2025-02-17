#! /usr/bin/env python3
""" test cases for bigfile detection """

__copyright__ = "(C) Guido Draheim, all rights reserved"""
__version__ = "1.0.2012"

# pylint: disable=missing-function-docstring,missing-class-docstring,unspecified-encoding,dangerous-default-value,unused-argument,unused-variable,line-too-long,multiple-statements,consider-using-f-string
from typing import Union, Optional, Tuple, List, Dict, Iterator, Iterable, cast

import os
import sys
import re
import subprocess
import zipfile
import inspect
import unittest
from fnmatch import fnmatchcase as fnmatch
import shutil
import random
import logging
#
import git_show_bigfiles as app

logg = logging.getLogger("TESTING")

if sys.version[0] == '2':
    stringtypes = basestring # type: ignore[name-defined] # pylint: disable=undefined-variable # PEP 484
else:
    stringtypes = str # pylint: disable=invalid-name

try:
    from cStringIO import StringIO  # type: ignore[import, attr-defined]
except ImportError:
    from io import StringIO  # Python3


GIT = "git"
BRANCH = "main"
KEEP = False
KB = 1024
MB = KB * KB
MAXSIZE = 50.0

def decodes(text: Union[bytes, str]) -> str:
    if isinstance(text, bytes):
        encoded = sys.getdefaultencoding()
        if encoded in ["ascii"]:
            encoded = "utf-8"
        try:
            return text.decode(encoded)
        except UnicodeDecodeError:
            return text.decode("latin-1")
    return text # also for None
def sh____(cmd: Union[str, List[str]], cwd: Optional[str] = None, shell: bool = True) -> int:
    if isinstance(cmd, stringtypes):
        logg.info(": %s", cmd)
    else:
        logg.info(": %s", " ".join(["'%s'" % item for item in cmd]))
    return subprocess.check_call(cmd, cwd=cwd, shell=shell)
def sx____(cmd: Union[str, List[str]], cwd: Optional[str] = None, shell: bool = True) -> int:
    if isinstance(cmd, stringtypes):
        logg.info(": %s", cmd)
    else:
        logg.info(": %s", " ".join(["'%s'" % item for item in cmd]))
    return subprocess.call(cmd, cwd=cwd, shell=shell)
def output(cmd: Union[str, List[str]], cwd: Optional[str] = None, shell: bool = True, pipe: Optional[str] = None) -> str:
    if isinstance(cmd, stringtypes):
        logg.info(": %s", cmd)
    else:
        logg.info(": %s", " ".join(["'%s'" % item for item in cmd]))
    if pipe is not None:
        run = subprocess.Popen(cmd, cwd=cwd, shell=shell, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
        out, err = run.communicate(pipe.encode("utf-8"))
    else:
        run = subprocess.Popen(cmd, cwd=cwd, shell=shell, stdout=subprocess.PIPE)
        out, err = run.communicate()
    return decodes(out)
def output2(cmd: Union[str, List[str]], cwd: Optional[str] = None, shell: bool = True, pipe: Optional[str] = None) -> Tuple[str, int]:
    if isinstance(cmd, stringtypes):
        logg.info(": %s", cmd)
    else:
        logg.info(": %s", " ".join(["'%s'" % item for item in cmd]))
    if pipe is not None:
        run = subprocess.Popen(cmd, cwd=cwd, shell=shell, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
        out, err = run.communicate(pipe.encode("utf-8"))
    else:
        run = subprocess.Popen(cmd, cwd=cwd, shell=shell, stdout=subprocess.PIPE)
        out, err = run.communicate()
    return decodes(out), run.returncode
def output3(cmd: Union[str, List[str]], cwd: Optional[str] = None, shell: bool = True, pipe: Optional[str] = None) -> Tuple[str, str, int]:
    if isinstance(cmd, stringtypes):
        logg.info(": %s", cmd)
    else:
        logg.info(": %s", " ".join(["'%s'" % item for item in cmd]))
    if pipe is not None:
        run = subprocess.Popen(cmd, cwd=cwd, shell=shell, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, stdin=subprocess.PIPE)
        out, err = run.communicate(pipe.encode("utf-8"))
    else:
        run = subprocess.Popen(cmd, cwd=cwd, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = run.communicate()
    return decodes(out), decodes(err), run.returncode

def gentext(size: int, start: str = "") -> str:
    random.seed(1234567891234567890)
    result = StringIO(start)
    old = ''
    pre = ''
    for i in range(size):
        while True:
            if old in " aeiouy":
                x = random.choice("bcdfghjklmnpqrstvwxz")
                if x == old or x == pre:
                    x = '\n'
            else:
                x = random.choice(" aeiouy")
            pre = old
            old = x
            break
        result.write(x)
    return cast(str, result.getvalue())

def text_file(filename: str, content: str) -> None:
    filedir = os.path.dirname(filename)
    if not os.path.isdir(filedir):
        os.makedirs(filedir)
    with open(filename, "w") as f:
        if content.startswith("\n"):
            x = re.match("(?s)\n( *)", content)
            assert x is not None
            indent = x.group(1)
            for line in content[1:].split("\n"):
                if line.startswith(indent):
                    line = line[len(indent):]
                f.write(line + "\n")
        else:
            f.write(content)
        f.close()

def zip_file(filename: str, content: Dict[str, str]) -> None:
    filedir = os.path.dirname(filename)
    if not os.path.isdir(filedir):
        os.makedirs(filedir)
    with zipfile.ZipFile(filename, "w") as f:
        for name, data in content.items():
            if data.startswith("\n"):
                text = ""
                x = re.match("(?s)\n( *)", data)
                assert x is not None
                indent = x.group(1)
                for line in data[1:].split("\n"):
                    if line.startswith(indent):
                        line = line[len(indent):]
                    text += line + "\n"
                f.writestr(name, text)
            else:
                f.writestr(name, data)

def split2(inp: Iterable[str]) -> Iterator[Tuple[str, str]]:
    for line in inp:
        if " " in line:
            a, b = line.split(" ", 1)
            yield a, b.strip()
def splits2(inp: str) -> Iterator[Tuple[str, str]]:
    for a, b in split2(inp.splitlines()):
        yield a, b

def split3(inp: Iterable[str]) -> Iterator[Tuple[str, str, str]]:
    for line in inp:
        if " " in line:
            a, b, c = line.split(" ", 2)
            yield a, b, c.strip()
def splits3(inp: str) -> Iterator[Tuple[str, str, str]]:
    for a, b, c in split3(inp.splitlines()):
        yield a, b, c

def get_caller_name() -> str:
    frame = inspect.currentframe().f_back.f_back  # type: ignore[union-attr]
    return frame.f_code.co_name  # type: ignore[union-attr]
def get_caller_caller_name() -> str:
    frame = inspect.currentframe().f_back.f_back.f_back  # type: ignore[union-attr]
    return frame.f_code.co_name  # type: ignore[union-attr]

class GitBigfileTest(unittest.TestCase):
    def caller_testname(self) -> str:
        name = get_caller_caller_name()
        x1 = name.find("_")
        if x1 < 0: return name
        x2 = name.find("_", x1 + 1)
        if x2 < 0: return name
        return name[:x2]
    def testname(self, suffix: Optional[str] = None) -> str:
        name = self.caller_testname()
        if suffix:
            return name + "_" + suffix
        return name
    def mk_testdir(self, testname: Optional[str] = None) -> str:
        testname = testname or self.caller_testname()
        newdir = "tmp/tmp." + testname
        if os.path.isdir(newdir):
            shutil.rmtree(newdir)
        os.makedirs(newdir)
        return newdir
    def rm_testdir(self, testname: Optional[str] = None) -> str:
        testname = testname or self.caller_testname()
        newdir = "tmp/tmp." + testname
        if os.path.isdir(newdir):
            shutil.rmtree(newdir)
        return newdir
    def test_101_simple(self) -> None:
        testdir = self.mk_testdir()
        git, main = GIT, BRANCH
        sh____(F"{git} init -b {main} {testdir}")
        text_file(F"{testdir}/a.txt", "A File")
        zip_file(F"{testdir}/b.zip", {"b.txt": "B File"})
        sh____(F"cd {testdir} && {git} add *.*")
        sh____(F"cd {testdir} && {git} --no-pager commit -m 'initial'")
        sh____(F"cd {testdir} && {git} --no-pager show --name-only")
        if not KEEP: self.rm_testdir()
    def test_102_bigfile(self) -> None:
        testdir = self.mk_testdir()
        git, main = GIT, BRANCH
        sh____(F"{git} init -b {main} {testdir}")
        text_file(F"{testdir}/a.txt", gentext(20 * KB))
        zip_file(F"{testdir}/b.zip", {"b.txt": gentext(20 * KB)})
        sh____(F"cd {testdir} && {git} add *.*")
        sh____(F"cd {testdir} && {git} --no-pager commit -m 'initial'")
        sh____(F"cd {testdir} && {git} --no-pager diff --name-only")
        out = output(F"cd {testdir} && {git} rev-list {main} --objects")
        sizes = {}
        for rev, name in splits2(out):
            logg.debug("FOUND %s %s", rev, name)
            if name in ("a.txt", "b.zip"):
                siz = output(F"cd {testdir} && git cat-file -s {rev}")
                sizes[name] = int(siz)
        self.assertEqual(20 * KB, 20480)
        self.assertEqual(sizes["a.txt"], 20480)
        self.assertEqual(sizes["b.zip"], 20588)
        if not KEEP: self.rm_testdir()
    def test_103_bigfile(self) -> None:
        testdir = self.mk_testdir()
        git, main = GIT, BRANCH
        sh____(F"{git} init -b {main} {testdir}")
        text = gentext(20 * KB)
        logg.info("TEXT %s", text)
        text_file(F"{testdir}/a.txt", text)
        zip_file(F"{testdir}/b.zip", {"b.txt": text})
        sh____(F"{git} add *.*", testdir)
        sh____(F"{git} --no-pager commit -m 'initial'", testdir)
        sh____(F"{git} --no-pager diff --name-only", testdir)
        out = output(F"{git} rev-list {main} --objects", testdir)
        revs = {}
        sizes = {}
        types = {}
        for rev, name in splits2(out):
            logg.debug("FOUND %s %s", rev, name)
            if name in ("a.txt", "b.zip"):
                revs[rev] = name
        siz = output(F"{git} cat-file --batch-check='%(objectsize) %(objecttype) %(objectname)'",
                     testdir, pipe="\n".join(revs.keys()))
        for siz, typ, rev in splits3(siz):
            name = revs[rev]
            sizes[name] = int(siz)
            types[name] = typ
        self.assertEqual(20 * KB, 20480)
        self.assertEqual(sizes["a.txt"], 20480)
        self.assertEqual(sizes["b.zip"], 20588)
        self.assertEqual(types["a.txt"], "blob")
        self.assertEqual(types["b.zip"], "blob")
        if not KEEP: self.rm_testdir()
    def test_202_bigfile(self) -> None:
        testdir = self.mk_testdir()
        git, main = GIT, BRANCH
        sh____(F"{git} init -b {main} {testdir}")
        text_file(F"{testdir}/a.txt", gentext(20 * KB))
        zip_file(F"{testdir}/b.zip", {"b.txt": gentext(20 * KB)})
        sh____(F"cd {testdir} && {git} add *.*")
        sh____(F"cd {testdir} && {git} --no-pager commit -m 'initial'")
        sh____(F"cd {testdir} && {git} --no-pager diff --name-only")
        app.REPO = testdir
        app.MAXSIZE = MAXSIZE
        sizes = list(app.each_size5())
        self.assertEqual(20 * KB, 20480)
        self.assertEqual(sizes[1].name, "a.txt")
        self.assertEqual(sizes[2].name, "b.zip")
        self.assertEqual(sizes[1].filesize, 20480)
        self.assertEqual(sizes[2].filesize, 20588)
        if not KEEP: self.rm_testdir()
    def test_203_bigfile(self) -> None:
        testdir = self.mk_testdir()
        git, main = GIT, BRANCH
        sh____(F"{git} init -b {main} {testdir}")
        text = gentext(20 * KB)
        logg.info("TEXT %s", text)
        text_file(F"{testdir}/a.txt", text)
        zip_file(F"{testdir}/b.zip", {"b.txt": text})
        sh____(F"{git} add *.*", testdir)
        sh____(F"{git} --no-pager commit -m 'initial'", testdir)
        sh____(F"{git} --no-pager diff --name-only", testdir)
        app.REPO = testdir
        app.MAXSIZE = MAXSIZE
        sizes = list(app.each_size5())
        self.assertEqual(len(sizes), 3)
        self.assertEqual(20 * KB, 20480)
        self.assertEqual(sizes[1].name, "a.txt")
        self.assertEqual(sizes[2].name, "b.zip")
        self.assertEqual(sizes[1].filesize, 20480)
        self.assertEqual(sizes[2].filesize, 20588)
        if not KEEP: self.rm_testdir()
    def test_213_bigfile(self) -> None:
        testdir = self.mk_testdir()
        git, main = GIT, BRANCH
        sh____(F"{git} init -b {main} {testdir}")
        text = gentext(20 * KB)
        logg.info("TEXT %s", text)
        text_file(F"{testdir}/a.txt", text)
        zip_file(F"{testdir}/b.zip", {"b.txt": text})
        sh____(F"{git} add *.*", testdir)
        sh____(F"{git} --no-pager commit -m 'initial'", testdir)
        sh____(F"{git} --no-pager diff --name-only", testdir)
        text_file(F"{testdir}/a.txt", gentext(5 * KB))
        sh____(F"{git} --no-pager commit -m 'update' a.txt", testdir)
        app.REPO = testdir
        app.MAXSIZE = MAXSIZE
        sizes = list(app.each_size5())
        for n, elem in enumerate(sizes):
            logg.info("sizes[%i] = %s", n, elem)
        self.assertEqual(len(sizes), 5)
        self.assertEqual(20 * KB, 20480)
        self.assertEqual(sizes[1].name, "a.txt")
        self.assertEqual(sizes[2].name, "b.zip")
        self.assertEqual(sizes[4].name, "a.txt")
        self.assertEqual(sizes[1].filesize, 5120)
        self.assertEqual(sizes[2].filesize, 20588)
        self.assertEqual(sizes[4].filesize, 20480)
        if not KEEP: self.rm_testdir()
    def test_233_bigfile(self) -> None:
        testdir = self.mk_testdir()
        git, main = GIT, BRANCH
        sh____(F"{git} init -b {main} {testdir}")
        text5 = gentext(5 * KB)
        text20 = gentext(20 * KB)
        logg.info("TEXT %s", text20)
        text_file(F"{testdir}/a.txt", text20)
        zip_file(F"{testdir}/b.zip", {"b.txt": text20})
        sh____(F"{git} add *.*", testdir)
        sh____(F"{git} --no-pager commit -m 'initial'", testdir)
        sh____(F"{git} --no-pager diff --name-only", testdir)
        text_file(F"{testdir}/a.txt", text5)
        sh____(F"{git} --no-pager commit -m 'update' a.txt", testdir)
        app.REPO = testdir
        app.MAXSIZE = 0.001
        self.assertEqual(int(app.MAXSIZE * app.MB), 1048)
        sizes = list(app.each_oversize5())
        for n, elem in enumerate(sizes):
            logg.info("sizes[%i] = %s", n, elem)
        self.assertEqual(len(sizes), 3)  # only 'blob' - as 'tree' objects are small
        self.assertEqual(20 * KB, 20480)
        self.assertEqual(sizes[0].name, "a.txt")
        self.assertEqual(sizes[1].name, "b.zip")
        self.assertEqual(sizes[2].name, "a.txt")
        self.assertEqual(sizes[0].filesize, 5120)
        self.assertEqual(sizes[1].filesize, 20588)
        self.assertEqual(sizes[2].filesize, 20480)
        if not KEEP: self.rm_testdir()
    def test_234_bigfile(self) -> None:
        testdir = self.mk_testdir()
        git, main = GIT, BRANCH
        sh____(F"{git} init -b {main} {testdir}")
        text5 = gentext(5 * KB)
        text20 = gentext(20 * KB)
        logg.info("TEXT %s", text20)
        text_file(F"{testdir}/a.txt", text20)
        zip_file(F"{testdir}/b.zip", {"b.txt": text20})
        sh____(F"{git} add *.*", testdir)
        sh____(F"{git} --no-pager commit -m 'initial'", testdir)
        sh____(F"{git} --no-pager diff --name-only", testdir)
        text_file(F"{testdir}/a.txt", text5)
        sh____(F"{git} --no-pager commit -m 'update' a.txt", testdir)
        app.REPO = testdir
        app.MAXSIZE = 0.011
        self.assertEqual(int(app.MAXSIZE * app.MB), 11534)
        sizes = list(app.each_oversize5())
        for n, elem in enumerate(sizes):
            logg.info("sizes[%i] = %s", n, elem)
        self.assertEqual(len(sizes), 2)  # not the 5 KB file anymore
        self.assertEqual(20 * KB, 20480)
        self.assertEqual(sizes[0].name, "b.zip")
        self.assertEqual(sizes[1].name, "a.txt")
        self.assertEqual(sizes[0].filesize, 20588)
        self.assertEqual(sizes[1].filesize, 20480)
        if not KEEP: self.rm_testdir()
    def test_313_bigfile(self) -> None:
        testdir = self.mk_testdir()
        git, main = GIT, BRANCH
        sh____(F"{git} init -b {main} {testdir}")
        text = gentext(20 * KB)
        logg.info("TEXT %s", text)
        text_file(F"{testdir}/a.txt", text)
        zip_file(F"{testdir}/b.zip", {"b.txt": text})
        sh____(F"{git} add *.*", testdir)
        sh____(F"{git} --no-pager commit -m 'initial'", testdir)
        sh____(F"{git} --no-pager diff --name-only", testdir)
        text_file(F"{testdir}/a.txt", gentext(5 * KB))
        sh____(F"{git} --no-pager commit -m 'update' a.txt", testdir)
        app.REPO = testdir
        app.MAXSIZE = MAXSIZE
        sizes = list(app.each_sumsize5())
        self.assertEqual(len(sizes), 2)
        self.assertEqual(20 * KB, 20480)
        self.assertEqual(sizes[0].name, "a.txt")
        self.assertEqual(sizes[1].name, "b.zip")
        self.assertEqual(sizes[0].filesum, 5120 + 20480)
        self.assertEqual(sizes[1].filesum, 20588)
        if not KEEP: self.rm_testdir()
    def test_333_bigfile(self) -> None:
        testdir = self.mk_testdir()
        git, main = GIT, BRANCH
        sh____(F"{git} init -b {main} {testdir}")
        text = gentext(20 * KB)
        logg.info("TEXT %s", text)
        text_file(F"{testdir}/a.txt", text)
        zip_file(F"{testdir}/b.zip", {"b.txt": text})
        sh____(F"{git} add *.*", testdir)
        sh____(F"{git} --no-pager commit -m 'initial'", testdir)
        sh____(F"{git} --no-pager diff --name-only", testdir)
        text_file(F"{testdir}/a.txt", gentext(5 * KB))
        sh____(F"{git} --no-pager commit -m 'update' a.txt", testdir)
        app.REPO = testdir
        app.MAXSIZE = 0.001
        sizes = list(app.each_sumoversize5())
        self.assertEqual(len(sizes), 2)
        self.assertEqual(20 * KB, 20480)
        self.assertEqual(sizes[0].name, "a.txt")
        self.assertEqual(sizes[1].name, "b.zip")
        self.assertEqual(sizes[0].filesum, 5120 + 20480)
        self.assertEqual(sizes[1].filesum, 20588)
        if not KEEP: self.rm_testdir()
    def test_334_bigfile(self) -> None:
        testdir = self.mk_testdir()
        git, main = GIT, BRANCH
        sh____(F"{git} init -b {main} {testdir}")
        text = gentext(20 * KB)
        logg.info("TEXT %s", text)
        text_file(F"{testdir}/a.txt", text)
        zip_file(F"{testdir}/b.zip", {"b.txt": text})
        sh____(F"{git} add *.*", testdir)
        sh____(F"{git} --no-pager commit -m 'initial'", testdir)
        sh____(F"{git} --no-pager diff --name-only", testdir)
        text_file(F"{testdir}/a.txt", gentext(5 * KB))
        sh____(F"{git} --no-pager commit -m 'update' a.txt", testdir)
        app.REPO = testdir
        app.MAXSIZE = 0.011
        self.assertEqual(int(app.MAXSIZE * app.MB), 11534)
        sizes = list(app.each_sumoversize5())
        self.assertEqual(len(sizes), 2)
        self.assertEqual(20 * KB, 20480)
        self.assertEqual(sizes[0].name, "b.zip")
        self.assertEqual(sizes[1].name, "a.txt")
        self.assertEqual(sizes[0].filesum, 20588)
        self.assertEqual(sizes[1].filesum, 20480) # without 5 KB
        if not KEEP: self.rm_testdir()
    def test_413_bigfile(self) -> None:
        testdir = self.mk_testdir()
        git, main = GIT, BRANCH
        sh____(F"{git} init -b {main} {testdir}")
        text = gentext(20 * KB)
        logg.info("TEXT %s", text)
        text_file(F"{testdir}/a.txt", text)
        zip_file(F"{testdir}/b.zip", {"b.txt": text})
        sh____(F"{git} add *.*", testdir)
        sh____(F"{git} --no-pager commit -m 'initial'", testdir)
        sh____(F"{git} --no-pager diff --name-only", testdir)
        text_file(F"{testdir}/a.txt", gentext(5 * KB))
        sh____(F"{git} --no-pager commit -m 'update' a.txt", testdir)
        app.REPO = testdir
        app.MAXSIZE = MAXSIZE
        sizes = list(app.each_extsize5())
        logg.info("sizes %s", sizes)
        self.assertEqual(len(sizes), 2)
        self.assertEqual(20 * KB, 20480)
        self.assertEqual(sizes[0].ext, ".txt")
        self.assertEqual(sizes[1].ext, ".zip")
        self.assertEqual(sizes[0].filesum, 5120 + 20480)
        self.assertEqual(sizes[1].filesum, 20588)
        if not KEEP: self.rm_testdir()
    def test_415_bigfile(self) -> None:
        testdir = self.mk_testdir()
        git, main = GIT, BRANCH
        sh____(F"{git} init -b {main} {testdir}")
        text = gentext(20 * KB)
        logg.info("TEXT %s", text)
        text_file(F"{testdir}/a.txt", text)
        zip_file(F"{testdir}/b.zip", {"b.txt": text})
        sh____(F"{git} add *.*", testdir)
        sh____(F"{git} --no-pager commit -m 'initial'", testdir)
        sh____(F"{git} --no-pager diff --name-only", testdir)
        text_file(F"{testdir}/a.txt", gentext(5 * KB))
        sh____(F"{git} --no-pager commit -m 'update' a.txt", testdir)
        text_file(F"{testdir}/dummyfile", gentext(8 * KB))
        sh____(F"{git} add dummyfile", testdir)
        sh____(F"{git} --no-pager commit -m 'dummy'", testdir)
        app.REPO = testdir
        app.MAXSIZE = MAXSIZE
        sizes = list(app.each_extsize5())
        logg.info("sizes %s", sizes)
        self.assertEqual(len(sizes), 3)
        self.assertEqual(20 * KB, 20480)
        self.assertEqual(sizes[0].ext, ".txt")
        self.assertEqual(sizes[1].ext, ".zip")
        self.assertEqual(sizes[2].ext, "")
        self.assertEqual(sizes[0].filesum, 5120 + 20480)
        self.assertEqual(sizes[1].filesum, 20588)
        self.assertEqual(sizes[2].filesum, 8192)
        if not KEEP: self.rm_testdir()
    def test_433_bigfile(self) -> None:
        testdir = self.mk_testdir()
        git, main = GIT, BRANCH
        sh____(F"{git} init -b {main} {testdir}")
        text = gentext(20 * KB)
        logg.info("TEXT %s", text)
        text_file(F"{testdir}/a.txt", text)
        zip_file(F"{testdir}/b.zip", {"b.txt": text})
        sh____(F"{git} add *.*", testdir)
        sh____(F"{git} --no-pager commit -m 'initial'", testdir)
        sh____(F"{git} --no-pager diff --name-only", testdir)
        text_file(F"{testdir}/a.txt", gentext(5 * KB))
        sh____(F"{git} --no-pager commit -m 'update' a.txt", testdir)
        app.REPO = testdir
        app.MAXSIZE = 0.001
        sizes = list(app.each_extoversize5())
        logg.info("sizes %s", sizes)
        self.assertEqual(len(sizes), 2)
        self.assertEqual(20 * KB, 20480)
        self.assertEqual(sizes[0].ext, ".txt")
        self.assertEqual(sizes[1].ext, ".zip")
        self.assertEqual(sizes[0].filesum, 5120 + 20480)
        self.assertEqual(sizes[1].filesum, 20588)
        if not KEEP: self.rm_testdir()
    def test_434_bigfile(self) -> None:
        testdir = self.mk_testdir()
        git, main = GIT, BRANCH
        sh____(F"{git} init -b {main} {testdir}")
        text = gentext(20 * KB)
        logg.info("TEXT %s", text)
        text_file(F"{testdir}/a.txt", text)
        zip_file(F"{testdir}/b.zip", {"b.txt": text})
        sh____(F"{git} add *.*", testdir)
        sh____(F"{git} --no-pager commit -m 'initial'", testdir)
        sh____(F"{git} --no-pager diff --name-only", testdir)
        text_file(F"{testdir}/a.txt", gentext(5 * KB))
        sh____(F"{git} --no-pager commit -m 'update' a.txt", testdir)
        app.REPO = testdir
        app.MAXSIZE = 0.011
        self.assertEqual(int(app.MAXSIZE * app.MB), 11534)
        sizes = list(app.each_extoversize5())
        logg.info("sizes %s", sizes)
        self.assertEqual(len(sizes), 2)
        self.assertEqual(20 * KB, 20480)
        self.assertEqual(sizes[0].ext, ".zip")
        self.assertEqual(sizes[1].ext, ".txt")
        self.assertEqual(sizes[0].filesum, 20588)
        self.assertEqual(sizes[1].filesum, 20480) # without 5KB
        if not KEEP: self.rm_testdir()
    def test_515_bigfile(self) -> None:
        testdir = self.mk_testdir()
        git, main = GIT, BRANCH
        sh____(F"{git} init -b {main} {testdir}")
        text = gentext(20 * KB)
        logg.info("TEXT %s", text)
        text_file(F"{testdir}/a.txt", text)
        zip_file(F"{testdir}/b.zip", {"b.txt": text})
        sh____(F"{git} add *.*", testdir)
        sh____(F"{git} --no-pager commit -m 'initial'", testdir)
        sh____(F"{git} --no-pager diff --name-only", testdir)
        text_file(F"{testdir}/a.txt", gentext(5 * KB))
        sh____(F"{git} --no-pager commit -m 'update' a.txt", testdir)
        text_file(F"{testdir}/dummyfile", gentext(8 * KB))
        sh____(F"{git} add dummyfile", testdir)
        sh____(F"{git} --no-pager commit -m 'dummy'", testdir)
        app.REPO = testdir
        app.MAXSIZE = MAXSIZE
        sizes = list(app.each_noext1())
        logg.info("sizes %s", sizes)
        self.assertEqual(len(sizes), 1)
        self.assertEqual(sizes[0].ext, "dummyfile")
        if not KEEP: self.rm_testdir()

if __name__ == "__main__":
    from optparse import OptionParser # pylint: disable=deprecated-module
    cmdline = OptionParser("%prog [options] test*",
                      epilog=__doc__.strip().split("\n", 1)[0])
    cmdline.formatter.max_help_position = 28
    cmdline.add_option("-v", "--verbose", action="count", default=0,
                      help="increase logging level [%default]")
    cmdline.add_option("-g", "--git", metavar="EXE", default=GIT,
                      help="use different git client [%default]")
    cmdline.add_option("-b", "--branch", metavar="NAME", default=BRANCH,
                      help="use different def branch [%default]")
    cmdline.add_option("-k", "--keep", action="count", default=0,
                      help="keep docker build container [%default]")
    cmdline.add_option("-l", "--logfile", metavar="FILE", default="",
                      help="additionally save the output log to a file [%default]")
    cmdline.add_option("--failfast", action="store_true", default=False,
                      help="Stop the test run on the first error or failure. [%default]")
    cmdline.add_option("--xmlresults", metavar="FILE", default=None,
                      help="capture results as a junit xml file [%default]")
    opt, cmdline_args = cmdline.parse_args()
    logging.basicConfig(level=logging.WARNING - opt.verbose * 5)
    #
    KEEP = opt.keep
    GIT = opt.git
    BRANCH = opt.branch
    #
    LOGFILE = None
    if opt.logfile:
        if os.path.exists(opt.logfile):
            os.remove(opt.logfile)
        LOGFILE = logging.FileHandler(opt.logfile)
        LOGFILE.setFormatter(logging.Formatter("%(levelname)s:%(relativeCreated)d:%(message)s"))
        logging.getLogger().addHandler(LOGFILE)
        logg.info("log diverted to %s", opt.logfile)
    #
    # unittest.main()
    suite = unittest.TestSuite()
    if not cmdline_args: cmdline_args = ["test_*"]
    for arg in cmdline_args:
        for classname in sorted(globals()):
            if not classname.endswith("Test"):
                continue
            testclass = globals()[classname]
            for method in sorted(dir(testclass)):
                if "*" not in arg: arg += "*"
                if len(arg) > 2 and arg[1] == "_":
                    arg = "test" + arg[1:]
                if fnmatch(method, arg):
                    suite.addTest(testclass(method))
    # select runner
    XMLFILE = None
    if opt.xmlresults:
        if os.path.exists(opt.xmlresults):
            os.remove(opt.xmlresults)
        XMLFILE = open(opt.xmlresults, "wb")  # type: ignore[assignment]
        logg.info("xml results into %s", opt.xmlresults)
    if XMLFILE:
        import xmlrunner  # type: ignore # pylint: disable=import-error
        Runner = xmlrunner.XMLTestRunner
        RESULT = Runner(XMLFILE).run(suite)
    else:
        Runner = unittest.TextTestRunner
        RESULT = Runner(verbosity=opt.verbose, failfast=opt.failfast).run(suite)
    if not RESULT.wasSuccessful():
        sys.exit(1)
