BASEYEAR=2023
FOR=today
PARALLEL = -j2
PYVERSION = 3.8
FILES = *.py *.cfg
PYTHON3 = python3
TWINE = twine
GIT = git
SCRIPT = git_bigfile.py

check:
	$(PYTHON3) $(SCRIPT:.py=_tests.py) 

test_%:
	$(PYTHON3) $(SCRIPT:.py=_tests.py)  $@ -v -k

t_%:
	$(PYTHON3) $(SCRIPT:.py=_tests.py)  $@ -vv -k

d_%:
	$(PYTHON3) $(SCRIPT:.py=_tests.py)  $@ -vv -k

# ....................................
version:
	@ grep -l __version__ $(FILES) | { while read f; do : \
	; THISYEAR=`date +%Y -d "$(FOR)"` ; YEARS=$$(expr $$THISYEAR - $(BASEYEAR)) \
        ; WEEKnDAY=`date +%W%u -d "$(FOR)"` ; sed -i \
	-e "/^version /s/[.]-*[0123456789][0123456789][0123456789]*/.$$YEARS$$WEEKnDAY/" \
	-e "/^ *__version__/s/[.]-*[0123456789][0123456789][0123456789]*\"/.$$YEARS$$WEEKnDAY\"/" \
	-e "/^ *__version__/s/[.]\\([0123456789]\\)\"/.\\1.$$YEARS$$WEEKnDAY\"/" \
	-e "/^ *__copyright__/s/(C) \\([123456789][0123456789]*\\)-[0123456789]*/(C) \\1-$$THISYEAR/" \
	-e "/^ *__copyright__/s/(C) [123456789][0123456789]* /(C) $$THISYEAR /" \
	$$f; done; }
	@ grep ^__version__ $(FILES) | grep -v _tests.py
	@ ver=`cat $(SCRIPT) | sed -e '/__version__/!d' -e 's/.*= *"//' -e 's/".*//' -e q` \
	; echo "# $(GIT) commit -m v$$ver"

############## https://pypi.org/...

README: README.MD Makefile
	cat README.MD | sed -e "/\\/badge/d" -e /^---/q > README
setup.py: Makefile
	{ echo '#!/usr/bin/env python3' \
	; echo 'import setuptools' \
	; echo 'setuptools.setup()' ; } > setup.py
	chmod +x setup.py
setup.py.tmp: Makefile
	echo "import setuptools ; setuptools.setup()" > setup.py

.PHONY: build
build:
	rm -rf build dist *.egg-info
	$(MAKE) $(PARALLEL) README setup.py
	# pip install --root=~/local . -v
	$(PYTHON3) setup.py sdist
	- rm -v setup.py README
	$(TWINE) check dist/*
	: $(TWINE) upload dist/*

ins install:
	$(MAKE) setup.py
	$(PYTHON3) -m pip install --no-compile --user .
	rm -v setup.py
	$(MAKE) show | sed -e "s|[.][.]/[.][.]/[.][.]/bin|$$HOME/.local/bin|"
show:
	python3 -m pip show -f $$(sed -e '/^name *=/!d' -e 's/.*= *//' setup.cfg)
uns uninstall: setup.py
	$(MAKE) setup.py
	$(PYTHON3) -m pip uninstall -v --yes $$(sed -e '/^name *=/!d' -e 's/.*= *//' setup.cfg)
	rm -v setup.py

# ...........................................
mypy:
	zypper install -y mypy
	zypper install -y python3-click python3-pathspec

MYPY = mypy
MYPY_STRICT = --strict --show-error-codes --show-error-context --no-warn-unused-ignores --python-version $(PYVERSION) --implicit-reexport
AUTOPEP8=autopep8
AUTOPEP8_INPLACE= --in-place

%.type:
	$(MYPY) $(MYPY_STRICT) $(MYPY_OPTIONS) $(@:.type=)

%.pep8:
	$(AUTOPEP8) $(AUTOPEP8_INPLACE) $(AUTOPEP8_OPTIONS) $(@:.pep8=)
	$(GIT) --no-pager diff $(@:.pep8=)

type: 
	$(MAKE) $(SCRIPT).type $(SCRIPT:.py=_tests.py).type
pep8 style: 
	$(MAKE) $(SCRIPT).pep8 $(SCRIPT:.py=_tests.py).pep8
