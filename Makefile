
# Makefile to build the .deb archive

BUILD_DIR := .
DOCKER_IMAGE := ros_observer-deb-builder
OUTPUT_DIR := /build

.PHONY: build

build:
	cd trace_compass && make build
	mkdir -p $(BUILD_DIR)
	docker build -t $(DOCKER_IMAGE) .
	docker run --rm -v $(BUILD_DIR):$(OUTPUT_DIR) $(DOCKER_IMAGE)
	docker cp $$(docker create --rm ${DOCKER_IMAGE}):${OUTPUT_DIR}/ "${BUILD_DIR}"



.PHONY: install
install: _install clean

.PHONY: _install
_install:
	python3 setup.py install

.PHONY: clean
clean:
	cd trace_compass && make clean
	rm -rf ros2tools.egg-info build  dist ros2tools/__pycache__ 
	rm -rf build
	docker rmi ${DOCKER_IMAGE} --force || true

