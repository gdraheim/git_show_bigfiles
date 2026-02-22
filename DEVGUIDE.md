# DEVELOPMENT GUIDELINES

* workplace setup
* makefile targets
* release process

## WORKPLACE SETUP

Development can be done with a pure text editor and a terminal session.

### VSCode setup

Use python and mypy extensions for Visual Studio Code (from Microsoft).

* Control-P: "ext list"
  * look for "Python", "Pylance" (style checker), "Mypy Type Checker" (type checker)
  * optional "Makefile Tools"
* Control-P: "ext install ms-python.mypy-type-checker"
  * this one pulls the latest mypy from the visualstudio marketplace
  * https://marketplace.visualstudio.com/items?itemName=ms-python.mypy-type-checker

The make targets are defaulting to tests with python3.6 but the mypy plugin
for vscode requires atleast python3.8. All current Linux distros provide an
additional package with a higher version number, e.g "zypper install python311".
Be sure to also install "python311-mypy" or compile "pip3 install mypy". 
Implant the paths to those tools into the workspace settings = `.vscode/settings.json`

    {
        "mypy-type-checker.reportingScope": "workspace",
        "mypy-type-checker.interpreter": [
                "/usr/bin/python3.11"
        ],
        "mypy-type-checker.path": [
                "mypy-3.11"
        ],
        "mypy-type-checker.args": [
                "--strict",
                "--show-error-codes",
                "--show-error-context",
                "--no-warn-unused-ignores",
                "--ignore-missing-imports",
                "--exclude=build"
        ],
        "python.defaultInterpreterPath": "python3"
    }

### Makefile setup

Common distro packages are:
* `zypper install python3 python3-pip` # atleast python3.6
* `zypper install python3-wheel python3-twine`
* `zypper install python3-coverage python3-unittest-xml-reporting`
* `zypper install python3-mypy python3-mypy_extensions python3-typing_extensions`
* `zypper install python3-autopep8`

## Makefile targets

### static code checking

* `make type`
* `make style`

## compiling targets

* `make build` # compiling the pypi package

### testing targets

* `make check` # running git_bigfile_tests.py 
* `make install` and `make uninstalls`

### release targets

* `make version`
* `make pkg`

## RELEASE PROCESS

* `make type`   # python mypy
* `make style`  # python style
* `make check`
* `make version` # or `make version FOR=tomorrow`
* `make pkg`
* `make ins`
* `make uns`
* `make coverage`
   * update README.md if necessary
* `git push` # if necessary
* wait for gitlab-ci or github-workflows to be okay (if active)
* prepare a tmp.changes.txt 
* `make tag`
   * run shown `git tag -F tmp.changes.txt v1.x` 
* update the short description on github
* `make pkg`
  * run show `twine ..`
* `git push --tags`
* consider making a github release with the latest news
