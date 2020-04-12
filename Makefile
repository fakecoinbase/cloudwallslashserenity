# all our targets are phony (no files to check).
.PHONY: help build rebuild prune

BUILD_TAG=`date --rfc-3339=date`-1

# Regular Makefile part for buildpypi itself
help:
	@echo ''
	@echo 'Usage: make [TARGET] [EXTRA_ARGUMENTS]'
	@echo 'Targets:'
	@echo '  build    	build Docker image'
	@echo '  prune    	shortcut for docker system prune -af; cleans up inactive containers and cache'
	@echo ''

build:
	docker build --no-cache -t cloudwallcapital/serenity:$BUILD_TAG .

push:
	docker push cloudwallcapital/serenity:$BUILD_TAG

prune:
	# clean all that is not actively used
	docker system prune -af
