[![Style Check](https://github.com/gdraheim/git_show_bigfiles/actions/workflows/stylecheck.yml/badge.svg?event=push&branch=main)](https://github.com/gdraheim/git_show_bigfiles/actions/workflows/stylecheck.yml)
[![Type Check](https://github.com/gdraheim/git_show_bigfiles/actions/workflows/typecheck.yml/badge.svg?event=push&branch=main)](https://github.com/gdraheim/git_show_bigfiles/actions/workflows/typecheck.yml)
[![Code Coverage](https://img.shields.io/badge/10%20tests-43%25%20coverage-brightgreen)](https://github.com/gdraheim/git_show_bigfiles/blob/main/git_show_bigfiles_tests.py)
[![PyPI version](https://badge.fury.io/py/git_show_bigfiles.svg)](https://pypi.org/project/git_show_bigfiles/)

# git show bigfiles - detection of files by size

The tool allows to check for large files in a git repo
with the intent to put it under git-lfs control.

Specifically it will check for parts being changed often.

The tool requires "git" to be installed using "git rev-list" 
and "git cat-file" to inspect the object store. Read more about 
git-plumbing at [git-scm:Git-Internals-Git-Objects](https://git-scm.com/book/en/v2/Git-Internals-Git-Objects)


