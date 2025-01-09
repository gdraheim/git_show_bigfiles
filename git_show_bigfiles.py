#! /usr/bin/env python3
""" git bigfile detection """

__copyright__ = "(C) Guido Draheim, all rights reserved"""
__version__ = "1.0.2012"

# pylint: disable=missing-function-docstring,missing-class-docstring,unspecified-encoding,dangerous-default-value,unused-argument,unused-variable,line-too-long,multiple-statements,consider-using-f-string
from typing import Union, Optional, Tuple, List, Dict, Iterator, Iterable, Any, cast, Sequence, Callable, NamedTuple

import os
import os.path as fs
import sys
import re
import subprocess
from datetime import date as Date
from datetime import datetime as Time
from collections import OrderedDict
from fnmatch import fnmatchcase as fnmatch
import logging
logg = logging.getLogger("CHECK")

if sys.version[0] == '2':
    stringtypes = basestring # type: ignore[name-defined] # pylint: disable=undefined-variable # PEP 484
else:
    stringtypes = str # pylint: disable=invalid-name

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
FMT = ""
KB = 1024
MB = KB * KB
MAXSIZE: float = 50.0 # in MB

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
    if isinstance(text, bytes):
        encoded = sys.getdefaultencoding()
        if encoded in ["ascii"]:
            encoded = "utf-8"
        try:
            return text.decode(encoded)
        except UnicodeDecodeError:
            return text.decode("latin-1")
    return text # works for None as well
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
        if line.count(" ") >= 2:
            a, b, c = line.split(" ", 2)
            yield a, b, c.strip()
        elif " " in line:
            logg.warning("can not split3: %s", line.rstrip())
def splits3(inp: str) -> Iterator[Tuple[str, str, str]]:
    for a, b, c in split3(inp.splitlines()):
        yield a, b, c
def split4(inp: Iterable[str]) -> Iterator[Tuple[str, str, str, str]]:
    for line in inp:
        if line.count(" ") >= 3:
            a, b, c, d = line.split(" ", 3)
            yield a, b, c, d.strip()
        elif " " in line:
            logg.warning("can not split4: %s", line.rstrip())
def splits4(inp: str) -> Iterator[Tuple[str, str, str, str]]:
    for a, b, c, d in split4(inp.splitlines()):
        yield a, b, c, d

# ..............................................................

JSONItem = Union[str, int, float, bool, Date, Time, None, Dict[str, Any], List[Any]]
JSONDict = Dict[str, JSONItem]
JSONList = List[JSONDict]
RowSortList = Union[Sequence[str], Dict[str, str], Callable[[JSONDict], str]]
ColSortList = Union[Sequence[str], Dict[str, str], Callable[[str], str]]
LegendList = Union[Dict[str, str], Sequence[str]]

def tabToFMT(fmt: str, result: JSONList, sorts: RowSortList = [], formats: Dict[str, str] = {}, *,  #
             datedelim: str = '-', legend: LegendList = [],  #
             reorder: ColSortList = [], combine: Dict[str, str] = {}) -> str:
    """ This code is supposed to be copy-n-paste into other files. You can safely try-import from 
        tabtotext or tabtoxlsx to override this function. Only a subset of features is supported. """
    tab = '|'
    if fmt in ["wide", "text"]:
        tab = ''
    if fmt in ["tabs", "tab", "dat", "ifs", "data"]:
        tab = '\t'
    if fmt in ["csv", "scsv", "list"]:
        tab = ';'
    if fmt in ["xls", "sxlx"]:
        tab = ','
    none_string = "~"
    true_string = "(yes)"
    false_string = "(no)"
    minwidth = 5
    floatfmt = "%4.2f"
    noright = fmt in ["dat"]
    noheaders = fmt in ["text", "list"]
    formatright = re.compile("[{]:[^{}]*>[^{}]*[}]")
    formatnumber = re.compile("[{]:[^{}]*[defghDEFGHMQR$%][}]")
    def rightalign(col: str) -> bool:
        if col in formats and not noright:
            if formats[col].startswith(" "):
                return True
            if formatright.search(formats[col]):
                return True
            if formatnumber.search(formats[col]):
                return True
        return False
    def format(name: str, val: JSONItem) -> str:  # pylint: disable=redefined-builtin
        if name in formats:
            fmt4 = formats[name]
            if "{:" in fmt4:
                try:
                    return fmt4.format(val)
                except (ValueError, TypeError) as e:
                    logg.debug("format <%s> does not apply: %s", fmt, e)
            if "%s" in fmt4:
                try:
                    return fmt % strJSON(val)
                except (ValueError, TypeError) as e:
                    logg.debug("format <%s> does not apply: %s", fmt, e)
        if isinstance(val, float):
            return floatfmt % val
        return strJSON(val)
    def strJSON(value: JSONItem) -> str:
        if value is None: return none_string
        if value is False: return false_string
        if value is True: return true_string
        if isinstance(value, Time):
            return value.strftime("%Y-%m-%d.%H%M")
        if isinstance(value, Date):
            return value.strftime("%Y-%m-%d")
        return str(value)
    def asdict(item: JSONDict) -> JSONDict:
        if hasattr(item, "_asdict"):
            return item._asdict()  # type: ignore[attr-defined, union-attr, no-any-return, arg-type]
        if isinstance(item, stringtypes):
            return { "value": item}
        return item
    cols: Dict[str, int] = {}
    for item in result:
        for name, value in asdict(item).items():
            if name not in cols:
                cols[name] = max(minwidth, len(name))
            cols[name] = max(cols[name], len(format(name, value)))
    def sortkey(header: str) -> str:
        if callable(reorder):
            return reorder(header)
        else:
            sortheaders = reorder
            if not sortheaders and not callable(sorts):
                sortheaders = sorts
            if isinstance(sortheaders, dict):
                if header in sortheaders:
                    return sortheaders[header]
            else:
                if header in sortheaders:
                    return "%07i" % sortheaders.index(header)
        return header
    def sortrow(row: JSONDict) -> str:
        item = asdict(row)
        if callable(sorts):
            return sorts(item)
        else:
            sortvalue = ""
            for sort in sorts:
                if sort in item:
                    value = item[sort]
                    if value is None:
                        sortvalue += "\n?"
                    elif value is False:
                        sortvalue += "\n"
                    elif value is True:
                        sortvalue += "\n!"
                    elif isinstance(value, int):
                        sortvalue += "\n%020i" % value
                    else:
                        sortvalue += "\n" + strJSON(value)
                else:
                    sortvalue += "\n?"
            return sortvalue
    # CSV
    if fmt in ["list", "csv", "scsv", "xlsx", "xls", "tab", "dat", "ifs", "data"]:
        tab1 = tab if tab else ";"
        import csv  # pylint: disable=import-outside-toplevel
        csvfile = StringIO()
        writer = csv.DictWriter(csvfile, fieldnames=sorted(cols.keys(), key=sortkey),
                                restval='~', quoting=csv.QUOTE_MINIMAL, delimiter=tab1)
        if not noheaders:
            writer.writeheader()
        for row in sorted(result, key=sortrow):
            rowvalues: Dict[str, str] = {}
            for name, value in asdict(row).items():
                rowvalues[name] = format(name, value)
            writer.writerow(rowvalues)
        return cast(str, csvfile.getvalue())
    # GFM
    def rightF(col: str, formatter: str) -> str:
        if rightalign(col):
            return formatter.replace("%-", "%")
        return formatter
    def rightS(col: str, formatter: str) -> str:
        if rightalign(col):
            return formatter[:-1] + ":"
        return formatter
    tab2 = (tab + " " if tab else "")
    lines: List[str] = []
    if not noheaders:
        line = [rightF(name, tab2 + "%%-%is" % cols[name]) % name for name in sorted(cols.keys(), key=sortkey)]
        lines += [(" ".join(line)).rstrip()]
        if tab:
            seperators = [(tab2 + "%%-%is" % cols[name]) % rightS(name, "-" * cols[name])
                          for name in sorted(cols.keys(), key=sortkey)]
            lines.append(" ".join(seperators))
    for item in sorted(result, key=sortrow):
        values: Dict[str, str] = {}
        for name, value in asdict(item).items():
            values[name] = format(name, value)
        line = [rightF(name, tab2 + "%%-%is" % cols[name]) % values.get(name, none_string)
                for name in sorted(cols.keys(), key=sortkey)]
        lines.append((" ".join(line)).rstrip())
    return "\n".join(lines) + "\n"

# ..............................................................
class HistAuthor4(NamedTuple):
    authorname: str
    author: str
    committername: str
    committer: str
class Author2(NamedTuple):
    email: str
    name: str
class Committer2(NamedTuple):
    email: str
    name: str

def each_mail2() -> Iterator[Union[Author2, Committer2]]:
    emails: List[str] = []
    for mail in each_author4():
        if mail.author not in emails:
            emails.append(mail.author)
            yield Author2(mail.author, mail.authorname)
        if mail.committer not in mail:
            emails.append(mail.committer)
            yield Committer2(mail.committer, mail.committername)
def each_author4() -> Iterator[HistAuthor4]:
    git, main = GIT, BRANCH
    out = output(F"{git} rev-list '--pretty=;%an;%ae;%cn;%ce' {main} ", REPO)
    revs: Dict[str, str] = OrderedDict()
    disks: Dict[str, int] = {}
    sizes: Dict[str, int] = {}
    types: Dict[str, str] = {}
    for line in out.splitlines():
        if line.startswith(";"):
            mails = line.strip().split(";")
            authorname = mails[1] if len(mails) >=2 else ""
            author = mails[2] if len(mails) >=3 else ""
            committername = mails[3] if len(mails) >= 4 else ""
            committer = mails[4] if len(mails) >= 5 else ""
            yield HistAuthor4(authorname, author, committername, committer)



# ..............................................................
class HistSize5(NamedTuple):
    rev: str
    typ: str
    disksize: int
    filesize: int
    name: str
def get_rev_list() -> str:
    return "\n".join(" ".join([str_(elem) for elem in item]) for item in each_size5())
def get_sizes() -> str:
    return "\n".join(" ".join([str_(elem) for elem in item]) for item in each_size5())
def each_size5() -> Iterator[HistSize5]:
    git, main = GIT, BRANCH
    out = output(F"{git} rev-list {main} --objects", REPO)
    revs: Dict[str, str] = OrderedDict()
    disks: Dict[str, int] = {}
    sizes: Dict[str, int] = {}
    types: Dict[str, str] = {}
    for rev, name in splits2(out):
        logg.debug("FOUND %s %s", rev, name)
        revs[rev] = name
    objectnames = "\n".join(revs.keys()) + "\n"
    logg.debug("objectnames => %s", objectnames)
    siz = output(F"{git} cat-file --batch-check='%(objectsize:disk) %(objectsize) %(objecttype) %(objectname)'",
                 REPO, pipe=objectnames)
    logg.debug("cat-file => %s", siz)
    for disk1, size1, type1, rev in splits4(siz):
        disks[rev] = int(disk1)
        sizes[rev] = int(size1)
        types[rev] = type1
    for rev in revs:
        nam = revs[rev]
        dsk = disks[rev]
        sze = sizes[rev]
        typ = types[rev]
        yield HistSize5(rev, typ, dsk, sze, nam)
def get_nosizes(exts: Optional[str] = None) -> str:
    return "\n".join(" ".join([str_(elem) for elem in item]) for item in each_nosize5(exts=exts))
def each_nosize5(exts: Optional[str] = None) -> Iterator[HistSize5]:
    extlist = exts.split(",") if exts is not None else EXT.split(",")
    for rev, typ, disk, size, name in each_size5():
        if typ in ["tree"]: continue
        nam, ext = map_splitext(name)
        for pat in extlist:
            if fnmatch(ext, pat):
                yield HistSize5(rev, typ, disk, size, name)
                break
def get_oversize() -> str:
    return "\n".join(" ".join([str_(elem) for elem in item]) for item in each_oversize5())
def each_oversize5() -> Iterator[HistSize5]:
    for rev, typ, disk, size, name in each_size5():
        if size >= MAXSIZE * MB:
            yield HistSize5(rev, typ, disk, size, name)

def each_gitfile() -> Iterator[str]:
    found = []
    for elem in each_size5():
        if "/.git/" in elem.name:
            if elem.name not in found:
                found.append(elem.name)
                yield elem.name
def each_gitdir() -> Iterator[str]:
    found = []
    for elem in each_size5():
        if "/.git/" in elem.name:
            gitpath = re.sub("/[.]git/.*", "/.git", elem.name)
            if gitpath not in found:
                found.append(gitpath)
                yield gitpath

class SumSize4(NamedTuple):
    disksum: int
    filesum: int
    changes: int
    name: str
class SumSize5(NamedTuple):
    disksum: int
    filesum: int
    changes: int
    name: str
    dchanges: str
def get_nosumsizes(exts: Optional[str] = None) -> str:
    sumsizes = sorted(list(each_nosumsize4(exts=exts)), key=lambda x: x[0])
    return "\n".join(" ".join([str_(elem) for elem in item]) for item in sumsizes)
def each_nosumsize4(exts: Optional[str] = None) -> Iterator[SumSize4]:
    extlist = exts.split(",") if exts is not None else EXT.split(",")
    for sums, disk, changes, name, parts in each_sumsize5():
        nam, ext = map_splitext(name)
        for pat in extlist:
            if fnmatch(ext, pat):
                yield SumSize4(sums, disk, changes, name)
                break
def get_sumsizes() -> str:
    sumsizes = sorted(list(each_sumsize4()), key=lambda x: x[0])
    return "\n".join(" ".join([str_(elem) for elem in item]) for item in sumsizes)
def each_sumsize4() -> Iterator[SumSize4]:
    for disk, sums, changes, name, parts in each_sumsize5():
        logg.debug("sum disk %s size %s", disk, sums)
        yield SumSize4(disk, sums, changes, name)
def each_sumsize5() -> Iterator[SumSize5]:
    disksums: Dict[str, int] = {}
    filesums: Dict[str, int] = {}
    dchanges: Dict[str, List[int]] = {}
    for rev, typ, disk, size, name in each_size5():
        logg.debug("disk %s size %s", disk, size)
        if not name: continue
        if typ in ["tree"]: continue
        if name not in filesums:
            disksums[name] = 0
            filesums[name] = 0
            dchanges[name] = []
        filesums[name] += size
        disksums[name] += disk
        dchanges[name] += [disk]
    for name, disksum in disksums.items():
        yield SumSize5(disksum, filesums[name], len(dchanges[name]), name,
                       "|" + "+".join([str(item) for item in dchanges[name]]))

def each_sumoversize4() -> Iterator[SumSize4]:
    for disk, sums, changes, name, parts in each_sumoversize5():
        logg.debug("sum disk %s size %s (over %i MB)", disk, sums, MAXSIZE)
        yield SumSize4(disk, sums, changes, name)
def each_sumoversize5() -> Iterator[SumSize5]:
    disksums: Dict[str, int] = {}
    filesums: Dict[str, int] = {}
    dchanges: Dict[str, List[int]] = {}
    for rev, typ, disk, size, name in each_size5():
        if size < MAXSIZE * MB: continue
        logg.debug("disk %s size %s (over %i MB)", disk, size, MAXSIZE)
        if not name: continue
        if typ in ["tree"]: continue
        if name not in filesums:
            disksums[name] = 0
            filesums[name] = 0
            dchanges[name] = []
        filesums[name] += size
        disksums[name] += disk
        dchanges[name] += [disk]
    for name, disksum in disksums.items():
        yield SumSize5(disksum, filesums[name], len(dchanges[name]), name,
                       "|" + "+".join([str(item) for item in dchanges[name]]))

class ExtSize5(NamedTuple):
    disksum: int
    filesum: int
    changes: int
    ext: str
    files: str
def get_extsizes() -> str:
    sumsizes = sorted(list(each_extsize4()), key=lambda x: x[0])
    return "\n".join(" ".join([str_(elem) for elem in list(item)]) for item in sumsizes)
def each_extsize4() -> Iterator[ExtSize5]:
    for sums, disk, changes, ext, names in each_extsize5():
        yield ExtSize5(sums, disk, changes, ext, "%s/files" % names.count("|"))
def each_extsize5() -> Iterator[ExtSize5]:
    disksums: Dict[str, int] = {}
    filesums: Dict[str, int] = {}
    dchanges: Dict[str, Dict[str, List[int]]] = {}
    for disksum, filesum, changes, name, diskchanges in each_sumsize5():
        if not name: continue
        logg.debug("sum disk %s size %s", disksum, filesum)
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
        dchanges[ext][name] += [disksum]
    for ext, disksum in disksums.items():
        yield ExtSize5(disksum, filesums[ext], len(dchanges[ext]), ext, "|" + "|".join(dchanges[ext]))

def each_extoversize4() -> Iterator[ExtSize5]:
    for sums, disk, changes, ext, names in each_extoversize5():
        yield ExtSize5(sums, disk, changes, ext, "%s/files" % names.count("|"))
def each_extoversize5() -> Iterator[ExtSize5]:
    disksums: Dict[str, int] = {}
    filesums: Dict[str, int] = {}
    dchanges: Dict[str, Dict[str, List[int]]] = {}
    for disksum, filesum, changes, name, diskchanges in each_sumoversize5():
        if not name: continue
        logg.debug("sum disk %s size %s (over %i MB)", disksum, filesum, MAXSIZE)
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
        dchanges[ext][name] += [disksum]
    for ext, disksum in disksums.items():
        yield ExtSize5(disksum, filesums[ext], len(dchanges[ext]), ext, "|" + "|".join(dchanges[ext]))

MAPPINGS = """
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

def map_ext(name: str, ext: str) -> str:
    if not ext:
        for line in MAPPINGS.splitlines():
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

class NoExt1(NamedTuple):
    ext: str
def get_noexts() -> str:
    return "\n".join(list(item.ext for item in each_noext1()))
def each_noext1() -> Iterator[NoExt1]:
    noext = []
    for disksum, filesum, changes, ext, names in each_extsize5():
        logg.debug("ext '%s'", ext)
        if fnmatch(ext, EXT):
            noext = names.split("|")
            logg.debug("found %s noext", len(noext))
    for name in noext:
        if name:
            logg.debug("name %s", name)
            yield NoExt1(name)

def get_help() -> str:
    text = ""
    for line in open(__file__):
        if line.strip().startswith("elif cmd in"):
            pre, txt = line.split("elif cmd in", 1)
            text += "   " + txt.rstrip().replace("#", "") + "\n"
    return text + __doc__

def _main(cmd: str, args: List[str]) -> None:
    if PRETTY:
        formats = {"disksum": " {:_}", "filesum": " {:_}", "changes": " "}
    else:
        formats = {"disksum": " ", "filesum": " ", "changes": " "}
    name = cmd.replace("-", "_")
    if F"run_{name}" in globals():
        methodcall = globals()[F"run_{name}"]
        methodcall()
    elif cmd in ["help"]:  # this help screen
        print(get_help())
    elif cmd in ["oversize"]:  # show files in all revs with sizes over lfs limit
        headers = ["disksize", "filesize", "rev", "typ"]
        print(tabToFMT(FMT, list(each_oversize5()), headers, formats))  # type: ignore[arg-type]
        # print(get_oversize())
    elif cmd in ["size"]:  # show sizes of all revs
        headers = ["disksize", "filesize", "rev", "typ"]
        print(tabToFMT(FMT, list(each_size5()), headers, formats))  # type: ignore[arg-type]
        # print(get_sizes())
    elif cmd in ["nosize"]:  # show sizes of all revs with -E '' (default no extension)
        headers = ["disksize", "filesize", "rev", "typ"]
        print(tabToFMT(FMT, list(each_nosize5()), headers, formats))  # type: ignore[arg-type]
        # print(get_nosizes())
    elif cmd in ["nosumsize"]:  # show sizes of all revs with -E '' summarized per file history
        headers = ["disksum", "filesum", "changes"]
        print(tabToFMT(FMT, list(each_nosumsize4()), headers, formats))  # type: ignore[arg-type]
        # print(get_nosumsizes())
    elif cmd in ["sumsize"]:  # show sizes of all revs summarized per file history
        headers = ["disksum", "filesum", "changes"]
        print(tabToFMT(FMT, list(each_sumsize4()), headers, formats))  # type: ignore[arg-type]
        # print(get_sumsizes())
    elif cmd in ["sumoversize"]:  # show sizes of all revs with oversize files summarized per file history
        headers = ["disksum", "filesum", "changes"]
        print(tabToFMT(FMT, list(each_sumoversize4()), headers, formats))  # type: ignore[arg-type]
        # print(get_sumsizes())
    elif cmd in ["extoversize"]:  # show ext with oversize files and summarize over history
        headers = ["disksum", "filesum", "changes", "ext", "files"]
        print(tabToFMT(FMT, list(each_extoversize4()), headers, formats))  # type: ignore[arg-type]
        # print(get_extoversizes())
    elif cmd in ["extsize"]:  # show sizes of all revs summarized per file extension and history
        headers = ["disksum", "filesum", "changes", "ext", "files"]
        print(tabToFMT(FMT, list(each_extsize4()), headers, formats))  # type: ignore[arg-type]
        # print(get_extsizes())
    elif cmd in ["noext"]:  # show files with no extension as show on 'extsizes'
        print(tabToFMT(FMT, list(each_noext1())))  # type: ignore[arg-type]
        # print(get_noexts())
    elif cmd in ["git", "gitlist"]:  # show /.git/ paths having files (for migrations)
        print(tabToFMT(FMT, list(each_gitdir())))  # type: ignore[arg-type]
        # print(get_noexts())
    elif cmd in ["authors", "authorlist"]:  # show list of authors and committers (for migrations)
        print(tabToFMT(FMT, list(each_author4())))  # type: ignore[arg-type]
    elif cmd in ["mail", "emails", "emaillist"]:  # show list of authors and committers (for migrations)
        print(tabToFMT(FMT, list(each_mail2())))  # type: ignore[arg-type]
        # print(get_noexts())
    elif "." in cmd and cmd[0] == "*":
        print(get_nosizes(exts=cmd[1:]))
    elif "." in cmd:
        print(get_nosumsizes(exts=cmd))
    elif F"get_{name}" in globals():
        methodcall = globals()[F"get_{name}"]
        print(methodcall())

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
    cmdline.add_option("-r", "--repo", metavar="PATH", default=REPO,
                      help="use different repo path [%default]")
    cmdline.add_option("-l", "--logfile", metavar="FILE", default="",
                      help="additionally save the output log to a file [%default]")
    cmdline.add_option("-x", "--maxsize", metavar="MB", default=MAXSIZE,
                      help="oversize files (in MB) must be in lfs [%default]")
    cmdline.add_option("-P", "--pretty", action="store_true", default=False,
                      help="enhanced value results [%default]")
    cmdline.add_option("-E", "--ext", metavar="EXT", default=EXT,
                      help="show nolist for this ext [%default]")
    cmdline.add_option("-o", "--fmt", metavar="md|text|csv", default=FMT,
                      help="use differen tabtotext [%default]")
    opt, cmdline_args = cmdline.parse_args()
    logging.basicConfig(level=logging.WARNING - opt.verbose * 5)
    #
    GIT = opt.git
    BRANCH = opt.branch
    REPO = opt.repo or None
    MAXSIZE = float(opt.maxsize)
    PRETTY = opt.pretty
    EXT = opt.ext
    FMT = opt.fmt
    logg.debug("BRANCH %s REPO %s", BRANCH, REPO)
    #
    _logfile = None  # pylint: disable=invalid-name
    if opt.logfile:
        if os.path.exists(opt.logfile):
            os.remove(opt.logfile)
        _logfile = logging.FileHandler(opt.logfile)
        _logfile.setFormatter(logging.Formatter("%(levelname)s:%(relativeCreated)d:%(message)s"))
        logging.getLogger().addHandler(_logfile)
        logg.info("log diverted to %s", opt.logfile)
    #
    logg.debug("args %s", cmdline_args)
    if cmdline_args:
        _main(cmdline_args[0], cmdline_args[1:])
    else:
        print(get_help())
