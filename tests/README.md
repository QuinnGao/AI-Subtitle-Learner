# 测试说明

## 运行测试

### 在 Docker 容器中运行（推荐）

项目提供了 Docker Compose 配置来运行测试，确保测试环境与生产环境一致。

#### 使用脚本运行

**Linux/macOS:**
```bash
# 运行字幕接口测试
./scripts/run-tests.sh subtitle

# 运行所有测试
./scripts/run-tests.sh all

# 运行测试并生成覆盖率报告
./scripts/run-tests.sh coverage
```

**Windows (PowerShell):**
```powershell
# 运行字幕接口测试
.\scripts\run-tests.ps1 subtitle

# 运行所有测试
.\scripts\run-tests.ps1 all

# 运行测试并生成覆盖率报告
.\scripts\run-tests.ps1 coverage
```

#### 直接使用 Docker Compose

```bash
# 运行字幕接口测试
docker-compose -f docker-compose.test.yml run --rm test

# 运行所有测试
docker-compose -f docker-compose.test.yml run --rm test-all

# 运行测试并生成覆盖率报告
docker-compose -f docker-compose.test.yml run --rm test-coverage
```

#### 运行特定测试

```bash
# 运行特定测试类
docker-compose -f docker-compose.test.yml run --rm test pytest tests/test_subtitle.py::TestSubtitleAPI -v

# 运行特定测试方法
docker-compose -f docker-compose.test.yml run --rm test pytest tests/test_subtitle.py::TestSubtitleAPI::test_create_subtitle_task_success -v
```

#### 查看测试结果

测试结果会保存在 `test-results/` 目录，覆盖率报告会保存在 `htmlcov/` 目录。

### 本地运行（不使用 Docker）

#### 使用 pytest

```bash
# 安装测试依赖
pip install -r requirements.txt

# 运行所有测试
pytest

# 运行字幕接口测试
pytest tests/test_subtitle.py -v

# 运行特定测试
pytest tests/test_subtitle.py::TestSubtitleAPI::test_create_subtitle_task_success -v

# 查看测试覆盖率
pytest --cov=app --cov-report=html tests/
```

#### 使用 uv

```bash
# 运行测试
uv run pytest tests/test_subtitle.py -v
```

## 测试覆盖范围

### 字幕接口测试 (`test_subtitle.py`)

#### 基础功能测试
- ✅ 创建字幕处理任务（成功场景）
- ✅ 创建字幕处理任务（无效文件）
- ✅ 创建字幕处理任务（完整配置）
- ✅ 获取任务状态
- ✅ 获取不存在的任务
- ✅ 下载任务结果
- ✅ 下载未完成的任务

#### 功能配置测试
- ✅ 不同的字幕布局（4种布局）
- ✅ 不同的翻译服务（OpenAI, DeepLX, Bing, Google）
- ✅ 启用优化功能
- ✅ 启用分割功能
- ✅ 启用反思翻译功能
- ✅ 自定义提示词
- ✅ 最大字数配置
- ✅ 字幕样式配置
- ✅ 目标语言配置
- ✅ 线程数和批处理大小配置

#### 文件格式测试
- ✅ SRT 格式
- ✅ ASS 格式
- ✅ VTT 格式

#### 高级功能测试
- ✅ 任务进度更新
- ✅ 任务状态转换
- ✅ 完整工作流测试
- ✅ 并发请求测试
- ✅ 错误处理测试
- ✅ 自定义输出路径
- ✅ 提供视频路径
- ✅ DeepLX 端点配置

#### 验证测试
- ✅ 请求参数验证
- ✅ 配置参数验证
- ✅ 响应字段完整性验证

## 测试 Fixtures

### `client`
FastAPI 测试客户端，用于发送 HTTP 请求

### `temp_dir`
临时目录，用于存储测试文件

### `sample_srt_file`
示例 SRT 字幕文件

### `sample_ass_file`
示例 ASS 字幕文件

### `sample_vtt_file`
示例 VTT 字幕文件

### `sample_srt_file_not_exist`
不存在的文件路径（用于错误测试）

## 测试注意事项

1. **异步任务处理**：某些测试需要等待后台任务完成，使用了 `time.sleep()` 进行轮询
2. **文件路径**：测试使用临时目录，确保不会影响实际文件
3. **并发测试**：使用 `ThreadPoolExecutor` 测试并发请求
4. **错误场景**：测试覆盖了各种错误情况，如文件不存在、任务未完成等

## 持续集成

测试可以在 CI/CD 流程中运行：

```yaml
# GitHub Actions 示例
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest tests/ -v --cov=app --cov-report=xml
```
