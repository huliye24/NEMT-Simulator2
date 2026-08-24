"""
NEMT 代码模板生成器

自动生成胶囊代码、测试代码和配置文件。
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


# ==================== 模板 ====================

CAPSULE_TEMPLATE = '''"""
{class_name} - {description}

{description_long}
"""

from typing import Dict, List, Any, Optional
from nemt.core.capsule import ModuleCapsule
from nemt.core.event_bus import Event

__all__ = ['{class_name}']


class {class_name}(ModuleCapsule):
    """
    {class_name} 胶囊

    {description}

    订阅事件:
    {subscribed_events}

    发布事件:
    {published_events}
    """

    def __init__(self):
        super().__init__('{capsule_id}')
        
        # 状态
        {state_init}

    def init(self) -> None:
        """初始化"""
        {init_code}
    
    def exec(self) -> Dict[str, Any]:
        """
        执行 - 返回胶囊状态

        Returns:
            状态字典
        """
        return {{
            {exec_return}
        }}
    
    def shutdown(self) -> None:
        """关闭"""
        {shutdown_code}
'''

TEST_TEMPLATE = '''
"""
{class_name} 测试
"""

import pytest
from nemt.core.event_bus import EventBus
from nemt.core.config_center import ConfigCenter
from nemt.{module_path}.{class_name}


class Test{class_name}:
    """{class_name} 测试"""

    def test_creation(self):
        """测试创建"""
        capsule = {class_name}()
        assert capsule.capsule_id == '{capsule_id}'

    def test_init(self):
        """测试初始化"""
        eb = EventBus()
        cc = ConfigCenter()
        
        capsule = {class_name}()
        capsule.event_bus = eb
        capsule.config = cc
        capsule.init()
        
        assert capsule.is_initialized

    def test_exec(self):
        """测试执行"""
        eb = EventBus()
        cc = ConfigCenter()
        
        capsule = {class_name}()
        capsule.event_bus = eb
        capsule.config = cc
        capsule.init()
        
        result = capsule.exec()
        assert isinstance(result, dict)

    def test_shutdown(self):
        """测试关闭"""
        eb = EventBus()
        cc = ConfigCenter()
        
        capsule = {class_name}()
        capsule.event_bus = eb
        capsule.config = cc
        capsule.init()
        
        capsule.shutdown()
        assert not capsule.is_running
'''

CONFIG_TEMPLATE = '''
# {class_name} 配置

# 胶囊配置
{module_path}:
  enabled: true
  
  # 参数配置
  params:
    {params}

  # 事件订阅
  subscriptions:
    - nemt.signal
    - market.bar
    
  # 发布事件
  publications:
    - nemt.{capsule_id}
'''

REQUIREMENTS_TEMPLATE = '''
# {class_name} 依赖

# 核心依赖
nemt>=0.2.0

# 额外依赖
{extra_deps}
'''


# ==================== 生成器 ====================

class CodeGenerator:
    """代码生成器"""

    def __init__(self, output_dir: str = None):
        self.output_dir = Path(output_dir) if output_dir else Path.cwd()

    def generate_capsule(self, name: str, description: str = '',
                       subscribed_events: List[str] = None,
                       published_events: List[str] = None,
                       params: Dict[str, any] = None) -> str:
        """
        生成胶囊代码

        Args:
            name: 胶囊名称
            description: 简短描述
            subscribed_events: 订阅的事件列表
            published_events: 发布的事件列表
            params: 参数字典

        Returns:
            生成的文件路径
        """
        # 规范化名称
        name = name.lower().replace('-', '_').replace(' ', '_')
        class_name = ''.join(word.capitalize() for word in name.split('_'))
        capsule_id = name

        # 准备参数
        subscribed_events = subscribed_events or []
        published_events = published_events or []
        params = params or {}

        # 生成事件列表字符串
        sub_events_str = '\n    '.join([f'- {e}' for e in subscribed_events]) or '    (无)'
        pub_events_str = '\n    '.join([f'- {e}' for e in published_events]) or '    (无)'

        # 生成状态初始化
        state_init = '\n        '.join([f'self._{k}: {type(v).__name__} = {repr(v)}'
                                          for k, v in params.items()]) or '        pass'

        # 生成初始化代码
        init_code = '\n        '.join([f'self.subscribe(\'{e}\', self._on_{e.replace(".", "_")})'
                                          for e in subscribed_events]) if subscribed_events else '        pass'

        # 生成执行返回
        exec_return = '\n            '.join([f'\'{k}\': self._{k},'
                                          for k in params.keys()]) or '            \'status\': \'ok\''

        # 生成关闭代码
        shutdown_code = '\n        '.join([f'self.unsubscribe(\'{e}\', self._on_{e.replace(".", "_")})'
                                            for e in subscribed_events]) if subscribed_events else '        pass'

        # 生成模块路径
        module_path = 'core'

        # 格式化模板
        code = CAPSULE_TEMPLATE.format(
            class_name=class_name,
            description=description or f'{class_name} capsule',
            description_long=description or f'{class_name} 胶囊模块',
            capsule_id=capsule_id,
            subscribed_events=sub_events_str,
            published_events=pub_events_str,
            state_init=state_init or '        pass',
            init_code=init_code,
            exec_return=exec_return,
            shutdown_code=shutdown_code,
            module_path=module_path,
        )

        # 写入文件
        output_path = self.output_dir / 'nemt_os' / 'nemt' / 'core' / f'{name}_capsule.py'
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(code, encoding='utf-8')

        return str(output_path)

    def generate_test(self, capsule_name: str, output_dir: str = None) -> str:
        """
        生成测试代码

        Args:
            capsule_name: 胶囊名称
            output_dir: 输出目录

        Returns:
            生成的文件路径
        """
        # 规范化名称
        name = capsule_name.lower().replace('-', '_').replace(' ', '_')
        class_name = ''.join(word.capitalize() for word in name.split('_'))
        capsule_id = name
        module_path = 'core'

        # 格式化模板
        code = TEST_TEMPLATE.format(
            class_name=class_name,
            capsule_id=capsule_id,
            module_path=module_path,
        )

        # 写入文件
        output_path = Path(output_dir or str(self.output_dir / 'tests'))
        output_path.mkdir(parents=True, exist_ok=True)
        output_path = output_path / f'test_{name}_capsule.py'
        output_path.write_text(code, encoding='utf-8')

        return str(output_path)

    def generate_config(self, capsule_name: str, params: Dict[str, any] = None,
                      output_dir: str = None) -> str:
        """
        生成配置文件

        Args:
            capsule_name: 胶囊名称
            params: 参数字典
            output_dir: 输出目录

        Returns:
            生成的文件路径
        """
        name = capsule_name.lower().replace('-', '_')
        params = params or {}

        # 生成参数字符串
        params_str = '\n    '.join([f'{k}: {v}' for k, v in params.items()]) or '    enabled: true'

        # 格式化模板
        code = CONFIG_TEMPLATE.format(
            class_name=capsule_name,
            capsule_id=name,
            module_path=name,
            params=params_str,
        )

        # 写入文件
        output_path = Path(output_dir or str(self.output_dir / 'config'))
        output_path.mkdir(parents=True, exist_ok=True)
        output_path = output_path / f'{name}.yaml'
        output_path.write_text(code, encoding='utf-8')

        return str(output_path)


# ==================== 便捷函数 ====================

def create_capsule(name: str, description: str = '', **kwargs) -> str:
    """
    创建胶囊的便捷函数

    Args:
        name: 胶囊名称
        description: 描述
        **kwargs: 其他参数

    Returns:
        生成的文件路径
    """
    generator = CodeGenerator()
    return generator.generate_capsule(name, description, **kwargs)


def create_test(capsule_name: str, output_dir: str = None) -> str:
    """
    创建测试的便捷函数

    Args:
        capsule_name: 胶囊名称
        output_dir: 输出目录

    Returns:
        生成的文件路径
    """
    generator = CodeGenerator()
    return generator.generate_test(capsule_name, output_dir)


def create_config(capsule_name: str, params: Dict = None, output_dir: str = None) -> str:
    """
    创建配置的便捷函数

    Args:
        capsule_name: 胶囊名称
        params: 参数
        output_dir: 输出目录

    Returns:
        生成的文件路径
    """
    generator = CodeGenerator()
    return generator.generate_config(capsule_name, params, output_dir)


# ==================== 主程序 ====================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='NEMT 代码生成器')
    parser.add_argument('command', choices=['capsule', 'test', 'config', 'all'],
                       help='生成类型')
    parser.add_argument('name', help='名称')
    parser.add_argument('-d', '--description', help='描述')
    parser.add_argument('-o', '--output', help='输出目录')
    parser.add_argument('-s', '--subscribed', nargs='+', help='订阅事件')
    parser.add_argument('-p', '--published', nargs='+', help='发布事件')
    parser.add_argument('--params', nargs='+', help='参数 (key=value)')

    args = parser.parse_args()

    # 解析参数
    params = {}
    if args.params:
        for p in args.params:
            if '=' in p:
                k, v = p.split('=', 1)
                # 尝试转换为数字
                try:
                    v = float(v)
                    if v.is_integer():
                        v = int(v)
                except ValueError:
                    pass
                params[k] = v

    generator = CodeGenerator(args.output)

    if args.command == 'capsule':
        path = generator.generate_capsule(
            args.name, args.description,
            args.subscribed or [], args.published or [], params
        )
        print(f'胶囊代码已生成: {path}')

    elif args.command == 'test':
        path = generator.generate_test(args.name)
        print(f'测试代码已生成: {path}')

    elif args.command == 'config':
        path = generator.generate_config(args.name, params)
        print(f'配置文件已生成: {path}')

    elif args.command == 'all':
        path1 = generator.generate_capsule(
            args.name, args.description,
            args.subscribed or [], args.published or [], params
        )
        path2 = generator.generate_test(args.name)
        path3 = generator.generate_config(args.name, params)
        print(f'已生成:')
        print(f'  胶囊: {path1}')
        print(f'  测试: {path2}')
        print(f'  配置: {path3}')
