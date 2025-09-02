#!/usr/bin/env python3
"""
PNG to PDF Converter
将PNG图片转换为PDF格式的独立工具

功能:
- 单个PNG文件转换为PDF
- 批量处理目录中的所有PNG文件
- 支持自定义输出目录
- 错误处理和日志记录
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List, Optional
import logging

try:
    from PIL import Image
    # 增加PIL的安全限制以处理大图片
    Image.MAX_IMAGE_PIXELS = None  # 移除像素限制
except ImportError:
    print("Error: PIL (Pillow) library is required but not installed.")
    print("Please install it using: pip install Pillow")
    sys.exit(1)


def setup_logging(verbose: bool = False) -> None:
    """设置日志记录"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def convert_png_to_pdf(png_path: str, pdf_path: str) -> bool:
    """
    将单个PNG文件转换为PDF
    
    Args:
        png_path: PNG文件路径
        pdf_path: 输出PDF文件路径
        
    Returns:
        bool: 转换是否成功
    """
    try:
        # 检查PNG文件是否存在
        if not os.path.exists(png_path):
            logging.error(f"PNG文件不存在: {png_path}")
            return False
        
        # 打开PNG图片
        with Image.open(png_path) as img:
            # 确保图片是RGB模式（PDF需要RGB模式）
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 保存为PDF
            img.save(pdf_path, 'PDF', resolution=300.0, quality=95)
            logging.info(f"成功转换: {png_path} -> {pdf_path}")
            return True
            
    except Exception as e:
        logging.error(f"转换失败 {png_path}: {e}")
        return False


def batch_convert_png_to_pdf(input_dir: str, output_dir: Optional[str] = None) -> dict:
    """
    批量转换目录中的所有PNG文件为PDF
    
    Args:
        input_dir: 包含PNG文件的输入目录
        output_dir: 输出目录，如果为None则使用输入目录
        
    Returns:
        dict: 转换结果统计
    """
    input_path = Path(input_dir)
    
    if not input_path.exists():
        logging.error(f"输入目录不存在: {input_dir}")
        return {"success": 0, "failed": 0, "total": 0}
    
    # 设置输出目录
    if output_dir is None:
        output_path = input_path
    else:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
    
    # 查找所有PNG文件
    png_files = list(input_path.glob("*.png"))
    
    if not png_files:
        logging.warning(f"在目录 {input_dir} 中未找到PNG文件")
        return {"success": 0, "failed": 0, "total": 0}
    
    logging.info(f"找到 {len(png_files)} 个PNG文件")
    
    success_count = 0
    failed_count = 0
    
    for png_file in png_files:
        # 生成对应的PDF文件名
        pdf_filename = png_file.stem + ".pdf"
        pdf_path = output_path / pdf_filename
        
        # 转换文件
        if convert_png_to_pdf(str(png_file), str(pdf_path)):
            success_count += 1
        else:
            failed_count += 1
    
    return {
        "success": success_count,
        "failed": failed_count,
        "total": len(png_files)
    }


def process_drugs_com_pngs(workspace_dir: Optional[str] = None) -> None:
    """
    专门处理drugs_com_pdfs目录中的PNG文件
    
    Args:
        workspace_dir: 工作目录路径，如果为None则使用当前脚本所在目录
    """
    if workspace_dir is None:
        workspace_dir = Path(__file__).resolve().parent
    else:
        workspace_dir = Path(workspace_dir)
    
    # 查找drugs_com_pdfs目录
    drugs_dir = workspace_dir / "drugs_com_pdfs"
    
    if not drugs_dir.exists():
        logging.error(f"未找到drugs_com_pdfs目录: {drugs_dir}")
        return
    
    logging.info(f"处理目录: {drugs_dir}")
    
    # 批量转换
    result = batch_convert_png_to_pdf(str(drugs_dir))
    
    # 输出结果
    print(f"\n转换完成!")
    print(f"总计: {result['total']} 个文件")
    print(f"成功: {result['success']} 个")
    print(f"失败: {result['failed']} 个")
    
    if result['failed'] > 0:
        print(f"请检查日志了解失败原因")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="PNG to PDF Converter - 将PNG图片转换为PDF格式",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 转换单个文件
  python png_to_pdf_converter.py -i image.png -o output.pdf
  
  # 批量转换目录中的所有PNG文件
  python png_to_pdf_converter.py -d /path/to/png/directory
  
  # 批量转换并指定输出目录
  python png_to_pdf_converter.py -d /path/to/png/directory -o /path/to/pdf/directory
  
  # 处理drugs_com_pdfs目录（默认行为）
  python png_to_pdf_converter.py --drugs-com
  
  # 详细输出
  python png_to_pdf_converter.py --drugs-com -v
        """
    )
    
    # 参数组
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        '-i', '--input',
        help='输入PNG文件路径'
    )
    input_group.add_argument(
        '-d', '--directory',
        help='包含PNG文件的目录路径'
    )
    input_group.add_argument(
        '--drugs-com',
        action='store_true',
        help='处理drugs_com_pdfs目录中的PNG文件'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='输出PDF文件路径或目录路径'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='详细输出'
    )
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(args.verbose)
    
    try:
        if args.drugs_com:
            # 处理drugs_com_pdfs目录
            process_drugs_com_pngs()
            
        elif args.directory:
            # 批量转换目录
            if args.output and os.path.isfile(args.output):
                logging.error("当使用目录模式时，输出参数应该是目录路径，不是文件路径")
                sys.exit(1)
            
            result = batch_convert_png_to_pdf(args.directory, args.output)
            
            print(f"\n转换完成!")
            print(f"总计: {result['total']} 个文件")
            print(f"成功: {result['success']} 个")
            print(f"失败: {result['failed']} 个")
            
        else:
            # 单个文件转换
            if not args.output:
                # 如果没有指定输出路径，使用相同的文件名但扩展名为.pdf
                input_path = Path(args.input)
                args.output = str(input_path.with_suffix('.pdf'))
            
            success = convert_png_to_pdf(args.input, args.output)
            
            if success:
                print(f"✓ 成功转换: {args.input} -> {args.output}")
            else:
                print(f"✗ 转换失败: {args.input}")
                sys.exit(1)
                
    except KeyboardInterrupt:
        print("\n用户中断操作")
        sys.exit(1)
    except Exception as e:
        logging.error(f"程序执行出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
