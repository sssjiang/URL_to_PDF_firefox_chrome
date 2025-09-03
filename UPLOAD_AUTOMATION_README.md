# AITEP文件上传自动化脚本

这个脚本可以自动读取指定目录中的PDF文件，并将它们上传到AITEP网站。

## 功能特性

- 自动读取`/Users/zelinjiang/Downloads/journal`目录中的PDF文件
- 根据文件名提取ID（格式：`id.pdf`，如`1526.pdf`）
- 使用Chrome浏览器自动化打开对应的AITEP网页
- 自动点击上传按钮，选择文件并上传
- 支持错误重试和备用选择器
- 生成详细的日志文件
- 支持headless模式（后台运行）

## 安装要求

### 1. 安装Python依赖

```bash
pip install -r requirements.txt
```

### 2. 安装Chrome和ChromeDriver

**macOS (使用Homebrew):**
```bash
brew install --cask google-chrome
brew install chromedriver
```

**或者手动安装ChromeDriver:**
1. 下载ChromeDriver: https://chromedriver.chromium.org/
2. 将chromedriver放到PATH中（如`/usr/local/bin/`）

## 使用方法

### 基本用法

```bash
python3 auto_upload.py
```

### 后台运行（headless模式）

```bash
python3 auto_upload.py --headless
```

## 工作流程

脚本会按以下步骤自动执行：

1. **读取文件**: 扫描`/Users/zelinjiang/Downloads/journal`目录
2. **提取ID**: 从文件名中提取数字ID（如`1526.pdf` → `1526`）
3. **打开网页**: 访问`https://aitep.probot.hk/en/APIs/references/{id}`
4. **点击上传按钮**: 查找并点击class为`css-1p3hq3p ant-btn ant-btn-primary ant-btn-sm`的按钮
5. **选择文件**: 点击"Select File"按钮并选择对应的PDF文件
6. **确认上传**: 等待上传完成后点击"OK"按钮
7. **记录结果**: 在日志文件中记录成功/失败状态

## 文件结构

```
project/
├── auto_upload.py              # 主脚本
├── requirements.txt            # Python依赖
├── UPLOAD_AUTOMATION_README.md # 说明文档
└── upload_log_YYYYMMDD_HHMMSS.txt  # 自动生成的日志文件
```

## 日志文件

脚本会自动创建带时间戳的日志文件，包含：
- 每个文件的处理状态
- 错误信息和调试详情
- 最终的成功/失败统计

日志文件格式：`upload_log_20241203_143022.txt`

## 错误处理

脚本包含多层错误处理机制：

1. **备用选择器**: 如果主要的CSS选择器失败，会尝试备用选择器
2. **自动重试**: 对于常见的超时错误会自动重试
3. **详细日志**: 所有错误都会记录到日志文件中
4. **优雅降级**: 即使某些文件失败，脚本也会继续处理其他文件

## 注意事项

1. **文件命名**: 确保PDF文件名格式为`{id}.pdf`，其中`id`是纯数字
2. **网络连接**: 确保有稳定的网络连接
3. **浏览器版本**: 确保Chrome浏览器和ChromeDriver版本匹配
4. **权限**: 确保脚本有读取文件和写入日志的权限
5. **服务器限制**: 脚本在每次上传之间等待3秒，避免过载服务器

## 故障排除

### Chrome Driver问题
```bash
# 检查chromedriver是否在PATH中
which chromedriver

# 检查Chrome版本
google-chrome --version

# 重新安装chromedriver
brew reinstall chromedriver
```

### Selenium问题
```bash
# 重新安装selenium
pip uninstall selenium
pip install selenium>=4.0.0
```

### 文件权限问题
```bash
# 检查目录权限
ls -la /Users/zelinjiang/Downloads/journal/
```

## 自定义配置

如需修改配置，可以编辑`auto_upload.py`中的以下变量：

```python
# 修改PDF文件目录
pdf_directory = "/path/to/your/pdf/directory"

# 修改等待时间（秒）
timeout = 30

# 修改上传间隔时间（秒）
time.sleep(3)
```

## 支持

如果遇到问题，请检查：
1. 日志文件中的详细错误信息
2. 确保所有依赖都已正确安装
3. 确保目标网站的HTML结构没有变化
4. 确保PDF文件名格式正确
