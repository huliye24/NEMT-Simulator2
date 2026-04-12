classdef NEMTSimulator
    %NEMTSimulator 非平衡市场理论模拟器
    %
    % 基于改进的非线性薛定谔方程 (NLS):
    %   i*∂ψ/∂t + α*∂²ψ/∂x² + β*|ψ|²*ψ = η(x,t)
    %
    % 使用方法:
    %   sim = NEMTSimulator();
    %   psi = sim.initializeState(priceData);
    %   psi = sim.evolve(psi);
    %   [freqs, spectrum] = sim.spectralAnalysis(psi);
    
    properties
        params (1,1) NEMTParams = NEMTParams()  % 模型参数
        psi                               % 当前状态复振幅
        psiHistory                        % 演化历史
        psiEvolution                       % 时空演化矩阵
        spectrum                           % 频谱
        freqs                              % 频率轴
        N                                  % 数据点数
        spectralWidth                      % 谱宽
        meanFrequency                      % 平均频率
    end
    
    methods
        function obj = NEMTSimulator(params)
            % 构造函数
            if nargin >= 1 && ~isempty(params)
                obj.params = params;
            end
        end
        
        function obj = initializeState(obj, priceData)
            % initializeState 初始化市场状态（复振幅ψ）
            %
            % 输入:
            %   priceData - 原始价格序列 (向量)
            %
            % 输出:
            %   obj.psi - 归一化后的复振幅
            
            % 归一化处理
            normalized = (priceData - mean(priceData)) / std(priceData);
            
            % 转换为复振幅（虚部为0）
            obj.psi = normalized + 1i * zeros(size(normalized));
            obj.N = length(obj.psi);
            
            % 初始化历史记录
            obj.psiHistory = {abs(obj.psi)};
            
            fprintf('初始化完成: %d 个数据点\n', obj.N);
        end
        
        function psi = evolve(obj, psi)
            % evolve 时间演化（核心算法）
            %
            % NLS方程离散格式（欧拉法）:
            %   dψ/dt = i*(α*∇²ψ + β*|ψ|²*ψ) + η
            %
            % 输入:
            %   psi - 初始复振幅
            %
            % 输出:
            %   psi - 演化后的复振幅
            
            if ~exist('psi', 'var') || isempty(psi)
                psi = obj.psi;
            end
            
            psi = psi(:);  % 确保为列向量
            N = length(psi);
            
            alpha = obj.params.alpha;
            beta = obj.params.beta;
            dt = obj.params.dt;
            dx = obj.params.dx;
            steps = obj.params.steps;
            noiseLevel = obj.params.noise;
            
            % 演化循环
            for t = 1:steps
                % 1. 计算拉普拉斯算子（二阶中心差分）
                laplacian = zeros(N, 1);
                laplacian(2:N-1) = psi(1:N-2) - 2*psi(2:N-1) + psi(3:N);
                laplacian(1) = psi(2) - 2*psi(1);
                laplacian(N) = psi(N-1) - 2*psi(N);
                laplacian = laplacian / (dx^2);
                
                % 2. 非线性项 |ψ|²*ψ
                psiAbs = abs(psi);
                psiAbs = min(psiAbs, 10);  % 限制幅度避免溢出
                nonlinear = beta * (psiAbs.^2) .* psi;
                
                % 3. NLS更新
                dpsi = 1i * (alpha * laplacian + nonlinear);
                
                % 4. 添加噪声
                noise = noiseLevel * (randn(N, 1) + 1i*randn(N, 1)) / sqrt(2);
                
                % 5. 更新状态（欧拉法）
                psi = psi + dt * (dpsi + noise);
                
                % 记录振幅演化
                obj.psiHistory{end+1} = abs(psi);
            end
            
            obj.psi = psi;
            obj.psiEvolution = cell2mat(obj.psiHistory')';  % N x steps 矩阵
            
            fprintf('演化完成: %d 步\n', steps);
        end
        
        function [freqs, spectrum] = spectralAnalysis(obj, psi)
            % spectralAnalysis 频谱分析
            %
            % 输入:
            %   psi - 复振幅（可选，默认使用最终状态）
            %
            % 输出:
            %   freqs   - 频率轴
            %   spectrum - 振幅谱
            
            if ~exist('psi', 'var') || isempty(psi)
                psi = obj.psi;
            end
            
            % FFT变换
            spectrum = fft(psi);
            
            % 频率轴
            N = length(psi);
            freqs = fftfreq(N, obj.params.dx);
            
            % 取正半轴
            positiveIdx = freqs >= 0;
            freqs = freqs(positiveIdx);
            spectrum = abs(spectrum(positiveIdx));
            
            obj.spectrum = spectrum;
            obj.freqs = freqs;
        end
        
        function width = computeSpectralWidth(obj)
            % computeSpectralWidth 计算谱宽
            %
            % 谱宽 = sqrt(Σ(f - f_mean)²·S(f) / ΣS(f))
            %
            % 输出:
            %   width - 谱宽值
            
            if isempty(obj.spectrum)
                obj.spectralAnalysis();
            end
            
            spectrumPower = obj.spectrum.^2;
            freqs = obj.freqs;
            
            % 计算加权均值
            totalPower = sum(spectrumPower);
            if totalPower < 1e-10
                warning('谱功率过低，可能存在数值问题');
                width = 0;
                return;
            end
            
            meanFreq = sum(freqs .* spectrumPower) / totalPower;
            
            % 计算方差
            variance = sum((freqs - meanFreq).^2 .* spectrumPower) / totalPower;
            width = sqrt(variance);
            
            obj.spectralWidth = width;
            obj.meanFrequency = meanFreq;
        end
        
        function resonance = detectResonance(obj)
            % detectResonance 检测共振峰
            %
            % 输出:
            %   resonance - 结构体，包含:
            %       peakFrequencies - 共振频率
            %       peakAmplitudes  - 共振振幅
            %       numPeaks        - 共振峰数量
            
            if isempty(obj.spectrum)
                obj.spectralAnalysis();
            end
            
            spectrumPower = obj.spectrum.^2;
            threshold = mean(spectrumPower) * 2;
            
            peakIndices = [];
            for i = 2:length(spectrumPower)-1
                if spectrumPower(i) > spectrumPower(i-1) && ...
                   spectrumPower(i) > spectrumPower(i+1) && ...
                   spectrumPower(i) > threshold
                    peakIndices = [peakIndices, i]; %#ok<AGROW>
                end
            end
            
            resonance = struct();
            resonance.peakFrequencies = obj.freqs(peakIndices);
            resonance.peakAmplitudes = obj.spectrum(peakIndices);
            resonance.numPeaks = length(peakIndices);
        end
        
        function acf = computeAutocorrelation(obj, psi)
            % computeAutocorrelation 计算自相关函数
            %
            % 输入:
            %   psi - 复振幅（可选）
            %
            % 输出:
            %   acf - 自相关函数
            
            if ~exist('psi', 'var') || isempty(psi)
                psi = obj.psi;
            end
            
            absPsi = abs(psi);
            acf = xcorr(absPsi, absPsi, 'coeff');
            acf = acf(length(absPsi):end);  % 取正半部分
        end
    end
end
