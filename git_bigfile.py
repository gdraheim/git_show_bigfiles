#! /usr/bin/env python3
""" git bigfile detection """

__copyright__ = "(C) Guido Draheim, all rights reserved"""
__version__ = "0.1.0"

from typing import Union, Optional, Tuple, List, Dict, Iterator, Iterable, Any, cast

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
PRETTY = False
KEEP = False
EXT = ""
KB = 1024
MB = KB * KB

def str_(obj: Any, no: str = '-') -> str:
    if not obj:
        return no
    if isinstance(obj, int) and PRETTY:
       text = str(obj)
       if len(text) > 9:
          return text[:-9] + "_" + text[-9:-6] + "_" + text[-6:-3] + "_" + text[-3:]
       if len(text) > 6:
          return text[:-6] + "_" + text[-6:-3] + "_" + text[-3:]
       if len(text) > 3:
          return text[:-3] + "_" + text[-3:]
       return text
    text = str(obj)
    if not text:
        return no
    return text

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

def get_nosizes(exts: Optional[str] = None) -> str:
    return "\n".join(" ".join([str_(elem) for elem in item]) for item in each_nosizes(exts=exts))
def each_nosizes(exts: Optional[str] = None) -> Iterator[Tuple[str, str, int, int, str]]:
    extlist = exts.split(",") if exts is not None else EXT.split(",")
    for rev, type, disk, size, name in each_sizes():
        if type in ["tree"]: continue
        nam, ext = map_splitext(name)
        for pat in extlist:
            if fnmatch(ext, pat):
                yield rev, type, disk, size, name    
                break

def get_rev_list() -> str:
    return "\n".join(" ".join([str_(elem) for elem in item]) for item in each_sizes())
def get_sizes() -> str:
    return "\n".join(" ".join([str_(elem) for elem in item]) for item in each_sizes())
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

def get_nosumsizes(exts: Optional[str] = None) -> str:
    sumsizes = sorted(list(each_nosumsizes4(exts=exts)), key=lambda x: x[0])
    return "\n".join(" ".join([str_(elem) for elem in item]) for item in sumsizes)
def each_nosumsizes4(exts: Optional[str] = None) -> Iterator[Tuple[int, int, str]]:
    extlist = exts.split(",") if exts is not None else EXT.split(",")
    for sum, disk, changes, name, parts in each_sumsizes5():
        nam, ext = map_splitext(name)
        for pat in extlist:
            if fnmatch(ext, pat):
                yield sum, disk, changes, name
                break
def get_sumsizes() -> str:
    sumsizes = sorted(list(each_sumsizes4()), key=lambda x: x[0])
    return "\n".join(" ".join([str_(elem) for elem in item]) for item in sumsizes)
def each_sumsizes4() -> Iterator[Tuple[int, int, str]]:
    for sum, disk, changes, name, parts in each_sumsizes5():
        yield sum, disk, changes, name
def each_sumsizes5() -> Iterator[Tuple[int, int, str, str]]:
    disksums: Dict[str, int] = {}
    filesums: Dict[str, int] = {}
    dchanges: Dict[str, List[int]] = {}
    for rev, type, disk, size, name in each_sizes():
        if not name: continue
        if type in ["tree"]: continue
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
    sumsizes = sorted(list(each_extsizes5_files()), key=lambda x: x[0])
    return "\n".join(" ".join([str_(elem) for elem in item]) for item in sumsizes)
def each_extsizes5_files() -> Iterator[Tuple[int, int, str]]:
    for sum, disk, changes, ext, names in each_extsizes5():
        yield sum, disk, changes, ext, "%s/revs" % len(names)
def each_extsizes5() -> Iterator[Tuple[int, int, int, str]]:
    disksums: Dict[str, int] = {}
    filesums: Dict[str, int] = {}
    dchanges: Dict[str, Dict[str, int]] = {}
    for disksum, filesum, changes, name, diskchanges in each_sumsizes5():
        if not name: continue
        filename = fs.basename(name)
        nam, ext = map_splitext(filename)
        if ext not in filesums:
             disksums[ext] = 0
             filesums[ext] = 0
             dchanges[ext] = {}
        if name not in dchanges[ext]:
             dchanges[ext][name] = []
        filesums[ext] += filesum
        disksums[ext] += disksum
        dchanges[ext][name] += [ disksum ]
    for ext, disksum in disksums.items():
        yield disksum, filesums[ext], len(dchanges[ext]), ext, "|" + "|".join(dchanges[ext])

mapping = """
jenkinsfile= */Jenkinsfile
jenkinsfile= */Jenkinsfile_*
jenkinsfile= */Error_Jenkinsfile
makefile= */Makefile
makefile= */Makefile*
readme= */README*
license= */LICENSE*
license= */COPYING*
dot.suo = */.suo
dot.fpg = */.fpg
dot.project = */.project
dot.cproject = */.cproject
dot.pylintrc = */.pylintrc
dot.gitignore = */.gitignore
exe.simtask = */simtaskmanager
exe.simtask = */simtaskmanager_debug
exe.datasync = */DataSync
exe.datasync = */DataSync_debug
"""

def map_ext(name, ext):
    if not ext:
        for line in mapping.splitlines():
            if "=" in line:
                mapped1, pattern1 = line.split("=", 1)
                mapped, pattern = mapped1.strip(), pattern1.strip()
                if fnmatch(name, pattern):
                    return mapped
                if pattern.startswith("*/") and "/" not in name:
                    if fnmatch(name, pattern[2:]):
                        return mapped
    return ext

def map_splitext(name: str) -> Tuple[str, str]:
    nam, ext = fs.splitext(name)
    if not ext:
        ext = map_ext(name, ext)
    return nam, ext

def get_noext() -> str:
    return "\n".join(list(each_noext()))
def each_noext() -> Iterator[str]:
     noext = []
     for disksum, filesum, changes, ext, names in each_extsizes5():
        logg.info("ext '%s'", ext)
        if fnmatch(ext, EXT):
            noext = names.split("|")
            logg.debug("found %s noext", len(noext))
     for name in noext:
         if name:
            logg.debug("name %s", name)
            yield name

def get_help():
    text = ""
    for line in open(__file__):
        if line.strip().startswith("elif cmd in"):
            pre, txt = line.split("elif cmd in", 1)
            text += "   " + txt.rstrip().replace("#", "") + "\n"
    return text + __doc__

def run(cmd: str, args: List[str]) -> None:
    name = cmd.replace("-", "_")
    if F"run_{name}" in globals():
        methodcall = globals()[F"run_{name}"]
        methodcall()
    elif cmd in ["help"]: # this help screen
       print(get_help())
    elif cmd in ["sizes"]: # show sizes of all revs
       print(get_sizes())
    elif cmd in ["nosizes"]: # show sizes of all revs with -E '' (default no extension)
       print(get_nosizes())
    elif cmd in ["sumsizes"]: # show sizes of all revs summarized per file history
       print(get_sumsizes())
    elif cmd in ["nosumsizes"]: # show sizes of all revs with -E '' summarized per file history
       print(get_nosumsizes())
    elif cmd in ["extsizes"]: # show sizes of all revs summarized per file extension and history
       print(get_extsizes())
    elif cmd in ["noext"]: # show files with no extension as show on 'extsizes'
       print(get_noext())
    elif "." in cmd and cmd[0] == "*":
       print(get_nosizes(exts = cmd[1:]))
    elif "." in cmd:
       print(get_nosumsizes(exts = cmd))
    elif F"run_{name}" in globals():
        methodcall = globals()[F"run_{name}"]
        print(methodcall())

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
    _o.add_option("-P", "--pretty", action="store_true", default=False,
                  help="enhanced value results [%default]")
    _o.add_option("-E", "--ext", metavar="EXT", default=EXT,
                  help="show nolist for this ext [%default]")
    opt, args = _o.parse_args()
    logging.basicConfig(level=logging.WARNING - opt.verbose * 5)
    #
    GIT = opt.git
    BRANCH = opt.branch
    REPO = opt.repo or None
    PRETTY = opt.pretty
    EXT = opt.ext
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
    if args:
        run(args[0], args[1:])
    else:
        print(get_help())


