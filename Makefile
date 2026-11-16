IMAGE   := openchamber-docker
TAG     := local
PORT    := 3000

.DEFAULT_GOAL := help

.PHONY: help
help: ## 📖 Show this help
	@echo "🐳 openchamber-docker — dev tasks"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

.PHONY: build
build: ## 🔨 Build the image locally
	docker build -t $(IMAGE):$(TAG) .

.PHONY: run
run: ## 🚀 Run locally on :3000 against an external OpenCode server
	docker run --rm -it \
		--name $(IMAGE) \
		-p $(PORT):3000 \
		-e OPENCHAMBER_UI_PASSWORD=$${OPENCHAMBER_UI_PASSWORD:-$${UI_PASSWORD:-password}} \
		-e OPENCODE_SKIP_START=$${OPENCODE_SKIP_START:-true} \
		-e OPENCODE_HOST=$${OPENCODE_HOST:-http://host.docker.internal:4096} \
		-e OPENCODE_SERVER_PASSWORD=$${OPENCODE_SERVER_PASSWORD:-$${OPENCODE_PASSWORD:-password}} \
		-v $$(pwd)/workspace:/workspace \
		$(IMAGE):$(TAG)

.PHONY: shell
shell: ## 🐚 Shell into the running container
	docker exec -it $(IMAGE) bash

.PHONY: test
test: ## 🧪 Run the version-bump script's unit tests
	pytest test_update_versions.py

.PHONY: update-versions
update-versions: ## ⬆️  Check npm for newer packages → rewrite Dockerfile + VERSION
	python3 update_versions.py

.PHONY: clean
clean: ## 🧹 Remove local image and Python cache
	docker rmi $(IMAGE):$(TAG) 2>/dev/null || true
	rm -rf __pycache__ .pytest_cache

.PHONY: check-build
check-build: ## 🔍 Check GHCR tag + CI build status (TAG=v2.7.2 to check a specific tag)
	python3 check_build.py $(if $(filter-out local,$(TAG)),$(TAG))
