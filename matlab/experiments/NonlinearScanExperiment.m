classdef NonlinearScanExperiment
    %NonlinearScanExperiment 非线性扫描实验
    %
    % 目的：研究非线性效应（情绪/杠杆/羊群）对市场的影响
    %
    % 预期观察：
    %   - β增大：可能出现孤子结构
    %   - β增大：局部价格聚集
    %   - 高β：谱峰分裂
    
    properties
        priceData              % 原始价格数据
        betaValues            % β值列表
        results               % 实验结果
    end
    
    methods
        function obj = NonlinearScanExperiment(priceData, betaValues)
            % 构造函数
            obj.priceData = priceData;
            if nargin >= 2 && ~isempty(betaValues)
                obj.betaValues = betaValues;
            else
                obj.betaValues = [0.1, 0.5, 1.0, 2.0, 5.0, 10.0];
            end
        end
        
        function obj = run(obj)
            % run 执行非线性扫描实验
            
            fprintf('\n');
            fprintf('========================================================\n');
            fprintf('实验2：非线性强度扫描\n');
            fprintf('目的：观察不同非线性强度下的市场结构\n');
            fprintf('========================================================\n');
            
            obj.results = [];
            
            for i = 1:length(obj.betaValues)
                beta = obj.betaValues(i);
                fprintf('[%d/%d] 非线性强度 β = %.2f\n', i, length(obj.betaValues), beta);
                
                % 创建模拟器
                params = NEMTParams(0.1, beta, 0.2, 0.01, 1.0, 200);
                sim = NEMTSimulator(params);
                
                % 初始化
                psi = sim.initializeState(obj.priceData);
                
                % 演化
                psi = sim.evolve(psi);
                
                % 频谱分析
                [freqs, spectrum] = sim.spectralAnalysis(psi);
                width = sim.computeSpectralWidth();
                resonance = sim.detectResonance();
                
                % 保存结果
                result = struct();
                result.beta = beta;
                result.params = params;
                result.spectralWidth = width;
                result.meanFrequency = sim.meanFrequency;
                result.resonance = resonance;
                result.spectrum = spectrum;
                result.freqs = freqs;
                result.psi = psi;
                result.evolution = sim.psiEvolution;
                
                obj.results = [obj.results, result]; %#ok<AGROW>
                
                fprintf('    谱宽: %.6f, 共振峰: %d\n', width, resonance.numPeaks);
            end
            
            obj.analyze();
        end
        
        function summary = analyze(obj)
            % analyze 分析实验结果
            
            fprintf('\n');
            fprintf('========================================================\n');
            fprintf('非线性扫描分析\n');
            fprintf('========================================================\n');
            
            widths = [obj.results.spectralWidth];
            
            % 谱宽随β变化
            fprintf('\n谱宽随β变化:\n');
            for i = 1:length(obj.betaValues)
                fprintf('  β = %6.2f: 谱宽 = %.6f\n', ...
                    obj.betaValues(i), widths(i));
            end
            
            % 检测孤子特征（谱峰数量变化）
            peakCounts = arrayfun(@(x) x.numPeaks, obj.results);
            peakChanges = diff(peakCounts);
            
            idx = find(peakChanges < 0, 1);
            if ~isempty(idx)
                fprintf('\n警告: 在 β = %.2f → %.2f 出现谱峰分裂\n', ...
                    obj.betaValues(idx), obj.betaValues(idx+1));
                fprintf('这可能表明孤子结构形成\n');
            end
            
            % 寻找最优β（谱宽最小=最稳定）
            [minWidth, minIdx] = min(widths);
            fprintf('\n最小谱宽: β = %.2f, 宽度 = %.6f\n', ...
                obj.betaValues(minIdx), minWidth);
            
            % 返回摘要
            summary = struct();
            summary.betaValues = obj.betaValues;
            summary.spectralWidths = widths;
            summary.resonanceCounts = peakCounts;
            summary.minBeta = obj.betaValues(minIdx);
            summary.minWidth = minWidth;
        end
    end
end
