#!/usr/bin/env python3
"""
获取 GitHub 待审查 PR 列表
需要设置 GITHUB_TOKEN 环境变量
"""

import os
import requests
from datetime import datetime


def get_pending_prs(owner: str, repo: str, token: str = None) -> list:
    """获取待审查的 PR"""
    
    headers = {
        'Accept': 'application/vnd.github.v3+json'
    }
    if token:
        headers['Authorization'] = f'token {token}'
    
    url = f'https://api.github.com/repos/{owner}/{repo}/pulls'
    params = {
        'state': 'open',
        'sort': 'updated',
        'direction': 'desc'
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        prs = response.json()
        
        pending = []
        for pr in prs:
            # 检查是否有待处理的审查请求
            pending.append({
                'number': pr['number'],
                'title': pr['title'],
                'author': pr['user']['login'],
                'updated_at': pr['updated_at'],
                'url': pr['html_url'],
                'draft': pr['draft']
            })
        
        return pending
    
    except requests.RequestException as e:
        print(f"❌ 获取 PR 失败: {e}")
        return []


def format_pr_list(prs: list) -> str:
    """格式化 PR 列表"""
    if not prs:
        return "✅ 没有待审查的 PR"
    
    output = f"📋 待审查 PR ({len(prs)} 个):\n\n"
    
    for pr in prs[:10]:  # 最多显示 10 个
        draft_mark = "📝 " if pr['draft'] else ""
        updated = datetime.fromisoformat(pr['updated_at'].replace('Z', '+00:00'))
        days_ago = (datetime.now() - updated.replace(tzinfo=None)).days
        
        output += f"{draft_mark}#{pr['number']}: {pr['title']}\n"
        output += f"   作者: @{pr['author']} | 更新: {days_ago} 天前\n"
        output += f"   🔗 {pr['url']}\n\n"
    
    return output


def main():
    # 配置
    owner = os.getenv('GITHUB_OWNER', 'huliye24')
    repo = os.getenv('GITHUB_REPO', 'NEMT-Simulator2')
    token = os.getenv('GITHUB_TOKEN')
    
    print(f"🔍 获取 {owner}/{repo} 的待审查 PR...")
    
    prs = get_pending_prs(owner, repo, token)
    print(format_pr_list(prs))
    
    return prs


if __name__ == "__main__":
    main()
