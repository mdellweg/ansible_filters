# Copyright (c) 2020 Matthias Dellweg
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


import typing as t

from jinja2.runtime import Undefined


def empty_test(value: t.Any) -> bool:
    """
    Check whether a value is false or an empty string, list or dict.
    """
    if isinstance(value, Undefined):
        return True
    if isinstance(value, bool):
        return not value
    if value is None:
        return True
    if value == "":
        return True
    if value == []:
        return True
    if value == {}:
        return True
    if value == b"":
        return True
    return False


class TestModule:
    def tests(self) -> t.Dict[str, t.Callable]:
        return {
            "empty": empty_test,
        }
