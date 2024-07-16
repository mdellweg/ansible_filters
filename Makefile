NAMESPACE := $(shell python -c 'import yaml; print(yaml.safe_load(open("galaxy.yml"))["namespace"])')
NAME := $(shell python -c 'import yaml; print(yaml.safe_load(open("galaxy.yml"))["name"])')
VERSION := $(shell python -c 'import yaml; print(yaml.safe_load(open("galaxy.yml"))["version"])')
MANIFEST := build/collections/ansible_collections/$(NAMESPACE)/$(NAME)/MANIFEST.json

ROLES := $(wildcard roles/*)
PLUGIN_TYPES := $(filter-out __%,$(notdir $(wildcard plugins/*)))
METADATA := galaxy.yml LICENSE README.md meta/runtime.yml
$(foreach PLUGIN_TYPE,$(PLUGIN_TYPES),$(eval _$(PLUGIN_TYPE) := $(filter-out %__init__.py,$(wildcard plugins/$(PLUGIN_TYPE)/*.py))))
DEPENDENCIES := $(METADATA) $(foreach PLUGIN_TYPE,$(PLUGIN_TYPES),$(_$(PLUGIN_TYPE))) $(foreach ROLE,$(ROLES),$(wildcard $(ROLE)/*/*)) $(foreach ROLE,$(ROLES),$(ROLE)/README.md)

PYTHON_VERSION = $(shell python -c 'import sys; print("{}.{}".format(sys.version_info.major, sys.version_info.minor))')
SANITY_OPTS =
TEST =
PYTEST = pytest -n 4 -v

default: help
help:
	@echo "Please use \`make <target>' where <target> is one of:"
	@echo "  help             to show this message"
	@echo "  info             to show infos about the collection"
	@echo "  lint             to run code linting"
	@echo "  test             to run unit tests"
	@echo "  sanity           to run santy tests"
	@echo "  setup            to set up test, lint"
	@echo "  test-setup       to install test dependencies"
	@echo "  dist             to build the collection artifact"

info:
	@echo "Building collection $(NAMESPACE)-$(NAME)-$(VERSION)"
	@echo "  roles:\n $(foreach ROLE,$(notdir $(ROLES)),   - $(ROLE)\n)"
	@echo " $(foreach PLUGIN_TYPE,$(PLUGIN_TYPES), $(PLUGIN_TYPE):\n $(foreach PLUGIN,$(basename $(notdir $(_$(PLUGIN_TYPE)))),   - $(PLUGIN)\n)\n)"

format:
	isort .
	black .

lint: $(MANIFEST)
	yamllint -f parsable tests/playbooks
	ansible-playbook --syntax-check tests/playbooks/*.yaml | grep -v '^$$'
	black --check --diff .
	isort -c --diff .
	GALAXY_IMPORTER_CONFIG=tests/galaxy-importer.cfg python -m galaxy_importer.main $(NAMESPACE)-$(NAME)-$(VERSION).tar.gz
	@echo "🙊 Code 🙉 LGTM 🙈"

sanity: $(MANIFEST)
	# Fake a fresh git repo for ansible-test
	cd $(<D) ; git init ; echo tests > .gitignore ; ansible-test sanity $(SANITY_OPTS) --python $(PYTHON_VERSION)

test: $(MANIFEST)
	$(PYTEST) $(TEST)

test_%: FORCE $(MANIFEST)
	pytest -v 'tests/test_playbooks.py::test_playbook[$*]'

test-setup: requirements.txt
	pip install -r requirements.txt

$(MANIFEST): $(NAMESPACE)-$(NAME)-$(VERSION).tar.gz
	ansible-galaxy collection install -p build/collections $< --force

build/src/%: %
	install -m 644 -DT $< $@

$(NAMESPACE)-$(NAME)-$(VERSION).tar.gz: $(addprefix build/src/,$(DEPENDENCIES))
	ansible-galaxy collection build build/src --force

dist: $(NAMESPACE)-$(NAME)-$(VERSION).tar.gz

install: $(MANIFEST)

publish: $(NAMESPACE)-$(NAME)-$(VERSION).tar.gz
	ansible-galaxy collection publish --api-key $(GALAXY_API_KEY) $<

clean:
	rm -rf build importer_result.json

FORCE:

.PHONY: help dist install format lint sanity test test-setup publish FORCE
