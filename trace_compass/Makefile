SHELL:=/bin/bash

.DEFAULT_GOAL := all

ROOT_DIR:=$(shell dirname "$(realpath $(firstword $(MAKEFILE_LIST)))")

MAKEFLAGS += --no-print-directory

.EXPORT_ALL_VARIABLES:
ROS_HOME?=${ROOT_DIR}/.ros
TRACING_LOG_DIRECTORY=${ROS_HOME}/tracing
DOCKER_BUILDKIT?=1
DOCKER_CONFIG?=

PROJECT:=trace_compass
TAG:=$(shell git rev-parse --short HEAD 2>/dev/null || echo "latest")
IMAGE:=${PROJECT}:${TAG}


USER := $(shell whoami)
UID := $(shell id -u)
GID := $(shell id -g)

.PHONY: help
help:
	@printf "Usage: make \033[36m<target>\033[0m\n%s\n" "$$(awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z0-9_-]+:.*?##/ { gsub(/\\$$/, "", $$2); printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) }' $(MAKEFILE_LIST) | sort | uniq | sed 's/\$$//' | sed 's/\\$$//' )"

.PHONY: build
build: ## Build the Trace Compass Docker context
	docker build . -t ${PROJECT}:${TAG} -f Dockerfile

.PHONY: clean
clean: ## Clean all build artificats including docker context
	rm -rf .log
	docker rmi --force ${PROJECT}:${TAG} > /dev/null 2>&1 || true

.PHONY: start
start: ## Start Trace Compass 
	@echo "Starting Trace Compass..."
	mkdir -p ${TRACING_LOG_DIRECTORY}
	docker stop -f ${PROJECT} > /dev/null 2>&1 || true
	docker rm -f ${PROJECT} > /dev/null 2>&1 || true
	xhost +local:docker
	docker run \
               -d \
               --rm \
               -e DISPLAY=$$DISPLAY \
               -v ${TRACING_LOG_DIRECTORY}:/opt/trace-compass/tracing_logs \
               -v /tmp/.X11-unix:/tmp/.X11-unix \
               --network host \
			   --name ${PROJECT} ${PROJECT}:${TAG}
	@echo "Trace Compass started..."

.PHONY: stop
stop:  ## Stop Trace Compass
	@echo "Stoping Trace Compass..."
	docker stop -f ${PROJECT} > /dev/null 2>&1 || true
	docker rm -f ${PROJECT} > /dev/null 2>&1 || true
	@echo "Trace Compass stopped"

