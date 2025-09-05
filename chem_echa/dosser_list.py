import requests
from datetime import datetime

def filter_dosser_items(response_data):
    """
    筛选dosser项目：
    1. 优先选择registrationStatus为'Active'且lastUpdatedDate最新的项目
    2. 如果没有Active状态的项目，则选择时间最新的项目
    """
    if 'items' not in response_data or not response_data['items']:
        return None
    
    items = response_data['items']
    
    # 如果只有一个项目，直接返回
    if len(items) == 1:
        return items[0]
    
    # 分离Active和非Active项目
    active_items = [item for item in items if item.get('registrationStatus') == 'Active']
    
    def parse_date(date_str):
        """解析日期字符串为datetime对象"""
        if not date_str:
            return datetime.min
        try:
            # 处理ISO格式的日期时间
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            return datetime.min
    
    # 如果有Active状态的项目，从中选择时间最新的
    if active_items:
        return max(active_items, key=lambda x: parse_date(x.get('lastUpdatedDate')))
    
    # 如果没有Active状态的项目，从所有项目中选择时间最新的
    return max(items, key=lambda x: parse_date(x.get('lastUpdatedDate')))

cookies = {
    'legalNotice': '%7B%22accepted%22%3Atrue%2C%22expired%22%3Afalse%2C%22acceptedDate%22%3A1756802272182%7D',
    'cck1': '%7B%22cm%22%3Atrue%2C%22all1st%22%3Atrue%7D',
    '_pk_ses.b1c62efe-8fd0-4b63-a615-30d86a21a01e.f839': '*',
    '_pk_id.b1c62efe-8fd0-4b63-a615-30d86a21a01e.f839': 'afbddb297a39ebfa.1756802275.1.1756976436.1756971630.',
}

headers = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en,zh;q=0.9,zh-CN;q=0.8',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Pragma': 'no-cache',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
    'sec-ch-ua': '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    # 'Cookie': 'legalNotice=%7B%22accepted%22%3Atrue%2C%22expired%22%3Afalse%2C%22acceptedDate%22%3A1756802272182%7D; cck1=%7B%22cm%22%3Atrue%2C%22all1st%22%3Atrue%7D; _pk_ses.b1c62efe-8fd0-4b63-a615-30d86a21a01e.f839=*; _pk_id.b1c62efe-8fd0-4b63-a615-30d86a21a01e.f839=afbddb297a39ebfa.1756802275.1.1756976436.1756971630.',
}

def get_dosser_asset_external_id(rml_id, verbose=False):
    """
    获取dosser的assetExternalId
    
    Args:
        rml_id (str): RML ID
        verbose (bool): 是否打印详细信息，默认为 False
    
    Returns:
        dict: 包含以下字段的字典
            - asset_external_id (str): 筛选出的项目的assetExternalId，如果没有找到则为None
            - selected_item (dict): 筛选出的完整项目信息，如果没有找到则为None
            - reason (str): 筛选理由说明
            - raw_response (dict): 原始API响应数据
    """
    params = {
        'pageIndex': '1',
        'pageSize': '100',
        'rmlId': rml_id,
        'registrationStatuses': 'Active',
    }

    response = requests.get(
        'https://chem.echa.europa.eu/api-dossier-list/v1/dossier',
        params=params,
        cookies=cookies,
        headers=headers,
    )

    # 获取响应数据
    response_data = response.json()

    # 筛选最合适的项目
    filtered_item = filter_dosser_items(response_data)

    result = {
        'asset_external_id': None,
        'selected_item': None,
        'reason': '',
        'raw_response': response_data
    }

    if filtered_item:
        asset_external_id = filtered_item.get('assetExternalId')
        result['asset_external_id'] = asset_external_id
        result['selected_item'] = filtered_item
        
        if filtered_item.get('registrationStatus') == 'Active':
            result['reason'] = f"选择了Active状态的项目，最后更新时间: {filtered_item.get('lastUpdatedDate')}"
        else:
            result['reason'] = f"没有Active状态的项目，选择了最新更新的项目，最后更新时间: {filtered_item.get('lastUpdatedDate')}"
        
        if verbose:
            print(f"筛选结果 assetExternalId: {asset_external_id}")
            print(f"\n筛选理由: {result['reason']}")
    else:
        result['reason'] = "没有找到任何项目"
        if verbose:
            print("没有找到任何项目")

    if verbose:
        print(f"\n原始完整响应:")
        print(response_data)

    return result


# 如果直接运行此脚本，则执行测试
if __name__ == "__main__":
    result = get_dosser_asset_external_id(rml_id='100.036.124', verbose=True)
    print(f"\n函数返回结果:")
    print(f"Asset External ID: {result['asset_external_id']}")
    print(f"筛选理由: {result['reason']}")