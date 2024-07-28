# Copyright (c) 2020 Matthias Dellweg
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import typing as t

try:
    import jq

    HAS_JQ = True
except ImportError:
    HAS_JQ = False

try:
    from packaging.version import parse as parse_version

    HAS_PACKAGING = True
except ImportError:
    HAS_PACKAGING = False

from ansible.errors import AnsibleError, AnsibleFilterError
from ansible.module_utils import six
from ansible.module_utils._text import to_native, to_text
from ansible.module_utils.basic import missing_required_lib
from ansible.utils.display import Display


def jq_filter(value: t.Any, filter_expression: str, all: bool = False) -> t.Any:
    """
    Parse input with jq language.
    """
    if not HAS_JQ:
        raise AnsibleError(missing_required_lib("jq"))
    if all:
        return jq.all(filter_expression, value)
    else:
        return jq.first(filter_expression, value)


def map_to_native(value: t.Any) -> t.Any:
    if isinstance(value, six.string_types):
        return to_native(value)
    if isinstance(value, dict):
        return {map_to_native(key): map_to_native(val) for key, val in value.items()}
    if isinstance(value, list):
        return [map_to_native(val) for val in value]
    return value


def repr_filter(value: t.Any) -> str:
    """
    Convert value into python representation string.
    """
    return to_text(repr(map_to_native(value)))


def canonical_semver_filter(value: str) -> str:
    """
    Represent a semantic version in a canonical form.
    """
    return to_text(str(parse_version(to_native(value))))


def _assert_key(key: t.Any) -> str:
    if not isinstance(key, str):
        raise AnsibleFilterError("Dictionary keys need to be strings.")
    if not key.isidentifier():
        raise AnsibleFilterError("Dictionary keys need to be proper identifiers.")
    return key


def _quote(string: str) -> str:
    return '"' + string.replace("\\", "\\\\").replace('"', '\\"') + '"'


def to_jaml(data: t.Any, level: int = 0, embed_in: str = "") -> str:
    """Filter for Jinja 2 templates to render human readable YAML."""
    # Don't even believe this is complete!
    # Yes, I have checked pyyaml and ruamel.

    nl = False
    if isinstance(data, str):
        result = _quote(data)
    elif data is True:
        result = "true"
    elif data is False:
        result = "false"
    elif isinstance(data, int):
        result = f"{data}"
    elif isinstance(data, list):
        if len(data):
            nl = embed_in == "dict"
            result = ("\n" + "  " * level).join(
                ("-" + to_jaml(item, level + 1, "list") for item in data)
            )
        else:
            result = "[]"
    elif isinstance(data, dict):
        if len(data):
            nl = embed_in == "dict"
            result = ("\n" + "  " * level).join(
                (
                    f"{_assert_key(key)}:" + to_jaml(value, level + 1, "dict")
                    for key, value in sorted(data.items())
                )
            )
        else:
            result = "{}"
    else:
        raise AnsibleFilterError("This object is not serializable.")
    if nl:
        return "\n" + "  " * level + result
    elif embed_in in ("dict", "list"):
        return " " + result
    elif embed_in == "document":
        if level != 0:
            Display().warning("jaml: Level should be 0 when embedding in 'document'.")
        return result
    else:
        if level != 0:
            Display().warning("jaml: Level should be 0 when serializing a docoment.")
        return "---\n" + result + "\n...\n"


class FilterModule:
    def filters(self) -> t.Dict[str, t.Callable]:
        return {
            "canonical_semver": canonical_semver_filter,
            "jq": jq_filter,
            "repr": repr_filter,
            "jaml": to_jaml,
        }
