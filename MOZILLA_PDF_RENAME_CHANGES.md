# Mozilla PDF 重命名和错误检测功能修改说明

## 问题描述
1. 每次URL运行后，Firefox会在运行根目录生成一个名为`mozilla.pdf`的文件，但每次运行都会覆盖之前的文件
2. 需要简化文件命名格式
3. 需要检测和特殊处理错误页面（如Page Not Found）

## 解决方案
修改了`auto_operation_down_drugs_com_firefox.py`脚本，实现以下功能：

### 1. 主要修改内容

#### A. 新增函数类型导入
```python
from typing import List, Optional, Tuple, Dict
```

#### B. 修改Excel读取函数
- 原函数：`get_drugs_com_links(excel_path: str) -> List[str]`
- 新函数：`get_drugs_com_links_with_ids(excel_path: str) -> List[Dict]`

新函数会：
- 自动检测ID列（支持 'id', 'ID', 'Id', 'index', 'Index'）
- 如果没有ID列，会自动生成序号作为ID
- 返回包含ID和链接的字典列表

#### C. 新增错误页面检测函数
```python
def check_page_for_errors(driver: webdriver.Firefox) -> bool
```

此函数会：
- 检查页面标题和内容
- 识别常见错误指示符（如"Page Not Found", "404", "Error"等）
- 返回布尔值表示是否为错误页面

#### D. 修改文件重命名函数
```python
def move_and_rename_mozilla_pdf(source_dir: str, target_dir: str, record_id: str, is_error_page: bool = False) -> bool
```

此函数会：
- 查找生成的`mozilla.pdf`文件
- 根据记录ID和错误状态创建新的文件名格式：
  - 正常页面：`{记录ID}.pdf`
  - 错误页面：`{记录ID}_(error).pdf`
- 将文件移动到指定的目标目录

#### E. 修改Firefox驱动设置
- 新增`download_dir`参数到`setup_firefox_driver`函数
- 可以指定PDF下载目录

#### F. 更新主函数逻辑
- 创建新的输出目录：`drugs_com_pdfs_mozilla_renamed`
- 使用新的数据结构处理ID和链接
- 在每个页面加载后检测错误状态
- 根据页面状态决定文件命名方式
- 每次处理URL后，自动重命名并移动`mozilla.pdf`文件

### 2. 新的文件组织结构

```
项目根目录/
├── auto_operation_down_drugs_com_firefox.py  # 修改后的主脚本
├── drugs_com_pdfs_mozilla_renamed/           # 新的PDF输出目录
│   ├── 1539.pdf                             # 正常页面PDF文件
│   ├── 1540_(error).pdf                     # 错误页面PDF文件
│   ├── 1541.pdf
│   └── ...
├── test_mozilla_rename.py                   # 测试脚本
└── MOZILLA_PDF_RENAME_CHANGES.md           # 本说明文档
```

### 3. 使用方法

#### 运行脚本
```bash
# 使用默认Excel文件
python auto_operation_down_drugs_com_firefox.py

# 指定Excel文件
python auto_operation_down_drugs_com_firefox.py your_excel_file.xlsx

# 无头模式运行
python auto_operation_down_drugs_com_firefox.py --headless
```

#### 输出说明
- PDF文件会保存在`drugs_com_pdfs_mozilla_renamed`文件夹中
- 文件命名格式：
  - 正常页面：`{Excel中的ID}.pdf`（如：`1539.pdf`）
  - 错误页面：`{Excel中的ID}_(error).pdf`（如：`1540_(error).pdf`）
- 每个文件都有唯一的名称，不会相互覆盖

### 4. 测试验证

可以运行测试脚本验证功能：
```bash
python test_mozilla_rename.py
```

测试内容包括：
- Excel文件读取功能
- 文件重命名功能（正常和错误页面）
- 错误页面检测功能

### 5. 主要优势

1. **防止文件覆盖**：每个PDF文件都有基于ID的唯一名称
2. **简洁命名**：使用简化的`{ID}.pdf`格式，易于识别
3. **智能错误处理**：自动检测并标记错误页面
4. **易于管理**：所有PDF文件集中在专门的目录中
5. **可追溯性**：文件名直接对应Excel中的记录ID
6. **错误页面识别**：`_(error)`后缀清楚标示问题页面
7. **向后兼容**：保持原有的命令行参数和基本功能

### 6. 错误检测机制

脚本会自动检测以下错误指示符：
- 页面标题中的："page not found", "404", "error"等
- 页面内容中的："page not found", "not found", "invalid url", "broken link"等

### 7. 注意事项

1. 确保Excel文件包含ID列或者接受自动生成的序号ID
2. 确保有足够的磁盘空间存储PDF文件
3. Firefox需要正确配置打印设置以生成`mozilla.pdf`文件
4. 脚本会在每次处理URL后等待5秒以确保PDF生成完成
5. 错误页面也会被保存为PDF，便于后续检查和处理

### 8. 依赖库要求

```bash
pip install pandas openpyxl selenium
```

确保安装了geckodriver：
```bash
# macOS
brew install geckodriver

# 或从官网下载
# https://github.com/mozilla/geckodriver/releases
```
