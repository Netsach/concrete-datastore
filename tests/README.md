# Code Quality

## Running the test suite

### Configure the environment

```shell
python3 -m venv env
source env/bin/activate
pip install -e ".[tests]"
```

### Run the tests

Invoke Pytest with the following args:

```shell
pytest --ds=concrete_datastore.settings.unittest_settings --pyargs -q tests --cov --cov-report html --cov-report term
```

You can decide to deactivate coverage

```shell
pytest --ds=concrete_datastore.settings.unittest_settings --pyargs -q tests
```

You can also decide of which test file(s) you want to run by adding the filename(s) in the command:

```shell
pytest -s concrete_datastore --pyargs -q tests.test_imports
```
or
```shell
pytest -s concrete_datastore --pyargs -q tests.tests_permissions.test_permissions_with_user_level
```
