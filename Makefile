.PHONY: test test-subtitle test-all test-coverage help

help:
	@echo "可用的测试命令:"
	@echo "  make test-subtitle  - 运行字幕接口测试"
	@echo "  make test-all       - 运行所有测试"
	@echo "  make test-coverage  - 运行测试并生成覆盖率报告"
	@echo "  make test           - 运行字幕接口测试（默认）"

test: test-subtitle

test-subtitle:
	@echo "运行字幕接口测试..."
	docker-compose -f docker-compose.test.yml run --rm test

test-all:
	@echo "运行所有测试..."
	docker-compose -f docker-compose.test.yml run --rm test-all

test-coverage:
	@echo "运行测试并生成覆盖率报告..."
	docker-compose -f docker-compose.test.yml run --rm test-coverage
	@echo "覆盖率报告已生成在 htmlcov/index.html"

clean:
	@echo "清理测试结果..."
	rm -rf test-results htmlcov .pytest_cache .coverage

