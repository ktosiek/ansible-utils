from ansible.utils.plugins import filter_loader
import os
import pytest


filter_loader.add_directory(
    os.path.join(
        os.path.dirname(__file__),
        '..',
        'filter_plugins'))


multiget = filter_loader.get('multiget').filters()[0]


def test_getting_keys():
    assert ['a', 'b'] == multiget({1: 'a', 2: 'b', 3: 'c'}, [1, 2])


def test_error_on_missing_key():
    with pytest.raises(KeyError):
        multiget({1: 'a'}, [1, 2])


def test_ignoring_missing_keys():
    assert ['a'] == multiget({1: 'a'}, [1, 2], ignore_missing=True)
