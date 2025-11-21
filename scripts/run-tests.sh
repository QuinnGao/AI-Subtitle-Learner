#!/bin/bash
# 在 Docker 容器中运行测试

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  运行 Docker 测试${NC}"
echo -e "${GREEN}========================================${NC}"

# 创建测试结果目录
mkdir -p test-results
mkdir -p htmlcov

# 检查参数
TEST_TYPE=${1:-subtitle}

case $TEST_TYPE in
  subtitle)
    echo -e "${YELLOW}运行字幕接口测试...${NC}"
    docker-compose -f docker-compose.test.yml run --rm test
    ;;
  all)
    echo -e "${YELLOW}运行所有测试...${NC}"
    docker-compose -f docker-compose.test.yml run --rm test-all
    ;;
  coverage)
    echo -e "${YELLOW}运行测试并生成覆盖率报告...${NC}"
    docker-compose -f docker-compose.test.yml run --rm test-coverage
    echo -e "${GREEN}覆盖率报告已生成在 htmlcov/index.html${NC}"
    ;;
  *)
    echo -e "${RED}未知的测试类型: $TEST_TYPE${NC}"
    echo "用法: $0 [subtitle|all|coverage]"
    exit 1
    ;;
esac

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  测试完成${NC}"
echo -e "${GREEN}========================================${NC}"

