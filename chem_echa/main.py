#!/usr/bin/env python3
"""
ECHA Chemical Data Pipeline
整合调用search_page->dosser_list->dosser_detail->extract_toxicological_structure
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, Optional, List

# 导入自定义模块
from search_page import search_substance_rml_id
from dosser_list import get_dosser_asset_external_id
from dosser_detail import get_dosser_detail_html
from extract_toxicological_structure import ToxicologicalExtractor
from extract_json_link_detail import get_document_detail


class ECHADataPipeline:
    """ECHA化学数据获取管道"""
    
    def __init__(self, verbose: bool = True, save_files: bool = True):
        """
        初始化管道
        
        Args:
            verbose (bool): 是否打印详细信息
            save_files (bool): 是否保存中间文件
        """
        self.verbose = verbose
        self.save_files = save_files
        self.results = {}
    
    def run_pipeline(self, search_text: str, extract_output_file: str = None) -> Dict[str, Any]:
        """
        运行完整的数据获取管道
        
        Args:
            search_text (str): 搜索文本（CAS号、物质名称等）
            extract_output_file (str, optional): 毒理学结构提取结果的输出文件名
        
        Returns:
            dict: 包含所有步骤结果的字典
        """
        if self.verbose:
            print(f"=== ECHA数据获取管道开始 ===")
            print(f"搜索文本: {search_text}")
            print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print()
        
        pipeline_result = {
            'search_text': search_text,
            'timestamp': datetime.now().isoformat(),
            'step1_search': None,
            'step2_dosser_list': None,
            'step3_dosser_detail': None,
            'step4_toxicological_structure': None,
            'step5_extract_documents': None,
            'success': False,
            'error_message': None
        }
        
        try:
            # 步骤1: 搜索物质获取rmlId
            rml_id = self._step1_search_substance(search_text, pipeline_result)
            if not rml_id:
                return pipeline_result
            
            # 步骤2: 获取dosser的assetExternalId
            asset_external_id = self._step2_get_dosser_asset_id(rml_id, pipeline_result)
            if not asset_external_id:
                return pipeline_result
            
            # 步骤3: 获取dosser详情页面
            html_content = self._step3_get_dosser_detail(asset_external_id, pipeline_result)
            if not html_content:
                return pipeline_result
            
            # 步骤4: 提取毒理学信息结构
            asset_external_id = self._step4_extract_toxicological_structure(html_content, extract_output_file, pipeline_result)
            if not asset_external_id:
                return pipeline_result
            
            # 步骤5: 提取文档链接并转换为Markdown
            self._step5_extract_and_convert_documents(asset_external_id, pipeline_result)
            
            pipeline_result['success'] = True
            
            if self.verbose:
                print(f"\n=== 管道执行成功完成 ===")
                
        except Exception as e:
            pipeline_result['error_message'] = str(e)
            if self.verbose:
                print(f"\n=== 管道执行失败 ===")
                print(f"错误信息: {e}")
        
        self.results = pipeline_result
        return pipeline_result
    
    def _step1_search_substance(self, search_text: str, pipeline_result: Dict) -> Optional[str]:
        """步骤1: 搜索物质获取rmlId"""
        if self.verbose:
            print("步骤1: 搜索物质获取rmlId...")
        
        search_result = search_substance_rml_id(search_text, verbose=self.verbose)
        pipeline_result['step1_search'] = search_result
        
        rml_id = search_result.get('rml_id')
        if not rml_id:
            pipeline_result['error_message'] = f"未找到搜索文本 '{search_text}' 对应的rmlId"
            if self.verbose:
                print(f"❌ 步骤1失败: {pipeline_result['error_message']}")
            return None
        
        if self.verbose:
            print(f"✅ 步骤1成功: rmlId = {rml_id}")
            print()
        
        return rml_id
    
    def _step2_get_dosser_asset_id(self, rml_id: str, pipeline_result: Dict) -> Optional[str]:
        """步骤2: 获取dosser的assetExternalId"""
        if self.verbose:
            print("步骤2: 获取dosser的assetExternalId...")
        
        dosser_result = get_dosser_asset_external_id(rml_id=rml_id, verbose=self.verbose)
        pipeline_result['step2_dosser_list'] = dosser_result
        
        asset_external_id = dosser_result.get('asset_external_id')
        if not asset_external_id:
            pipeline_result['error_message'] = f"未找到rmlId '{rml_id}' 对应的assetExternalId"
            if self.verbose:
                print(f"❌ 步骤2失败: {pipeline_result['error_message']}")
            return None
        
        if self.verbose:
            print(f"✅ 步骤2成功: assetExternalId = {asset_external_id}")
            print()
        
        return asset_external_id
    
    def _step3_get_dosser_detail(self, asset_external_id: str, pipeline_result: Dict) -> Optional[str]:
        """步骤3: 获取dosser详情页面"""
        if self.verbose:
            print("步骤3: 获取dosser详情页面...")
        
        dosser_detail_result = get_dosser_detail_html(
            asset_external_id=asset_external_id,
            save_to_file=False,  # 中间过程不保存文件
            verbose=self.verbose
        )
        pipeline_result['step3_dosser_detail'] = dosser_detail_result
        
        if not dosser_detail_result.get('success'):
            pipeline_result['error_message'] = f"获取dosser详情页面失败，状态码: {dosser_detail_result.get('status_code')}"
            if self.verbose:
                print(f"❌ 步骤3失败: {pipeline_result['error_message']}")
            return None
        
        html_content = dosser_detail_result.get('html_content')
        
        if self.verbose:
            print(f"✅ 步骤3成功: 获取HTML内容 ({len(html_content)} 字符)")
            print()
        
        # 返回HTML内容给下一步使用
        return html_content
    
    def _step4_extract_toxicological_structure(self, html_content: str, output_file: str, pipeline_result: Dict) -> Optional[str]:
        """步骤4: 提取毒理学信息结构"""
        if self.verbose:
            print("步骤4: 提取毒理学信息结构...")
        
        try:
            # 直接使用HTML内容创建毒理学提取器实例
            extractor = ToxicologicalExtractor(html_content=html_content)
            
            # 提取毒理学结构
            structure = extractor.extract_toxicological_structure()
            
            if structure:
                # 生成输出文件名
                if output_file is None:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    search_text_safe = "".join(c for c in pipeline_result['search_text'] if c.isalnum() or c in '-_')[:20]
                    output_file = f"toxicological_structure_{search_text_safe}_{timestamp}.json"
                
                # 中间过程不保存文件
                saved_file = None
                
                # 记录结果
                pipeline_result['step4_toxicological_structure'] = {
                    'structure': structure,
                    'output_file': saved_file,
                    'sections_count': len(structure),
                    'success': True
                }
                
                if self.verbose:
                    print(f"✅ 步骤4成功: 提取到 {len(structure)} 个主要部分")
                    print("   提取的结构概览:")
                    extractor.print_structure(structure)
                    print()
                
                # 从pipeline_result中获取asset_external_id
                asset_external_id = pipeline_result.get('step2_dosser_list', {}).get('asset_external_id')
                return asset_external_id
            else:
                pipeline_result['step4_toxicological_structure'] = {
                    'structure': {},
                    'output_file': None,
                    'sections_count': 0,
                    'success': False,
                    'error': '未找到毒理学信息'
                }
                
                if self.verbose:
                    print("❌ 步骤4失败: 未找到毒理学信息")
                return None
                    
        except Exception as e:
            pipeline_result['step4_toxicological_structure'] = {
                'structure': {},
                'output_file': None,
                'sections_count': 0,
                'success': False,
                'error': str(e)
            }
            
            if self.verbose:
                print(f"❌ 步骤4失败: {str(e)}")
            
            return None
    
    def _step5_extract_and_convert_documents(self, asset_external_id: str, pipeline_result: Dict):
        """步骤5: 提取文档链接并转换为Markdown"""
        if self.verbose:
            print("步骤5: 提取文档链接并转换为Markdown...")
        
        # 获取步骤4的毒理学结构
        tox_structure = pipeline_result.get('step4_toxicological_structure', {}).get('structure', {})
        
        if not tox_structure:
            pipeline_result['step5_extract_documents'] = {
                'success': False,
                'error': '没有可用的毒理学结构数据',
                'processed_links': 0,
                'structure_with_content': {}
            }
            if self.verbose:
                print("❌ 步骤5失败: 没有可用的毒理学结构数据")
            return
        
        # 创建包含内容的结构副本
        structure_with_content = {}
        processed_links = 0
        successful_links = 0
        
        def process_structure_recursively(source_dict, target_dict):
            """递归处理结构，提取链接并获取内容"""
            nonlocal processed_links, successful_links
            
            for key, value in source_dict.items():
                if isinstance(value, dict):
                    # 如果值是字典，递归处理
                    target_dict[key] = {}
                    process_structure_recursively(value, target_dict[key])
                elif isinstance(value, str) and len(value) > 30 and '_' in value and '-' in value and '.' not in value:
                    # 如果值看起来像document_id，获取内容
                    processed_links += 1
                    document_id = value
                    
                    if self.verbose:
                        print(f"  处理文档 {processed_links}: {document_id[:20]}...")
                        print(f"    原始值: {value}")
                        print(f"    document_id: {document_id}")
                        print(f"    使用asset_external_id: {asset_external_id}")
                    
                    # 获取文档内容
                    # 使用当前pipeline的asset_external_id和提取的document_id
                    doc_result = get_document_detail(
                        asset_external_id=asset_external_id,
                        document_id=document_id,
                        output_format='markdown',
                        save_to_file=False,  # 不保存单独文件
                        verbose=False
                    )
                    
                    if doc_result.get('success') and doc_result.get('markdown_content'):
                        target_dict[key] = {
                            'document_id': document_id,
                            'markdown_content': doc_result['markdown_content'],
                            'content_length': len(doc_result['markdown_content']),
                            'status': 'success'
                        }
                        successful_links += 1
                        
                        if self.verbose:
                            print(f"    ✅ 成功获取内容 ({len(doc_result['markdown_content'])} 字符)")
                    else:
                        target_dict[key] = {
                            'document_id': document_id,
                            'markdown_content': None,
                            'error': f"获取失败，状态码: {doc_result.get('status_code')}",
                            'status': 'failed'
                        }
                        
                        if self.verbose:
                            print(f"    ❌ 获取失败: {doc_result.get('status_code')}")
                else:
                    # 其他类型的值，直接复制
                    target_dict[key] = value
        
        try:
            # 开始递归处理
            process_structure_recursively(tox_structure, structure_with_content)
            
            # 保存带内容的结构
            if self.save_files:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                search_text_safe = "".join(c for c in pipeline_result['search_text'] if c.isalnum() or c in '-_')[:20]
                output_file = f"toxicological_structure_with_content_{search_text_safe}_{timestamp}.json"
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(structure_with_content, f, indent=2, ensure_ascii=False)
                
                saved_file = os.path.abspath(output_file)
            else:
                saved_file = None
            
            # 记录结果
            pipeline_result['step5_extract_documents'] = {
                'success': True,
                'processed_links': processed_links,
                'successful_links': successful_links,
                'failed_links': processed_links - successful_links,
                'structure_with_content': structure_with_content,
                'output_file': saved_file
            }
            
            if self.verbose:
                print(f"✅ 步骤5成功: 处理了 {processed_links} 个链接，成功 {successful_links} 个")
                if saved_file:
                    print(f"   保存文件: {saved_file}")
                print()
                
        except Exception as e:
            pipeline_result['step5_extract_documents'] = {
                'success': False,
                'error': str(e),
                'processed_links': processed_links,
                'successful_links': successful_links,
                'structure_with_content': structure_with_content
            }
            
            if self.verbose:
                print(f"❌ 步骤5失败: {str(e)}")
    
    def save_results(self, output_file: str = None):
        """保存管道结果到JSON文件"""
        if not self.results:
            print("没有结果可保存")
            return
        
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            search_text_safe = "".join(c for c in self.results['search_text'] if c.isalnum() or c in '-_')[:20]
            output_file = f"echa_pipeline_result_{search_text_safe}_{timestamp}.json"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            
            if self.verbose:
                print(f"\n结果已保存到: {os.path.abspath(output_file)}")
        except Exception as e:
            print(f"保存结果失败: {e}")


def main():
    """主函数示例"""
    # 创建管道实例
    pipeline = ECHADataPipeline(verbose=True, save_files=True)
    
    # 示例1: 搜索CAS号
    search_text = "65-45-2"
    
    # 可选：指定毒理学结构提取结果的输出文件名
    extract_output_file = None  # 如果为None，将自动生成文件名
    
    # 运行管道
    result = pipeline.run_pipeline(search_text, extract_output_file=extract_output_file)
    
    # 保存结果
    pipeline.save_results()
    
    # 打印结果摘要
    if result['success']:
        print(f"\n=== 结果摘要 ===")
        print(f"搜索文本: {result['search_text']}")
        print(f"RML ID: {result['step1_search']['rml_id'] if result['step1_search'] else 'N/A'}")
        print(f"Asset External ID: {result['step2_dosser_list']['asset_external_id'] if result['step2_dosser_list'] else 'N/A'}")
        
        # 毒理学结构提取结果
        tox_result = result.get('step4_toxicological_structure', {})
        if tox_result.get('success'):
            print(f"毒理学结构提取: 成功提取 {tox_result.get('sections_count', 0)} 个部分")
            if tox_result.get('output_file'):
                print(f"结构文件: {tox_result.get('output_file')}")
        else:
            print(f"毒理学结构提取: 失败 - {tox_result.get('error', '未知错误')}")
        
        # 文档内容提取结果
        doc_result = result.get('step5_extract_documents', {})
        if doc_result.get('success'):
            print(f"文档内容提取: 处理 {doc_result.get('processed_links', 0)} 个链接，成功 {doc_result.get('successful_links', 0)} 个")
            if doc_result.get('output_file'):
                print(f"带内容的结构文件: {doc_result.get('output_file')}")
        else:
            print(f"文档内容提取: 失败 - {doc_result.get('error', '未知错误')}")
    else:
        print(f"\n=== 执行失败 ===")
        print(f"错误信息: {result.get('error_message', '未知错误')}")


if __name__ == "__main__":
    main()
