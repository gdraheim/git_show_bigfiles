BASEYEAR=2023
FOR=today
PARALLEL = -j2
PYVERSION = 3.9
FILES = *.py *.cfg
PYTHON3 = python3
GIT = git
SCRIPT = src/git_show_bigfiles.py
TESTS = tests/functests.py
VERFILES = src/*.py tests/*tests.py pyproject.toml
V=
VV=-vv

defautl: nam ver

ifeq ("$(wildcard /usr/bin/python3.11)","/usr/bin/python3.12")
  PY39=3.12
endif
ifeq ("$(wildcard /usr/bin/python3.9)","/usr/bin/python3.9")
  PY39=3.9
endif
ifeq ("$(wildcard /usr/bin/python3.10)","/usr/bin/python3.10")
  PY39=3.10
endif
ifeq ("$(wildcard /usr/bin/python3.11)","/usr/bin/python3.11")
  PY39=3.11
endif

PYTHON39=python$(PY39)
COVERAGE3 = ${PYTHON39} -m coverage
PIP3 = $(PYTHON39) -m pip
BUILD3=$(PYTHON39) -m build
TWINE3=$(PYTHON39) -m twine
MYPY3=mypy-$(PY39)

# ..................................

check: ; $(PYTHON3) $(TESTS) 
teststage: ; $(PYTHON3) $(TESTS) $(VV) $V --xmlresults=TEST-teststage.xml


test_%:
	$(PYTHON3) $(TESTS)  $@ $(VV) $V -k

t_%:
	$(PYTHON3) $(TESTS)  $@ $(VV) $V -k

d_%:
	$(PYTHON3) $(TESTS)  $@ $(VV) $V -k

cover:
	$(COVERAGE3) run $(TESTS)
	$(COVERAGE3) report $(SCRIPT)
coverage:	
	$(MAKE) cover
	$(COVERAGE3) report $(SCRIPT)
	$(COVERAGE3) xml

# ....................................
version:
	@ grep -l __version__ $(VERFILES) | { while read f; do : \
	; B="$(BASEYEAR)"; C=$$B; test -z "$(ORIGYEAR)" || C="$(ORIGYEAR)" \
	; Y=`date +%Y -d "$(FOR)"` ; X=$$(expr $$Y - $$B) \
	; W=`date +%W -d "$(FOR)"` \
	; D=`date +%u -d "$(FOR)"` ; sed -i \
	-e "/^ *version = /s/[.]-*[0123456789][0123456789][0123456789]*/.$$X$$W$$D/" \
	-e "/^ *__version__/s/[.]-*[0123456789][0123456789][0123456789]*\"/.$$X$$W$$D\"/" \
	-e "/^ *__version__/s/[.]\\([0123456789]\\)\"/.\\1.$$X$$W$$D\"/" \
	-e "/^ *__copyright__/s/(C) [0123456789]*-[0123456789]*/(C) $$C-$$Y/" \
	-e "/^ *__copyright__/s/(C) [0123456789]* /(C) $$Y /" \
	$$f; done; }
	@ grep "^version =" $(VERFILES) || true
	@ grep ^__version__ $(VERFILES) || true
	@ $(GIT) add $(VERFILES) || true
	@ ver=`cat pyproject.toml | sed -e '/^version *=/!d' -e 's/.*= *"//' -e 's/".*//' -e q` \
	; echo "# $(GIT) commit -m v$$ver"
nam: ; @ sed -e '/^name *=/!d' -e 's/.*= *"//' -e 's/".*//' -e q pyproject.toml
ver: ; @ sed -e '/^version *=/!d' -e 's/.*= *"//' -e 's/".*//' -e q pyproject.toml
verfiles:  ; grep -l __version__ $(VERFILES)

tag:
	@ ver=`grep "^version.*=" pyproject.toml | sed -e "s/version *= */v/"` \
	; rev=`git rev-parse --short HEAD` \
	; echo ": ${GIT} tag $$ver $$rev"

############## https://pypi.org/...

README: README.MD Makefile
	cat README.MD | sed -e "/\\/badge/d" -e /^---/q > README

package pkg:
	rm -rf build dist *.egg-info
	$(MAKE) $(PARALLEL) README
	$(BUILD3)
	- rm -v README
	$(MAKE) fix-metadata-version
	$(TWINE3) check dist/*
	: $(TWINE3) upload dist/*

fix-metadata-version:
	ls dist/*
	rm -rf dist.tmp; mkdir dist.tmp
	cd dist.tmp; for z in ../dist/*; do case "$$z" in *.whl) unzip $$z ;; *) tar xzvf $$z;; esac \
	; ( find . -name PKG-INFO ; find . -name METADATA ) \
	| while read f; do echo FOUND $$f; sed -i -e "s/Metadata-Version: 2.4/Metadata-Version: 2.2/" $$f; done \
	; case "$$z" in *.whl) zip -r $$z * ;; *) tar czvf $$z *;; esac ; ls -l $$z; done

ins install:
	$(MAKE) README
	test ! -d build || rm -rf build
	$(PIP3) install --no-compile --user .
	rm -v README
	$(MAKE) show | sed -e "s|[.][.]/[.][.]/[.][.]/bin|$$HOME/.local/bin|"
	: $(PYTHON39) -m $(notdir $(SCRIPT:.py=)) --help
show:
	@ $(PIP3) show -f `sed -e '/^name *=/!d' -e 's/name *= *"//' -e 's/".*//' pyproject.toml` 

uns uninstall: 
	$(PIP3) uninstall -v --yes `sed -e '/^name *=/!d' -e 's/name *= *"//' -e 's/".*//'  pyproject.toml`

# ...........................................
mypy:
	zypper install -y mypy
	zypper install -y python3-click python3-pathspec

MYPY = $(MYPY3)
MYPY_STRICT = --strict --show-error-codes --show-error-context --no-warn-unused-ignores --python-version $(PYVERSION) --implicit-reexport
AUTOPEP8=autopep8
AUTOPEP8_INPLACE= --in-place

%.type:
	$(MYPY) $(MYPY_STRICT) $(MYPY_OPTIONS) $(@:.type=)

%.pep8:
	$(AUTOPEP8) $(AUTOPEP8_INPLACE) $(AUTOPEP8_OPTIONS) $(@:.pep8=)
	$(GIT) --no-pager diff $(@:.pep8=)

type: 
	$(MAKE) $(SCRIPT).type $(TESTS).type
pep8 style: 
	$(MAKE) $(SCRIPT).pep8 $(TESTS).pep8
