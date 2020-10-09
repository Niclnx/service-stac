SHELL = /bin/bash

.DEFAULT_GOAL := help

SERVICE_NAME := service-stac

CURRENT_DIR := $(shell pwd)
VENV := $(CURRENT_DIR)/.venv
REQUIREMENTS = $(CURRENT_DIR)/requirements.txt
REQUIREMENTS_DEV = $(CURRENT_DIR)/requirements_dev.txt

# Django specific
# DJANGO_PROJECT := app
# DJANGO_PROJECT_DIR := $(CURRENT_DIR)/$(DJANGO_PROJECT)
# DJANGO_CONFIG_DIR := $(DJANGO_PROJECT_DIR)/config

# Test report
TEST_DIR := $(CURRENT_DIR)/tests
TEST_REPORT_DIR ?= $(TEST_DIR)/report
TEST_REPORT_FILE ?= nose2-junit.xml
TEST_REPORT_PATH := $(TEST_REPORT_DIR)/$(TEST_REPORT_FILE)

# Python local build directory
# PYTHON_LOCAL_DIR := $(CURRENT_DIR)/.local

# venv targets timestamps
# VENV_TIMESTAMP = $(VENV)/.timestamp
# REQUIREMENTS_TIMESTAMP = $(VENV)/.requirements.timestamp
# REQUIREMENTS_DEV_TIMESTAMP = $(VENV)/.dev-requirements.timestamp

# general targets timestamps
# TIMESTAMPS = .timestamps
# SYSTEM_PYTHON_TIMESTAMP = $(TIMESTAMPS)/.python-system.timestamp
# PYTHON_LOCAL_BUILD_TIMESTAMP = $(TIMESTAMPS)/.python-build.timestamp
# DOCKER_BUILD_TIMESTAMP = $(TIMESTAMPS)/.dockerbuild.timestamp

# Docker variables
DOCKER_IMG_LOCAL_TAG = swisstopo/$(SERVICE_NAME):local

# Find all python files that are not inside a hidden directory (directory starting with .)
PYTHON_FILES := $(shell find ./app ${TEST_DIR} -type f -name "*.py" -print)

# PROJECT_FILES := $(shell find ./app -type f -print)

PYTHON_VERSION := 3.6
SYSTEM_PYTHON := $(shell ./getPythonCmd.sh ${PYTHON_VERSION} ${PYTHON_LOCAL_DIR})
ifeq ($(SYSTEM_PYTHON),)
$(error "No matching python version found on system, minimum $(PYTHON_VERSION) required")
endif

# default configuration
ENV ?= dev
HTTP_PORT ?= 5000
DEBUG ?= 1
LOGGING_CFG ?= logging-cfg-local.yml
LOGGING_CFG_PATH := $(DJANGO_CONFIG_DIR)/$(LOGGING_CFG)

# Commands
DJANGO_MANAGER := $(DJANGO_PROJECT_DIR)/manage.py
GUNICORN := $(VENV)/bin/gunicorn
PYTHON := $(VENV)/bin/python3
PIP := $(VENV)/bin/pip3
FLASK := $(VENV)/bin/flask
YAPF := $(VENV)/bin/yapf
ISORT := $(VENV)/bin/isort
NOSE := $(VENV)/bin/nose2
PYLINT := $(VENV)/bin/pylint

# Set summon only if not already set, this allow to disable summon on environment
# that don't use it like for CodeBuild env
SUMMON ?= summon --up -p gopass -e service-stac-$(ENV)


all: help


.PHONY: help
help:
	@echo "Usage: make <target>"
	@echo
	@echo "Possible targets:"
	# @echo -e " \033[1mSETUP TARGETS\033[0m "
	@echo "- setup              Create the python virtual environment and install requirements"
	# @echo "- dev                Create the python virtual environment with developper tools"
	# @echo -e " \033[1mFORMATING, LINTING AND TESTING TOOLS TARGETS\033[0m "
	@echo "- format             Format the python source code"
	@echo "- lint               Lint the python source code"
	# @echo "- format-lint        Format and lint the python source code"
	# @echo "- test               Run the tests"
	@echo -e " \033[1mLOCAL SERVER TARGETS\033[0m "
	@echo "- serve              Run the project using the flask debug server. Port can be set by Env variable HTTP_PORT (default: 5000)"
	@echo "- gunicornserve      Run the project using the gunicorn WSGI server. Port can be set by Env variable DEBUG_HTTP_PORT (default: 5000)"
	@echo -e " \033[1mDOCKER TARGETS\033[0m "
	@echo "- dockerbuild        Build the project localy (with tag := $(DOCKER_IMG_LOCAL_TAG)) using the gunicorn WSGI server inside a container"
	@echo "- dockerpush         Build and push the project localy (with tag := $(DOCKER_IMG_LOCAL_TAG))"
	@echo "- dockerrun          Run the project using the gunicorn WSGI server inside a container (exposed port: 5000)"
	@echo "- shutdown           Stop the aforementioned container"
	@echo -e " \033[1mCLEANING TARGETS\033[0m "
	@echo "- clean              Clean genereated files"
	@echo "- clean_venv         Clean python venv"
	# @echo -e " \033[1mDJANGO TARGETS\033[0m "
	# @echo "- django-check       Inspect the Django project for common problems"
	# @echo "- django-migrate     Synchronize the database state with the current set of models and migrations"


# Build targets. Calling setup is all that is needed for the local files to be installed as needed.

# .PHONY: dev
# dev: $(REQUIREMENTS_DEV_TIMESTAMP)


.PHONY: setup
setup:
	test -d $(VENV) || ( $(SYSTEM_PYTHON) -m venv $(VENV) && $(PIP) install --upgrade pip setuptools; \
	$(PIP) install -U pip wheel; \
	$(PIP) install -r $(REQUIREMENTS_DEV); )
	test -d app/config/settings.py || echo "from .settings_dev import *" > app/config/settings.py

# linting target, calls upon yapf to make sure your code is easier to read and respects some conventions.

.PHONY: format
format: # $(REQUIREMENTS_DEV_TIMESTAMP)
	$(YAPF) -p -i --style .style.yapf $(PYTHON_FILES)
	$(ISORT) $(PYTHON_FILES)


.PHONY: lint
# lint: $(REQUIREMENTS_DEV_TIMESTAMP) django-check
lint:
	@echo "Run pylint..."
	$(PYLINT) $(PYTHON_FILES)


# Test target

.PHONY: test
test:
	mkdir -p $(TEST_REPORT_DIR)
	$(PYTHON) $(DJANGO_MANAGER) test


# Serve targets. Using these will run the application on your local machine. You can either serve with a wsgi front (like it would be within the container), or without.

# .PHONY: serve
# serve: $(REQUIREMENTS_TIMESTAMP)
# 	LOGGING_CFG=$(LOGGING_CFG_PATH) DEBUG=$(DEBUG) $(SUMMON) $(PYTHON) $(DJANGO_MANAGER) runserver $(HTTP_PORT)


# .PHONY: gunicornserve
# gunicornserve: $(REQUIREMENTS_TIMESTAMP)
# 	#$(GUNICORN) --chdir $(DJANGO_PROJECT_DIR) $(DJANGO_PROJECT).wsgi
# 	LOGGING_CFG=$(LOGGING_CFG_PATH) DEBUG=$(DEBUG) $(SUMMON) $(PYTHON) $(DJANGO_PROJECT_DIR)/wsgi.py


# Docker related functions.

.PHONY: build-test
build-test:
	docker build -t swisstopo/$(SERVICE_NAME)-test --target test .

.PHONY: build-production
	docker build -t swisstopo/$(SERVICE_NAME) --target production .

# .PHONY: dockerbuild
# dockerbuild: $(DOCKER_BUILD_TIMESTAMP)


# .PHONY: dockerpush
# dockerpush: $(DOCKER_BUILD_TIMESTAMP)
# 	docker push $(DOCKER_IMG_LOCAL_TAG)


# .PHONY: dockerrun
# dockerrun: $(DOCKER_BUILD_TIMESTAMP)
# 	@echo "Listening on port $(HTTP_PORT)"
# 	LOGGING_CFG=./config/$(LOGGING_CFG) HTTP_PORT=$(HTTP_PORT) $(SUMMON) docker-compose up


# .PHONY: shutdown
# shutdown:
# 	HTTP_PORT=$(HTTP_PORT) docker-compose down


# clean targets

.PHONY: clean_venv
clean_venv:
	rm -rf $(VENV)


.PHONY: clean
clean: clean_venv
	@# clean python cache files
	find . -name __pycache__ -type d -print0 | xargs -I {} -0 rm -rf "{}"
	rm -rf $(PYTHON_LOCAL_DIR)
	rm -rf $(TEST_REPORT_DIR)
	rm -rf $(TIMESTAMPS)


# django targets

# .PHONY: django-check
# django-check: $(REQUIREMENTS)
# 	@echo "Run django check"
# 	$(PYTHON) $(DJANGO_MANAGER) check --fail-level WARNING


# .PHONY: django-migrate
# django-migrate: $(REQUIREMENTS)
# 	$(SUMMON) $(PYTHON) $(DJANGO_MANAGER) migrate


# Actual builds targets with dependencies

# $(TIMESTAMPS):
# 	mkdir -p $(TIMESTAMPS)

# $(VENV_TIMESTAMP): $(SYSTEM_PYTHON_TIMESTAMP)
# 	test -d $(VENV) || $(SYSTEM_PYTHON) -m venv $(VENV) && $(PIP) install --upgrade pip setuptools
# 	@touch $(VENV_TIMESTAMP)


# $(REQUIREMENTS_TIMESTAMP): $(VENV_TIMESTAMP) $(REQUIREMENTS)
# 	$(PIP) install -U pip wheel; \
# 	$(PIP) install -r $(REQUIREMENTS);
# 	@touch $(REQUIREMENTS_TIMESTAMP)


# $(REQUIREMENTS_DEV_TIMESTAMP): $(REQUIREMENTS_TIMESTAMP) $(REQUIREMENTS_DEV)
# 	$(PIP) install -r $(REQUIREMENTS_DEV)
# 	@touch $(REQUIREMENTS_DEV_TIMESTAMP)


# $(DOCKER_BUILD_TIMESTAMP): $(TIMESTAMPS) $(PROJECT_FILES) $(CURRENT_DIR)/Dockerfile
# 	docker build -t $(DOCKER_IMG_LOCAL_TAG) .
# 	touch $(DOCKER_BUILD_TIMESTAMP)


# $(TEST_REPORT_DIR):
# 	mkdir -p $(TEST_REPORT_DIR)


# Python local build target

# ifneq ($(SYSTEM_PYTHON),)

# # A system python matching version has been found use it
# $(SYSTEM_PYTHON_TIMESTAMP): $(TIMESTAMPS)
# 	@echo "Using system" $(shell $(SYSTEM_PYTHON) --version 2>&1)
# 	touch $(SYSTEM_PYTHON_TIMESTAMP)


# else

# No python version found, build it localy
# $(SYSTEM_PYTHON_TIMESTAMP): $(TIMESTAMPS) $(PYTHON_LOCAL_BUILD_TIMESTAMP)
# 	@echo "Using local" $(shell $(SYSTEM_PYTHON) --version 2>&1)
# 	touch $(SYSTEM_PYTHON_TIMESTAMP)


# $(PYTHON_LOCAL_BUILD_TIMESTAMP): $(TIMESTAMPS)
# 	@echo "Building a local python..."
# 	mkdir -p $(PYTHON_LOCAL_DIR);
# 	curl -z $(PYTHON_LOCAL_DIR)/Python-$(PYTHON_VERSION).tar.xz https://www.python.org/ftp/python/$(PYTHON_VERSION)/Python-$(PYTHON_VERSION).tar.xz -o $(PYTHON_LOCAL_DIR)/Python-$(PYTHON_VERSION).tar.xz;
# 	cd $(PYTHON_LOCAL_DIR) && tar -xf Python-$(PYTHON_VERSION).tar.xz && Python-$(PYTHON_VERSION)/configure --prefix=$(PYTHON_LOCAL_DIR)/ && make altinstall
# 	touch $(PYTHON_LOCAL_BUILD_TIMESTAMP)

# SYSTEM_PYTHON := $(PYTHON_LOCAL_DIR)/python

# endif

