AUTO_FIX_IMPORTS ?= 0

CXML_TESTER_RELEASE = 0.1.1

PORT ?= 8080

ifneq ($(AUTO_FIX_IMPORTS), 1)
  autofix = --check-only
endif

test: static unit

init:
	pip3 install --upgrade pip
	pip install pipenv
	pipenv --python 3.8
	pipenv sync --dev

unit:
	pipenv run python -m pytest

static: imports flake8 pylint


flake8:
	pipenv run flake8 p6t util tests

pylint:
	pipenv run pylint p6t util tests -E

imports:
	pipenv run isort -rc $(autofix) p6t util tests

test-clean:
	rm -f tests/*.sqlite

export RUN_MODE = development

run:
	pipenv run gunicorn --bind :$(PORT) --workers 1 --threads 8 --timeout 0 p6t:app

run-prod:
	$(MAKE) run RUN_MODE=production

DOCKER_IMG_TAG = cxml-tester
DOCKER_IMG_VERSION = v1.0.1

docker:
	pipenv run pip freeze > requirements.txt
	docker build -t $(DOCKER_IMG_TAG):$(DOCKER_IMG_VERSION) .
ifeq ($(DOCKER_PUSH),1)
	docker push $(DOCKER_IMG_TAG):$(DOCKER_IMG_VERSION)
endif

########################## docker run commands ##################################
docker-test: DOCKER_IMG_TEST_NAME = cxml-tester
docker-test:
	-docker rm -f $(DOCKER_IMG_TEST_NAME)
	docker run --rm --name $(DOCKER_IMG_TEST_NAME) $(DOCKER_IMG_TAG):$(DOCKER_IMG_VERSION) bash -c 'pipenv sync --dev; make test'

docker-flask-dev:
	docker run --network="host" -it --rm --name flask-dev \
		$(DOCKER_IMG_TAG):$(DOCKER_IMG_VERSION) \
		make run-flask $(DOCKER_RUN_ARGS)

DOCKER_SERVICE_INSTALL = 0

ifeq ($(DOCKER_SERVICE_INSTALL),1)
	DOCKER_RUN_ARGS = -dit --restart always
else
	DOCKER_RUN_ARGS = -it --rm
endif

# make -n docker-flask-prod DOCKER_SERVICE_INSTALL=1
docker-flask-prod:
	docker pull $(DOCKER_IMG_TAG)
	docker run $(DOCKER_RUN_ARGS) -p 8080:8080 --name flask-prod $(DOCKER_IMG_TAG):$(DOCKER_IMG_VERSION) make run-flask-prod $(DOCKER_RUN_EXTRA_ARGS)

git-tag:
	git tag $(CXML_TESTER_RELEASE)
	git push origin $(CXML_TESTER_RELEASE)

.PHONY: docker

