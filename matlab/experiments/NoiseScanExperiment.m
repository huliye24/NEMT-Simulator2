classdef NoiseScanExperiment
    %NoiseScanExperiment 噪声扫描实验
    %
    % 目的：研究不同噪声水平下的谱结构响应
    %
    % 预期观察：
    %   - 低噪声：清晰的谱结构
    %   - 高噪声：谱宽突然放大（相变）
    %   - 可能出现共振峰
    
    properties
        priceData              % 原始价格数据
        noiseLevels           % 噪声水平列表
        results               % 实验结果
    end
    
    methods
        function obj = NoiseScanExperiment(priceData, noiseLevels)
            % 构造函数
            obj.priceData = priceData;
            if nargin >= 2 && ~isempty(noiseLevels)
                obj.noiseLevels = noiseLevels;
            else
                obj.noiseLevels = [0, 0.1, 0.3, 0.5, 0.8, 1.0];
            end
        end
        
        function obj = run(obj)
            % run 执行噪声扫描实验
            
            fprintf('\n');
            fprintf('========================================================\n');
            fprintf('实验1：噪声扫描\n');
            fprintf('目的：观察不同噪声水平下的谱结构响应\n');
            fprintf('========================================================\n');
            
            obj.results = [];
            
            for i = 1:length(obj.noiseLevels)
                nl = obj.noiseLevels(i);
                fprintf('[%d/%d] 噪声水平 η = %.2f\n', i, length(obj.noiseLevels), nl);
                
                % 创建模拟器
                params = NEMTParams(0.1, 1.0, nl, 0.01, 1.0, 200);
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
                result.noiseLevel = nl;
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
            fprintf('噪声扫描分析\n');
            fprintf('========================================================\n');
            
            widths = [obj.results.spectralWidth];
            
            % 检测相变
            if length(widths) >= 3
                growthRates = diff(widths) ./ diff(obj.noiseLevels);
                [maxGrowth, maxIdx] = max(growthRates);
                
                fprintf('\n最大增长率: η = %.2f → %.2f\n', ...
                    obj.noiseLevels(maxIdx), obj.noiseLevels(maxIdx+1));
                fprintf('增长率: %.4f\n', maxGrowth);
                
                if maxGrowth > 0.1
                    fprintf('警告: 在 η = %.2f 附近可能存在结构相变\n', ...
                        obj.noiseLevels(maxIdx+1));
                end
            end
            
            % 共振峰统计
            fprintf('\n共振峰统计:\n');
            for i = 1:length(obj.noiseLevels)
                fprintf('  η = %.2f: %d 个共振峰\n', ...
                    obj.noiseLevels(i), obj.results(i).resonance.numPeaks);
            end
            
            % 返回摘要
            summary = struct();
            summary.noiseLevels = obj.noiseLevels;
            summary.spectralWidths = widths;
            summary.resonanceCounts = [obj.results.resonance];
            summary.resonanceCounts = arrayfun(@(x) x.numPeaks, obj.results);
        end
    end
end
