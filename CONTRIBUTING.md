# How to contribute

We encourage contributing to this project and we thank you for taking the time to contribute.
To do so, please follow our contributing guideline:

## 1- Submit an issue
-  Check if a related issue does not already exist.
-  If not, submit an [issue ticket](https://github.com/Netsach/concrete-datastore/issues/new) that respects the following steps:
   -  Initiate the issue with an explicit title.
   -  Describe the issue.
   -  Choose the adequate label for your issue.
   -  In case of a bug, include the steps to reproduce, actual results and expected results.
-  Submit the issue and assign it to one of the maintainers to discuss it.
-  If you are able and want to fix the issue, see the chapter below.

## 2- Make changes
-  Fork the repository.
-  In your forked repository, create a new branch based on the latest version of `master` named `feature-<feature-name>` in case of a feature, or `fix-<bug>` in case of a bug fix (Please avoid working directly on `master` branch)
-  Make sure your code is [PEP8](https://www.python.org/dev/peps/pep-0008/) compliant and your `.py` files are [Black](https://black.readthedocs.io/en/stable/) formatted.
-  Add unittests to test your changes.
-  Add a brief description of your changes in [CHANGELOG.md](CHANGELOG.md) in the right section (Added, Changed, Removed).
-  Make sure your tests, pylint and [bandit](https://bandit.readthedocs.io/en/latest/) pass (see chapter [Code Quality](#CodeQuality) below for more details on how to run the checks)
-  Describe your commits with explicit messages

## 3- Submit changes
-  Push your changes to your branch on your forked repository
-  Open a pull request to the original repository
-  Reference the issue you handled in your pull request.
:no_entry_sign: **PLEASE DO NOT CLOSE THE ISSUE BY YOURSELF**
-  Assign the pull request to one of the repository maintainers.
:no_entry_sign: **IF YOU ARE ONE OF THE MAINTAINERS, PLEASE DO NOT ACCEPT YOUR OWN PULL REQUESTS UNLESS YOUR CHANGES WERE REVIEWED AND VALIDATED BY AT LEAST ANOTHER MEMBER OF THE PROJECT**
-  The pull request will be reviewed and discussed before any merge.

## <a name="CodeQuality"></a>Code Quality

### Configure the environment

```shell
python3 -m venv env
source env/bin/activate
pip install -e ".[dev,security,lint,lint_py3]"
```

### Ensure black

> Black makes code review faster by producing the smallest diffs possible.

[see black github project page](https://github.com/psf/black)

#### format all files:

```shell
black --config pyproject.toml .
```

#### check if all files ar well formatted:

```shell
black --check --config pyproject.toml .
```

### Ensure lint

> Pylint is a Python static code analysis tool which looks for programming errors, helps enforcing a coding standard, sniffs for code smells and offers simple refactoring suggestions.

[see pylint github project page](https://github.com/PyCQA/pylint)

```shell
pylint -E concrete_datastore
```

### Ensure bandit

> Bandit is a tool designed to find common security issues in Python code.

[see bandit github project page](https://github.com/PyCQA/bandit)

```shell
bandit concrete_datastore -r --exclude tests
```


### Release a new version

- change version within `concrete_datastore/__init__.py` file.
- Update CHANGELOG.md to fix version
- check version
    - ``VERSION=`python3 setup.py --version` ``
    - `echo $VERSION`
- commit yout changes
    - `git commit -am 'Release version '$VERSION`
- tag the new version
    - `git tag -a $VERSION -m $VERSION`
- install setuptools and whell
    - `pip install -U pip`
    - `pip install -U setuptools wheel twine`
- create dist
    - `python3 setup.py sdist`
    - `pip wheel --no-index --no-deps --wheel-dir dist dist/concrete-datastore-$VERSION.tar.gz`
- upload new version
    - `scp -P 11092 dist/* debian@packages.netsach.eu:/data/packages/`
    - NOOOOOOOOO - `python3 -m twine upload dist/*` - OOOOOOOON
- push the new tag
    - `git push --follow-tags`
