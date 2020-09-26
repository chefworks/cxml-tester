AUTO_FIX_IMPORTS ?= 0

PORT ?= 8080

ifneq ($(AUTO_FIX_IMPORTS), 1)
  autofix = --check-only
endif

test: static

initenv:
	pip3 install --upgrade pip
	pip install pipenv
	pipenv sync

static: imports flake8 pylint


flake8:
	pipenv run flake8 p6t util

pylint:
	pipenv run pylint p6t util -E

imports:
	pipenv run isort -rc $(autofix) p6t util

test-clean:
	rm -f tests/*.sqlite

export RUN_MODE = development

run-flask:
	pipenv run python flask run --host=0.0.0.0 --port=$(PORT)

run-flask-prod:
	$(MAKE) run-flask RUN_MODE=production

DOCKER_PUSH = 0
#DOCKER_IMG_TAG = docker-hub.chefworks.com/erp-webapi
DOCKER_IMG_TAG = docker.chefworks.cloud/cxml-tester
DOCKER_IMG_VERSION = v1.0

docker:
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

.PHONY: docker

