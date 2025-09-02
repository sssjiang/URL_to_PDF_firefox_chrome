#!/usr/bin/env python3
"""
测试PNG到PDF转换器的简单脚本
"""

import sys
import os
from pathlib import Path

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

try:
    from png_to_pdf_converter import convert_png_to_pdf, batch_convert_png_to_pdf
    print("✓ 成功导入转换器模块")
except ImportError as e:
    print(f"✗ 导入失败: {e}")
    sys.exit(1)

def test_single_conversion():
    """测试单个文件转换"""
    print("\n=== 测试单个文件转换 ===")
    
    # 查找第一个PNG文件
    drugs_dir = Path("drugs_com_pdfs")
    png_files = list(drugs_dir.glob("*.png"))
    
    if not png_files:
        print("未找到PNG文件进行测试")
        return False
    
    png_file = png_files[0]
    pdf_file = png_file.with_suffix('.pdf')
    
    print(f"测试文件: {png_file}")
    print(f"输出文件: {pdf_file}")
    
    # 执行转换
    success = convert_png_to_pdf(str(png_file), str(pdf_file))
    
    if success:
        print("✓ 单个文件转换测试成功")
        return True
    else:
        print("✗ 单个文件转换测试失败")
        return False

def test_batch_conversion():
    """测试批量转换"""
    print("\n=== 测试批量转换 ===")
    
    # 创建测试输出目录
    test_output_dir = Path("test_pdf_output")
    test_output_dir.mkdir(exist_ok=True)
    
    print(f"测试目录: drugs_com_pdfs")
    print(f"输出目录: {test_output_dir}")
    
    # 执行批量转换
    result = batch_convert_png_to_pdf("drugs_com_pdfs", str(test_output_dir))
    
    print(f"转换结果: {result}")
    
    if result['success'] > 0:
        print("✓ 批量转换测试成功")
        return True
    else:
        print("✗ 批量转换测试失败")
        return False

def main():
    """主测试函数"""
    print("PNG到PDF转换器测试")
    print("=" * 50)
    
    # 检查依赖
    try:
        from PIL import Image
        # 增加PIL的安全限制以处理大图片
        Image.MAX_IMAGE_PIXELS = None  # 移除像素限制
        print("✓ PIL库可用")
    except ImportError:
        print("✗ PIL库不可用，请安装: pip install Pillow")
        return
    
    # 检查测试目录
    if not Path("drugs_com_pdfs").exists():
        print("✗ 测试目录 drugs_com_pdfs 不存在")
        return
    
    # 运行测试
    test1_success = test_single_conversion()
    test2_success = test_batch_conversion()
    
    print("\n" + "=" * 50)
    print("测试总结:")
    print(f"单个文件转换: {'✓ 通过' if test1_success else '✗ 失败'}")
    print(f"批量转换: {'✓ 通过' if test2_success else '✗ 失败'}")
    
    if test1_success and test2_success:
        print("\n🎉 所有测试通过！转换器工作正常。")
    else:
        print("\n❌ 部分测试失败，请检查错误信息。")

if __name__ == "__main__":
    main()
