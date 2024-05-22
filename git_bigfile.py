#! /usr/bin/env python3
""" git bigfile detection """

__copyright__ = "(C) Guido Draheim, all rights reserved"""
__version__ = "0.1.0"

from typing import Union, Optional, Tuple, List, Dict, Iterator, Iterable, cast

import os, sys
import os.path as fs
import re
import subprocess
import zipfile
import unittest
from collections import OrderedDict
from fnmatch import fnmatchcase as fnmatch
import logging
logg = logging.getLogger("CHECK")

if sys.version[0] == '3':
    basestring = str
    xrange = range

try:
    from cStringIO import StringIO  # type: ignore[import, attr-defined]
except ImportError:
    from io import StringIO  # Python3

REPO: Optional[str] = None
GIT = "git"
BRANCH = "main"
KEEP = False
KB = 1024
MB = KB * KB

def decodes(text: Union[bytes, str]) -> str:
    if text is None: return None
    if isinstance(text, bytes):
        encoded = sys.getdefaultencoding()
        if encoded in ["ascii"]:
            encoded = "utf-8"
        try:
            return text.decode(encoded)
        except:
            return text.decode("latin-1")
    return text
def output(cmd: Union[str, List[str]], cwd: Optional[str] = None, shell: bool = True, input: Optional[str] = None) -> str:
    if isinstance(cmd, basestring):
        logg.info(": %s", cmd)
    else:
        logg.info(": %s", " ".join(["'%s'" % item for item in cmd]))
    if input is not None:
        run = subprocess.Popen(cmd, cwd=cwd, shell=shell, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
        out, err = run.communicate(input.encode("utf-8"))
    else:
        run = subprocess.Popen(cmd, cwd=cwd, shell=shell, stdout=subprocess.PIPE)
        out, err = run.communicate()
    return decodes(out)
def output2(cmd: Union[str, List[str]], cwd: Optional[str] = None, shell: bool = True, input: Optional[str] = None) -> Tuple[str, int]:
    if isinstance(cmd, basestring):
        logg.info(": %s", cmd)
    else:
        logg.info(": %s", " ".join(["'%s'" % item for item in cmd]))
    if input is not None:
        run = subprocess.Popen(cmd, cwd=cwd, shell=shell, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
        out, err = run.communicate(input.encode("utf-8"))
    else:
        run = subprocess.Popen(cmd, cwd=cwd, shell=shell, stdout=subprocess.PIPE)
        out, err = run.communicate()
    return decodes(out), run.returncode
def output3(cmd: Union[str, List[str]], cwd: Optional[str] = None, shell: bool = True, input: Optional[str] = None) -> Tuple[str, str, int]:
    if isinstance(cmd, basestring):
        logg.info(": %s", cmd)
    else:
        logg.info(": %s", " ".join(["'%s'" % item for item in cmd]))
    if input is not None:
        run = subprocess.Popen(cmd, cwd=cwd, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
        out, err = run.communicate(input.encode("utf-8"))
    else:
        run = subprocess.Popen(cmd, cwd=cwd, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = run.communicate()
    return decodes(out), decodes(err), run.returncode

def split2(inp: Iterable[str]) -> Iterator[Tuple[str, str]]:
    for line in inp:
        if " " in line:
            a, b = line.split(" ", 1)
            yield a, b.strip()
def splits2(inp: str) ->  Iterator[Tuple[str, str]]:
    for a, b in split2(inp.splitlines()):
        yield a, b

def split3(inp: Iterable[str]) -> Iterator[Tuple[str, str, str]]:
    for line in inp:
        if " " in line:
            a, b, c = line.split(" ", 2)
            yield a, b, c.strip()
def splits3(inp: str) ->  Iterator[Tuple[str, str, str]]:
    for a, b, c in split3(inp.splitlines()):
        yield a, b, c
def split4(inp: Iterable[str]) -> Iterator[Tuple[str, str, str]]:
    for line in inp:
        if " " in line:
            a, b, c, d = line.split(" ", 3)
            yield a, b, c, d.strip()
def splits4(inp: str) ->  Iterator[Tuple[str, str, str]]:
    for a, b, c, d in split4(inp.splitlines()):
        yield a, b, c, d

def get_rev_list() -> str:
    return "\n".join(" ".join([str(elem) for elem in item]) for item in each_sizes())
def get_sizes() -> str:
    return "\n".join(" ".join([str(elem) for elem in item]) for item in each_sizes())
def each_sizes() -> Iterator[Tuple[str, str, int, int, str]]:
    git, main = GIT, BRANCH
    out = output(F"{git} rev-list {main} --objects", REPO)
    revs = OrderedDict()
    disks = {}
    sizes = {}
    types = {}
    for rev, name in splits2(out):
         logg.debug("FOUND %s %s", rev, name)
         revs[rev] = name
    objectnames="\n".join(revs.keys()) + "\n"
    logg.debug("objectnames => %s", objectnames)
    siz = output(F"{git} cat-file --batch-check='%(objectsize) %(objectsize:disk) %(objecttype) %(objectname)'",
                 REPO, input=objectnames)
    logg.debug("cat-file => %s", siz)
    for siz, disk, typ, rev in splits4(siz):
         disks[rev] = int(disk)
         sizes[rev] = int(siz)
         types[rev] = typ
    for rev in revs:
         name = revs[rev]
         disk = disks[rev]
         size = sizes[rev]
         type = types[rev]
         yield rev, type, disk, size, name

def get_sumsizes() -> str:
    sumsizes = sorted(list(each_sumsizes4()), key=lambda x: x[0])
    return "\n".join(" ".join([str(elem) for elem in item]) for item in sumsizes)
def each_sumsizes4() -> Iterator[Tuple[int, int, str]]:
    for sum, disk, changes, name, parts in each_sumsizes5():
        yield sum, disk, changes, name
def each_sumsizes5() -> Iterator[Tuple[int, int, str, str]]:
    disksums: Dict[str, int] = {}
    filesums: Dict[str, int] = {}
    dchanges: Dict[str, List[int]] = {}
    for rev, type, disk, size, name in each_sizes():
        if not name: continue
        if name not in filesums:
             disksums[name] = 0
             filesums[name] = 0
             dchanges[name] = []
        filesums[name] += size
        disksums[name] += disk
        dchanges[name] += [ disk ]
    for name, disksum in disksums.items():
        yield disksum, filesums[name], len(dchanges[name]), name, "|" + "+".join([str(item) for item in dchanges[name]])

def get_extsizes() -> str:
    sumsizes = sorted(list(each_extsizes4()), key=lambda x: x[0])
    return "\n".join(" ".join([str(elem) for elem in item]) for item in sumsizes)
def each_extsizes4() -> Iterator[Tuple[int, int, str]]:
    for sum, disk, changes, ext, names in each_extsizes5():
        yield sum, disk, changes, ext
def each_extsizes5() -> Iterator[Tuple[int, int, int, str]]:
    disksums: Dict[str, int] = {}
    filesums: Dict[str, int] = {}
    dchanges: Dict[str, Dict[str, int]] = {}
    for disksum, filesum, changes, name, diskchanges in each_sumsizes5():
        if not name: continue
        filename = fs.basename(name)
        nam, ext = fs.splitext(filename)
        if ext not in filesums:
             disksums[ext] = 0
             filesums[ext] = 0
             dchanges[ext] = {}
        if filename not in dchanges[ext]:
             dchanges[ext][name] = []
        filesums[ext] += filesum
        disksums[ext] += disksum
        dchanges[ext][name] += [ disksum ]
    for ext, disksum in disksums.items():
        yield disksum, filesums[ext], len(dchanges[ext]), ext, "|" + "|".join(dchanges[ext])

def get_help():
    return __doc__


if __name__ == "__main__":
    from optparse import OptionParser
    _o = OptionParser("%prog [options] test*",
                      epilog=__doc__.strip().split("\n")[0])
    _o.add_option("-v", "--verbose", action="count", default=0,
                  help="increase logging level [%default]")
    _o.add_option("-g", "--git", metavar="EXE", default=GIT,
                  help="use different git client [%default]")
    _o.add_option("-b", "--branch", metavar="NAME", default=BRANCH,
                  help="use different def branch [%default]")
    _o.add_option("-r", "--repo", metavar="PATH", default=REPO,
                  help="use different repo path [%default]")
    _o.add_option("-l", "--logfile", metavar="FILE", default="",
                  help="additionally save the output log to a file [%default]")
    opt, args = _o.parse_args()
    logging.basicConfig(level=logging.WARNING - opt.verbose * 5)
    #
    GIT = opt.git
    BRANCH = opt.branch
    REPO = opt.repo or None
    logg.debug("BRANCH %s REPO %s", BRANCH, REPO)
    #
    logfile = None
    if opt.logfile:
        if os.path.exists(opt.logfile):
            os.remove(opt.logfile)
        logfile = logging.FileHandler(opt.logfile)
        logfile.setFormatter(logging.Formatter("%(levelname)s:%(relativeCreated)d:%(message)s"))
        logging.getLogger().addHandler(logfile)
        logg.info("log diverted to %s", opt.logfile)
    #
    logg.debug("args %s", args)
    for arg in args:
        name = arg.replace("-", "_")
        for method in sorted(globals()):
            if "_" not in method or method.startswith("_") or method.endswith("_"):
                continue
            logg.debug("method %s", method)
            methodcall = globals()[method]
            if not callable(methodcall):
                continue
            if fnmatch(method, F"run_{name}"):
                methodcall()
            elif fnmatch(method, F"get_{name}"):
                print(methodcall())


