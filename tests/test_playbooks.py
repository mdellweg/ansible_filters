import pytest
import os
import sys
import json
import ansible_runner


TEST_NAMES = [
    name[:-5] for name in os.listdir("tests/playbooks") if name.endswith(".yaml")
]


# Clean environment from anything that could cause encoding problems
if sys.version_info[0] == 2:
    for envvar in os.environ.keys():
        try:
            os.environ[envvar] = (
                os.environ[envvar].decode("utf-8").encode("ascii", "ignore")
            )
        except UnicodeError:
            os.environ.pop(envvar)


def run_playbook(playbook, extra_vars=None, limit=None, check_mode=False):
    # Assemble parameters for playbook call
    os.environ["ANSIBLE_CONFIG"] = os.path.join(os.getcwd(), "ansible.cfg")
    kwargs = {}
    kwargs["playbook"] = os.path.join(os.getcwd(), "tests", "playbooks", playbook)
    kwargs["inventory"] = "localhost,"
    kwargs["verbosity"] = 4
    if extra_vars:
        kwargs["extravars"] = extra_vars
    if limit:
        kwargs["limit"] = limit
    if check_mode:
        kwargs["cmdline"] = "--check"
    return ansible_runner.run(**kwargs)


@pytest.mark.parametrize("test_name", TEST_NAMES)
def test_playbook(test_name):
    playbook = test_name + ".yaml"
    run = run_playbook(playbook)
    assert run.rc == 0
