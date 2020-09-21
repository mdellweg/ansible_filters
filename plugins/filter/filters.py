# Copyright (c) 2020 Matthias Dellweg
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import absolute_import, division, print_function

import jq
from ansible.module_utils import six
from ansible.module_utils._text import to_native, to_text


__metaclass__ = type


def jq_filter(value, filter_expression, all=False):
    """
    Parse input with jq language.
    """
    if all:
        return jq.all(filter_expression, value)
    else:
        return jq.first(filter_expression, value)


def map_to_native(value):
    if isinstance(value, six.string_types):
        return to_native(value)
    if isinstance(value, dict):
        return {map_to_native(key): map_to_native(val) for key, val in value.items()}
    if isinstance(value, list):
        return [map_to_native(val) for val in value]
    return value


def repr_filter(value):
    """
    Convert value into python representation string.
    """
    return to_text(repr(map_to_native(value)))


class FilterModule(object):
    def filters(self):
        return {
            "jq": jq_filter,
            "repr": repr_filter,
        }
