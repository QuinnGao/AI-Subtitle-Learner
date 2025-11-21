# PowerShell 脚本：在 Docker 容器中运行测试

param(
    [Parameter(Position=0)]
    [ValidateSet("subtitle", "all", "coverage")]
    [string]$TestType = "subtitle"
)

Write-Host "========================================" -ForegroundColor Green
Write-Host "  运行 Docker 测试" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

# 创建测试结果目录
New-Item -ItemType Directory -Force -Path "test-results" | Out-Null
New-Item -ItemType Directory -Force -Path "htmlcov" | Out-Null

switch ($TestType) {
    "subtitle" {
        Write-Host "运行字幕接口测试..." -ForegroundColor Yellow
        docker-compose -f docker-compose.test.yml run --rm test
    }
    "all" {
        Write-Host "运行所有测试..." -ForegroundColor Yellow
        docker-compose -f docker-compose.test.yml run --rm test-all
    }
    "coverage" {
        Write-Host "运行测试并生成覆盖率报告..." -ForegroundColor Yellow
        docker-compose -f docker-compose.test.yml run --rm test-coverage
        Write-Host "覆盖率报告已生成在 htmlcov/index.html" -ForegroundColor Green
    }
}

Write-Host "========================================" -ForegroundColor Green
Write-Host "  测试完成" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

