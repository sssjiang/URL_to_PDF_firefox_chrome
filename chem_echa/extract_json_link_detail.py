import requests
import os
from markdownify import markdownify as md
from bs4 import BeautifulSoup

cookies = {
    'legalNotice': '%7B%22accepted%22%3Atrue%2C%22expired%22%3Afalse%2C%22acceptedDate%22%3A1756802272182%7D',
    'cck1': '%7B%22cm%22%3Atrue%2C%22all1st%22%3Atrue%7D',
    '_pk_id.b1c62efe-8fd0-4b63-a615-30d86a21a01e.f839': 'afbddb297a39ebfa.1756802275.2.1757041114.1756978804.',
}

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'en,zh;q=0.9,zh-CN;q=0.8',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Pragma': 'no-cache',
    'Referer': 'https://chem.echa.europa.eu/html-pages/2c770589-dbbf-4dfc-a0f3-d9162b85bb4d/index.html',
    'Sec-Fetch-Dest': 'iframe',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    # 'Cookie': 'legalNotice=%7B%22accepted%22%3Atrue%2C%22expired%22%3Afalse%2C%22acceptedDate%22%3A1756802272182%7D; cck1=%7B%22cm%22%3Atrue%2C%22all1st%22%3Atrue%7D; _pk_id.b1c62efe-8fd0-4b63-a615-30d86a21a01e.f839=afbddb297a39ebfa.1756802275.2.1757041114.1756978804.',
}

def get_document_detail(asset_external_id, document_id, output_format='markdown', save_to_file=True, output_filename=None, verbose=False):
    """
    获取文档详情页面内容，支持HTML和Markdown格式输出
    
    Args:
        asset_external_id (str): 资产外部ID（如：'2c770589-dbbf-4dfc-a0f3-d9162b85bb4d'）
        document_id (str): 文档ID（如：'664ca5e2-0724-482f-8c2e-c809311cb18d_d18b246e-13d7-423f-a045-5da4c757759e'）
        output_format (str): 输出格式，'html' 或 'markdown'，默认为 'markdown'
        save_to_file (bool): 是否保存为文件，默认为 True
        output_filename (str): 输出文件名，默认根据格式自动生成
        verbose (bool): 是否打印详细信息，默认为 False
    
    Returns:
        dict: 包含以下字段的字典
            - html_content (str): 原始HTML页面内容
            - markdown_content (str): Markdown格式内容（如果选择了markdown格式）
            - status_code (int): HTTP响应状态码
            - url (str): 请求的URL
            - saved_file (str): 保存的文件路径（如果save_to_file为True）
            - success (bool): 请求是否成功
            - output_format (str): 实际使用的输出格式
    """
    # 构造URL
    url = f'https://chem.echa.europa.eu/html-pages/{asset_external_id}/documents/{document_id}.html'
    
    result = {
        'html_content': None,
        'markdown_content': None,
        'status_code': None,
        'url': url,
        'saved_file': None,
        'success': False,
        'output_format': output_format
    }
    
    try:
        response = requests.get(url, cookies=cookies, headers=headers)
        result['status_code'] = response.status_code
        result['html_content'] = response.text
        
        if response.status_code == 200:
            result['success'] = True
            
            # 如果选择markdown格式，转换HTML内容
            if output_format.lower() == 'markdown':
                try:
                    # 使用BeautifulSoup清理HTML
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 移除script和style标签
                    for script in soup(["script", "style"]):
                        script.decompose()
                    
                    # 转换为markdown
                    result['markdown_content'] = md(str(soup), heading_style="ATX")
                except Exception as e:
                    if verbose:
                        print(f"转换为Markdown时出错: {str(e)}")
                    # 如果转换失败，回退到HTML格式
                    result['output_format'] = 'html'
            
            if save_to_file:
                if output_filename is None:
                    if result['output_format'] == 'markdown' and result['markdown_content']:
                        output_filename = f'document_detail_{asset_external_id}_{document_id[:8]}.md'
                    else:
                        output_filename = f'document_detail_{asset_external_id}_{document_id[:8]}.html'
                
                # 保存文件
                if result['output_format'] == 'markdown' and result['markdown_content']:
                    with open(output_filename, 'w', encoding='utf-8') as f:
                        f.write(result['markdown_content'])
                else:
                    with open(output_filename, 'w', encoding='utf-8') as f:
                        f.write(response.text)
                
                result['saved_file'] = os.path.abspath(output_filename)
                
                if verbose:
                    print(f"成功获取文档详情页面")
                    print(f"Asset External ID: {asset_external_id}")
                    print(f"Document ID: {document_id}")
                    print(f"URL: {url}")
                    print(f"状态码: {response.status_code}")
                    print(f"输出格式: {result['output_format']}")
                    print(f"HTML内容长度: {len(response.text)} 字符")
                    if result['markdown_content']:
                        print(f"Markdown内容长度: {len(result['markdown_content'])} 字符")
                    print(f"保存文件: {result['saved_file']}")
            else:
                if verbose:
                    print(f"成功获取文档详情页面")
                    print(f"Asset External ID: {asset_external_id}")
                    print(f"Document ID: {document_id}")
                    print(f"URL: {url}")
                    print(f"状态码: {response.status_code}")
                    print(f"输出格式: {result['output_format']}")
                    print(f"HTML内容长度: {len(response.text)} 字符")
                    if result['markdown_content']:
                        print(f"Markdown内容长度: {len(result['markdown_content'])} 字符")
        else:
            if verbose:
                print(f"请求失败")
                print(f"Asset External ID: {asset_external_id}")
                print(f"Document ID: {document_id}")
                print(f"URL: {url}")
                print(f"状态码: {response.status_code}")
                
    except Exception as e:
        if verbose:
            print(f"请求过程中发生错误: {str(e)}")
            print(f"Asset External ID: {asset_external_id}")
            print(f"Document ID: {document_id}")
            print(f"URL: {url}")
    
    return result


# 如果直接运行此脚本，则执行测试
if __name__ == "__main__":
    # 使用示例中的参数进行测试
    asset_id = '2c770589-dbbf-4dfc-a0f3-d9162b85bb4d'
    doc_id = '664ca5e2-0724-482f-8c2e-c809311cb18d_d18b246e-13d7-423f-a045-5da4c757759e'
    
    # 测试Markdown格式输出
    result = get_document_detail(asset_id, doc_id, output_format='markdown', verbose=True)
    print(f"\n函数返回结果:")
    print(f"请求成功: {result['success']}")
    print(f"状态码: {result['status_code']}")
    print(f"输出格式: {result['output_format']}")
    print(f"保存文件: {result['saved_file']}")
    if result['markdown_content']:
        print(f"Markdown内容前200字符: {result['markdown_content'][:200]}...")
    elif result['html_content']:
        print(f"HTML内容前200字符: {result['html_content'][:200]}...")