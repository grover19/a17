include common.mk

# Our directories
API_DIR = server
DB_DIR = data
SECURITY_DIR = security
REQ_DIR = .

export PYTHONPATH := $(shell pwd)

PYTESTFLAGS = -vv --verbose --cov-branch --cov-report term-missing --tb=short -W ignore::FutureWarning

FORCE:

prod: all_tests github

github: FORCE
	- git commit -a
	git push origin master

all_tests: FORCE
	$(MAKE) -C $(API_DIR) tests
	$(MAKE) -C $(DB_DIR) tests
	$(MAKE) -C $(SECURITY_DIR) tests

dev_env: FORCE
	pip install -r $(REQ_DIR)/requirements-dev.txt
	@echo "You should set PYTHONPATH to: "
	@echo $(shell pwd)

docs: FORCE
	cd $(API_DIR); make docs
