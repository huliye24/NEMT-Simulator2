#!/usr/bin/env python3
# Copyright 2026 NEMT Lab
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
MATLAB 桥接器 - MATLAB ↔ Python 协议转换
=============================================
将 MATLAB 的复杂输出 (多维矩阵、复数) 转换为 Python 可用的 JSON 格式

核心功能:
1. 通过 matlab.engine 启动/管理 MATLAB 引擎
2. 执行 NEMT 核心算法 (初始化、演化、频谱分析)
3. 处理数据转换 (矩阵 → DataFrame → JSON)
4. 缓存结果避免重复计算

使用方式:
    from adapters.matlab_bridge import MatlabBridge
    bridge = MatlabBridge()
    result = bridge.run_nemt_analysis(params)
"""

import os
import sys
import json
import time
import logging
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime

import numpy as np

from ..config import config

logger = logging.getLogger(__name__)

# ============================================================================
# 数据结构定义
# ============================================================================
@dataclass
class NEMTAnalysisResult:
    """NEMT 分析结果"""
    success: bool = False
    error: str = ""
    execution_time: float = 0.0

    # 原始数据
    close_prices: List[float] = field(default_factory=list)

    # NEMT 核心指标
    spectral_width: float = 0.0
    mean_frequency: float = 0.0
    resonance_peaks: List[Dict] = field(default_factory=list)

    # 频谱数据 (用于可视化)
    frequencies: List[float] = field(default_factory=list)
    spectrum: List[float] = field(default_factory=list)

    # 演化数据
    evolution_matrix: List[List[float]] = field(default_factory=list)

    # 统计指标
    stats: Dict[str, float] = field(default_factory=dict)

    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'error': self.error,
            'execution_time': self.execution_time,
            'spectral_width': self.spectral_width,
            'mean_frequency': self.mean_frequency,
            'resonance_peaks': self.resonance_peaks,
            'frequencies': self.frequencies[:100] if self.frequencies else [],  # 限制长度
            'spectrum': self.spectrum[:100] if self.spectrum else [],
            'stats': self.stats,
            'timestamp': self.timestamp,
        }

    def to_json(self, filepath: str = None) -> str:
        """导出为 JSON"""
        data = self.to_dict()
        json_str = json.dumps(data, indent=2, ensure_ascii=False)

        if filepath:
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(json_str)

        return json_str


# ============================================================================
# MATLAB 引擎管理器
# ============================================================================
class MatlabEngineManager:
    """
    MATLAB 引擎单例管理器
    ========================

    特性:
    - 线程安全 (使用线程本地存储)
    - 自动启动/复用引擎
    - 输出捕获
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._engine = None
        self._started = False
        self._lock = __import__('threading').Lock()
        self._initialized = True

        # 检测 MATLAB Engine API
        self._matlab_engine_available = self._check_matlab_engine()

    def _check_matlab_engine(self) -> bool:
        """检测 MATLAB Engine API 是否可用"""
        try:
            import matlab.engine
            logger.info("✅ MATLAB Engine API 可用")
            return True
        except ImportError:
            logger.warning("⚠️  MATLAB Engine API 不可用")
            logger.warning("   请在 MATLAB 中运行: >> engine.start_matlab")
            logger.warning("   或安装: cd $MATLABROOT/extern/engines/python && python setup.py install")
            return False

    @property
    def available(self) -> bool:
        return self._matlab_engine_available

    def get_engine(self):
        """获取或启动 MATLAB 引擎 (线程安全)"""
        if not self._matlab_engine_available:
            raise RuntimeError("MATLAB Engine API 不可用")

        if self._engine is None or not self._started:
            with self._lock:
                if self._engine is None:
                    import matlab.engine
                    logger.info("🚀 启动 MATLAB 引擎...")
                    start_time = time.time()

                    # 使用后台启动避免阻塞
                    self._engine = matlab.engine.start_matlab()

                    elapsed = time.time() - start_time
                    logger.info(f"✅ MATLAB 引擎启动成功 ({elapsed:.1f}s)")
                    self._started = True

        return self._engine

    def stop(self):
        """停止 MATLAB 引擎"""
        if self._engine:
            try:
                self._engine.quit()
                logger.info("🛑 MATLAB 引擎已停止")
            except Exception as e:
                logger.error(f"停止 MATLAB 引擎失败: {e}")
            finally:
                self._engine = None
                self._started = False


# 全局引擎实例
_engine_manager = MatlabEngineManager()


# ============================================================================
# MATLAB 桥接器主类
# ============================================================================
class MatlabBridge:
    """
    MATLAB 桥接器 - 协议转换的核心适配层
    ======================================

    功能:
    1. 将 Python 参数传递给 MATLAB
    2. 执行 NEMT 分析流程
    3. 将 MATLAB 输出 (矩阵) 转换为 Python JSON

    使用流程:
    1. 初始化: bridge = MatlabBridge()
    2. 设置数据: bridge.set_price_data(close_prices)
    3. 运行分析: result = bridge.run_analysis(params)
    4. 获取结果: result.spectral_width, result.resonance_peaks
    """

    def __init__(self, matlab_path: str = None):
        """
        初始化 MATLAB 桥接器

        Args:
            matlab_path: MATLAB 可执行文件路径 (可选)
        """
        self.matlab_path = matlab_path or config.matlab.engine_available
        self.engine = None
        self._cache = {}  # 结果缓存

        # 脚本路径
        self.scripts_path = str(config.paths.matlab_scripts)
        self.core_path = str(config.paths.matlab_core)

    # ------------------------------------------------------------------------
    # 引擎管理
    # ------------------------------------------------------------------------
    def start_engine(self) -> bool:
        """启动 MATLAB 引擎"""
        try:
            self.engine = _engine_manager.get_engine()

            # 添加路径
            self.engine.addpath(self.scripts_path, nargout=0)
            self.engine.addpath(self.core_path, nargout=0)

            logger.info(f"✅ MATLAB 路径已配置: {self.scripts_path}")
            return True

        except Exception as e:
            logger.error(f"启动 MATLAB 引擎失败: {e}")
            return False

    def stop_engine(self):
        """停止 MATLAB 引擎"""
        _engine_manager.stop()
        self.engine = None

    def is_engine_running(self) -> bool:
        """检查引擎是否运行"""
        return self.engine is not None

    # ------------------------------------------------------------------------
    # 数据传递 (Python → MATLAB)
    # ------------------------------------------------------------------------
    def set_price_data(self, prices: Union[List[float], np.ndarray],
                       symbol: str = "BTCUSDT") -> bool:
        """
        设置价格数据到 MATLAB 工作区

        Args:
            prices: 价格序列
            symbol: 交易对符号

        Returns:
            是否成功
        """
        if not self.engine:
            if not self.start_engine():
                return False

        try:
            # 转换为 numpy 数组并展平
            if isinstance(prices, list):
                prices = np.array(prices)
            prices = np.asarray(prices).flatten().astype(float)

            # 设置变量
            self.engine.workspace['priceData'] = prices
            self.engine.workspace['symbol'] = symbol
            self.engine.workspace['timestamp'] = list(range(len(prices)))

            logger.info(f"📊 价格数据已设置: {symbol}, {len(prices)} 点")
            return True

        except Exception as e:
            logger.error(f"设置价格数据失败: {e}")
            return False

    def set_nemt_params(self, params: Dict[str, Any]) -> bool:
        """
        设置 NEMT 参数到 MATLAB 工作区

        Args:
            params: NEMT 参数字典

        Returns:
            是否成功
        """
        if not self.engine:
            return False

        try:
            self.engine.workspace['alpha'] = params.get('alpha', 0.1)
            self.engine.workspace['beta'] = params.get('beta', 1.0)
            self.engine.workspace['noise'] = params.get('noiseLevel', params.get('noise', 0.2))
            self.engine.workspace['dt'] = params.get('dt', 0.01)
            self.engine.workspace['dx'] = params.get('dx', 1.0)
            self.engine.workspace['steps'] = params.get('steps', 200)

            n = params.get('n', len(prices) if 'priceData' in self.engine.workspace else 1000)
            self.engine.workspace['n'] = n

            logger.info(f"⚙️ NEMT 参数已设置: α={params['alpha']}, β={params['beta']}, η={params.get('noiseLevel', 0.2)}")
            return True

        except Exception as e:
            logger.error(f"设置 NEMT 参数失败: {e}")
            return False

    # ------------------------------------------------------------------------
    # MATLAB 代码执行
    # ------------------------------------------------------------------------
    def execute_code(self, code: str) -> Dict[str, Any]:
        """
        执行任意 MATLAB 代码

        Args:
            code: MATLAB 代码字符串

        Returns:
            执行结果字典
        """
        if not self.engine:
            if not self.start_engine():
                return {'success': False, 'error': '引擎启动失败'}

        try:
            # 包装代码以捕获错误
            wrapped_code = f"""
try
    {code}
catch ME
    fprintf(2, 'MATLAB_ERROR: %s\\n', ME.message);
end
"""
            self.engine.eval(wrapped_code, nargout=0)
            return {'success': True, 'message': '代码执行成功'}

        except Exception as e:
            logger.error(f"MATLAB 执行异常: {e}")
            return {'success': False, 'error': str(e)}

    def eval_expression(self, expression: str) -> Any:
        """
        计算 MATLAB 表达式并返回结果

        Args:
            expression: MATLAB 表达式

        Returns:
            表达式的值
        """
        if not self.engine:
            if not self.start_engine():
                return None

        try:
            return self.engine.eval(expression)
        except Exception as e:
            logger.error(f"计算表达式失败: {e}")
            return None

    def get_variable(self, name: str) -> Any:
        """获取 MATLAB 变量"""
        if not self.engine:
            return None

        try:
            value = self.engine.workspace[name]
            return self._convert_matlab_type(value)
        except Exception as e:
            logger.error(f"获取变量 {name} 失败: {e}")
            return None

    def _convert_matlab_type(self, value: Any) -> Any:
        """将 MATLAB 类型转换为 Python 原生类型"""
        if value is None:
            return None

        # 获取类型名
        type_name = type(value).__name__

        # matlab.double 类型
        if type_name == 'matlab.double':
            try:
                # 检查是否是复数
                if hasattr(value, 'real') and hasattr(value, 'imag'):
                    # 复数数组 - 返回复数列表
                    result = []
                    for i in range(len(value)):
                        if hasattr(value[i], 'real'):
                            result.append(complex(float(value[i].real), float(value[i].imag)))
                        else:
                            result.append(float(value[i]))
                    return result
                else:
                    # 实数数组
                    result = []
                    for v in value:
                        if hasattr(v, '_data'):
                            result.append(float(v._data[0]))
                        else:
                            try:
                                result.append(float(v))
                            except:
                                result.append(v)
                    return result
            except Exception as e:
                logger.warning(f"转换 matlab.double 失败: {e}")
                return None

        # matlab.int 等标量
        if type_name.startswith('matlab.'):
            try:
                return int(value)
            except:
                try:
                    return float(value)
                except:
                    return value

        # numpy 数组
        if isinstance(value, np.ndarray):
            return value.tolist()

        # 列表
        if isinstance(value, list):
            return value

        return value

    # ------------------------------------------------------------------------
    # NEMT 核心分析流程
    # ------------------------------------------------------------------------
    def run_analysis(self, price_data: List[float],
                     params: Dict[str, Any] = None,
                     use_cache: bool = True) -> NEMTAnalysisResult:
        """
        运行完整的 NEMT 分析

        Args:
            price_data: 价格序列
            params: NEMT 参数 (可选，使用默认值)
            use_cache: 是否使用缓存

        Returns:
            NEMTAnalysisResult 对象
        """
        result = NEMTAnalysisResult()
        start_time = time.time()

        # 使用默认参数
        if params is None:
            params = config.nemt_defaults.to_dict()

        # 检查缓存
        cache_key = self._make_cache_key(price_data, params)
        if use_cache and cache_key in self._cache:
            logger.info("📦 使用缓存的分析结果")
            return self._cache[cache_key]

        try:
            # 1. 启动引擎
            if not self.engine:
                if not self.start_engine():
                    result.error = "MATLAB 引擎启动失败"
                    return result

            # 2. 设置数据
            if not self.set_price_data(price_data):
                result.error = "设置价格数据失败"
                return result

            # 3. 设置参数
            self.set_nemt_params(params)

            # 4. 初始化状态
            init_code = """
            % 初始化 NEMT 状态 - 确保是列向量
            pd = priceData(:);
            normalized = (pd - mean(pd)) / std(pd);
            psi = normalized + 1i * zeros(length(normalized), 1);
            N = length(psi);
            """
            self.execute_code(init_code)

            # 5. 执行演化
            evolution_code = f"""
            % 时间演化 (NLS 方程)
            alpha = {params['alpha']};
            beta = {params['beta']};
            noiseLevel = {params.get('noiseLevel', params.get('noise', 0.2))};
            dt = {params['dt']};
            dx = {params['dx']};
            steps = {params['steps']};

            psiHistory = {{abs(psi)}};

            for t = 1:steps
                % Laplacian (use local N)
                n = length(psi);
                laplacian = zeros(n, 1);
                laplacian(2:n-1) = psi(1:n-2) - 2*psi(2:n-1) + psi(3:n);
                laplacian(1) = psi(2) - 2*psi(1);
                laplacian(n) = psi(n-1) - 2*psi(n);
                laplacian = laplacian / (dx^2);

                % Nonlinear term
                psiAbs = abs(psi);
                psiAbs = min(psiAbs, 10);
                nonlinear = beta * (psiAbs.^2) .* psi;

                % NLS update
                dpsi = 1i * (alpha * laplacian + nonlinear);

                % Noise
                noise = noiseLevel * (randn(n, 1) + 1i*randn(n, 1)) / sqrt(2);

                % Update
                psi = psi + dt * (dpsi + noise);

                % Record every 5 steps
                if mod(t, 5) == 0
                    psiHistory{{end+1}} = abs(psi);
                end
            end
            """
            self.execute_code(evolution_code)

            # 6. 频谱分析
            spectrum_code = """
            % FFT
            psi_vec = psi(:);
            N = length(psi_vec);
            spectrum = fftshift(fft(psi_vec));
            freqs = (-N/2:N/2-1) / N;

            % Take positive half
            mid = N/2 + 1;
            freqs = freqs(mid:end);
            spectrum = abs(spectrum(mid:end));

            % Spectral width
            spectrumPower = spectrum.^2;
            totalPower = sum(spectrumPower);
            if totalPower > 0
                meanFreq = sum(freqs .* spectrumPower) / totalPower;
                variance = sum((freqs - meanFreq).^2 .* spectrumPower) / totalPower;
                spectralWidth = sqrt(variance);
            else
                meanFreq = 0;
                spectralWidth = 0;
            end

            % Resonance peaks
            threshold = mean(spectrumPower) * 2;
            peakIndices = [];
            for i = 2:length(spectrumPower)-1
                if spectrumPower(i) > spectrumPower(i-1) && spectrumPower(i) > spectrumPower(i+1) && spectrumPower(i) > threshold
                    peakIndices = [peakIndices, i];
                end
            end
            peakFrequencies = freqs(peakIndices);
            peakAmplitudes = spectrum(peakIndices);
            """
            self.execute_code(spectrum_code)

            # 7. 提取结果
            result.spectral_width = float(self.get_variable('spectralWidth') or 0)
            result.mean_frequency = float(self.get_variable('meanFreq') or 0)

            # 提取共振峰
            peak_freqs = self.get_variable('peakFrequencies')
            peak_amps = self.get_variable('peakAmplitudes')
            if peak_freqs and peak_amps:
                if isinstance(peak_freqs, list) and isinstance(peak_amps, list):
                    for i in range(min(len(peak_freqs), len(peak_amps))):
                        result.resonance_peaks.append({
                            'frequency': float(peak_freqs[i]),
                            'amplitude': float(peak_amps[i]),
                        })

            # 提取频谱数据
            freqs = self.get_variable('freqs')
            spectrum = self.get_variable('spectrum')
            if freqs is not None:
                result.frequencies = [float(f) for f in freqs[:200]]
            if spectrum is not None:
                result.spectrum = [float(s) for s in spectrum[:200]]

            # 统计指标
            result.stats = {
                'data_points': len(price_data),
                'alpha': params['alpha'],
                'beta': params['beta'],
                'noise': params.get('noiseLevel', params.get('noise', 0.2)),
                'steps': params['steps'],
            }

            result.success = True

        except Exception as e:
            result.error = str(e)
            logger.error(f"NEMT 分析失败: {e}")

        finally:
            result.execution_time = time.time() - start_time
            logger.info(f"⏱️  分析完成，耗时: {result.execution_time:.2f}s")

        # 缓存结果
        if result.success:
            self._cache[cache_key] = result

        return result

    def _make_cache_key(self, price_data: List[float], params: Dict) -> str:
        """生成缓存键"""
        import hashlib
        data_hash = hashlib.md5(str(price_data[:100]).encode()).hexdigest()
        param_str = f"{params.get('alpha', 0.1)}_{params.get('beta', 1.0)}_{params.get('noiseLevel', 0.2)}"
        return f"{data_hash}_{param_str}"

    # ------------------------------------------------------------------------
    # 便捷方法
    # ------------------------------------------------------------------------
    def run_simple_analysis(self, close_prices: List[float]) -> Dict[str, Any]:
        """
        运行简单分析 (使用默认参数)

        Args:
            close_prices: 收盘价序列

        Returns:
            分析结果字典
        """
        result = self.run_analysis(close_prices)
        return result.to_dict()

    def run_noise_scan(self, price_data: List[float],
                      noise_levels: List[float] = None) -> List[NEMTAnalysisResult]:
        """
        运行噪声扫描实验

        Args:
            price_data: 价格数据
            noise_levels: 噪声水平列表 (默认: [0.01, 0.05, 0.1, 0.2, 0.5])

        Returns:
            各噪声水平的分析结果列表
        """
        if noise_levels is None:
            noise_levels = [0.01, 0.05, 0.1, 0.2, 0.5]

        results = []
        for noise in noise_levels:
            logger.info(f"🔍 噪声扫描: η = {noise}")
            params = config.nemt_defaults.to_dict()
            params['noiseLevel'] = noise
            result = self.run_analysis(price_data, params, use_cache=False)
            results.append(result)

        return results

    def run_beta_scan(self, price_data: List[float],
                      beta_values: List[float] = None) -> List[NEMTAnalysisResult]:
        """
        运行非线性扫描实验

        Args:
            price_data: 价格数据
            beta_values: β 值列表 (默认: [0.1, 0.5, 1.0, 2.0, 5.0])

        Returns:
            各 β 值的分析结果列表
        """
        if beta_values is None:
            beta_values = [0.1, 0.5, 1.0, 2.0, 5.0]

        results = []
        for beta in beta_values:
            logger.info(f"📈 非线性扫描: β = {beta}")
            params = config.nemt_defaults.to_dict()
            params['beta'] = beta
            result = self.run_analysis(price_data, params, use_cache=False)
            results.append(result)

        return results

    # ------------------------------------------------------------------------
    # 工具方法
    # ------------------------------------------------------------------------
    def export_to_json(self, result: NEMTAnalysisResult,
                       filepath: str = None) -> str:
        """导出结果到 JSON"""
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = str(config.paths.data_dir / f"nemt_result_{timestamp}.json")

        return result.to_json(filepath)

    def get_engine_info(self) -> Dict[str, Any]:
        """获取引擎信息"""
        return {
            'available': _engine_manager.available,
            'running': self.is_engine_running(),
            'scripts_path': self.scripts_path,
            'core_path': self.core_path,
        }


# ============================================================================
# 便捷函数
# ============================================================================
def create_matlab_bridge(matlab_path: str = None) -> MatlabBridge:
    """创建 MATLAB 桥接器"""
    return MatlabBridge(matlab_path)


# ============================================================================
# 单元测试
# ============================================================================
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    bridge = MatlabBridge()

    # 测试引擎信息
    info = bridge.get_engine_info()
    print(f"MATLAB 引擎信息: {json.dumps(info, indent=2, ensure_ascii=False)}")

    # 如果引擎可用，测试分析
    if info['available']:
        # 生成测试数据
        t = np.linspace(0, 10 * np.pi, 500)
        prices = 50000 + 1000 * np.sin(t) + 500 * np.random.randn(500)

        result = bridge.run_analysis(prices.tolist())
        print(f"分析结果: {json.dumps(result.to_dict(), indent=2, ensure_ascii=False)}")
