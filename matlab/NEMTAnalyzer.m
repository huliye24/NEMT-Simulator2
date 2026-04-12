% NEMTAnalyzer.m - 主分析程序
% NEMT分析主程序 - 结合噪声扫描和非线性扫描实验
%
% 使用方法:
%   1. 首先用Python获取数据: python binance_fetcher.py
%   2. 在MATLAB中运行: NEMTAnalyzer.run('BTC', '1h')

classdef NEMTAnalyzer < handle
    %NEMTAnalyzer NEMT分析主程序
    
    properties
        symbol              % 交易对符号
        interval            % 时间周期
        data                % 加载的价格数据
        noiseExp            % 噪声扫描实验
        nonlinearExp        % 非线性扫描实验
    end
    
    methods
        function obj = NEMTAnalyzer(symbol, interval)
            % 构造函数
            if nargin < 1 || isempty(symbol)
                symbol = 'BTC';
            end
            if nargin < 2 || isempty(interval)
                interval = '1h';
            end
            obj.symbol = symbol;
            obj.interval = interval;
        end
        
        function obj = loadData(obj, datapath)
            % loadData 加载数据（支持.mat和.csv格式）
            %
            % 输入:
            %   datapath - 数据目录、文件路径或空的（自动查找）
            %
            % 优先级:
            %   1. .mat 文件（推荐，日期类型完整保留）
            %   2. .csv 文件（备选）
            
            if nargin < 2
                datapath = 'matlab_data';
            end
            
            % 检查路径是否存在，不存在则往上级目录找
            if ~isfolder(datapath) && ~isfile(datapath)
                parentPath = fullfile(fileparts(mfilename('fullpath')), '..', datapath);
                if isfolder(parentPath)
                    datapath = parentPath;
                elseif isfile(parentPath)
                    datapath = parentPath;
                end
            end
            
            filepath = '';
            
            if isdir(datapath)
                % 目录模式：优先查找.mat文件
                matPath = fullfile(datapath, [obj.symbol '_' obj.interval '.mat']);
                csvPath = fullfile(datapath, [obj.symbol '_' obj.interval '.csv']);
                
                if isfile(matPath)
                    filepath = matPath;
                elseif isfile(csvPath)
                    filepath = csvPath;
                else
                    error('数据目录中未找到 %s_%s 的数据文件', obj.symbol, obj.interval);
                end
            else
                % 文件路径模式
                filepath = datapath;
            end
            
            % 使用DataLoader加载（自动识别格式）
            dataStruct = DataLoader.load(filepath);
            obj.data = dataStruct.close;  % 提取收盘价序列
            
            fprintf('数据加载完成: %d 个数据点\n', length(obj.data));
        end
        
        function obj = runNoiseScan(obj, noiseLevels)
            % runNoiseScan 运行噪声扫描实验
            
            if isempty(obj.data)
                error('请先加载数据: loadData()');
            end
            
            if nargin < 2
                noiseLevels = [0, 0.1, 0.2, 0.3, 0.5, 0.8, 1.0, 1.5];
            end
            
            obj.noiseExp = NoiseScanExperiment(obj.data, noiseLevels);
            obj.noiseExp.run();
        end
        
        function obj = runNonlinearScan(obj, betaValues)
            % runNonlinearScan 运行非线性扫描实验
            
            if isempty(obj.data)
                error('请先加载数据: loadData()');
            end
            
            if nargin < 2
                betaValues = [0.1, 0.5, 1.0, 2.0, 5.0, 10.0];
            end
            
            obj.nonlinearExp = NonlinearScanExperiment(obj.data, betaValues);
            obj.nonlinearExp.run();
        end
        
        function obj = runAll(obj, varargin)
            % runAll 运行全部实验
            
            fprintf('\n');
            fprintf('╔══════════════════════════════════════════════════════════╗\n');
            fprintf('║         NEMT 市场分析 - 完整实验流程                      ║\n');
            fprintf('╠══════════════════════════════════════════════════════════╣\n');
            fprintf('║  交易对: %s    周期: %s                              ║\n', obj.symbol, obj.interval);
            fprintf('╚══════════════════════════════════════════════════════════╝\n');
            
            % 加载数据
            if ~isempty(varargin)
                obj.loadData(varargin{1});
            else
                obj.loadData();
            end
            
            % 运行噪声扫描
            obj.runNoiseScan();
            
            % 运行非线性扫描
            obj.runNonlinearScan();
            
            % 可视化结果
            obj.visualize();
        end
        
        function h = visualize(obj, varargin)
            % visualize 可视化实验结果
            
            if ~isempty(obj.noiseExp) && ~isempty(obj.noiseExp.results)
                fprintf('\n绘制噪声扫描结果...\n');
                h1 = NEMTVisualizer.plotNoiseExperiment(...
                    obj.noiseExp.results, obj.noiseExp.noiseLevels);
                h1.Name = '噪声扫描实验';
            end
            
            if ~isempty(obj.nonlinearExp) && ~isempty(obj.nonlinearExp.results)
                fprintf('\n绘制非线性扫描结果...\n');
                h2 = NEMTVisualizer.plotNonlinearExperiment(...
                    obj.nonlinearExp.results, obj.nonlinearExp.betaValues);
                h2.Name = '非线性扫描实验';
            end
        end
        
        function report = generateReport(obj)
            % generateReport 生成分析报告
            
            fprintf('\n');
            fprintf('========================================================\n');
            fprintf('NEMT分析报告\n');
            fprintf('交易对: %s | 周期: %s\n', obj.symbol, obj.interval);
            fprintf('========================================================\n');
            
            report = struct();
            
            if ~isempty(obj.noiseExp) && ~isempty(obj.noiseExp.results)
                fprintf('\n【噪声扫描】\n');
                widths = [obj.noiseExp.results.spectralWidth];
                [minW, idx] = min(widths);
                fprintf('  最稳定噪声水平: η = %.2f (谱宽=%.6f)\n', ...
                    obj.noiseExp.noiseLevels(idx), minW);
                report.bestNoise = obj.noiseExp.noiseLevels(idx);
                report.noiseWidths = widths;
            end
            
            if ~isempty(obj.nonlinearExp) && ~isempty(obj.nonlinearExp.results)
                fprintf('\n【非线性扫描】\n');
                widths = [obj.nonlinearExp.results.spectralWidth];
                [minW, idx] = min(widths);
                fprintf('  最稳定非线性强度: β = %.2f (谱宽=%.6f)\n', ...
                    obj.nonlinearExp.betaValues(idx), minW);
                report.bestBeta = obj.nonlinearExp.betaValues(idx);
                report.betaWidths = widths;
            end
            
            fprintf('\n========================================================\n');
        end
    end
    
    methods (Static)
        function analyzer = run(symbol, interval, datapath)
            % run 快捷运行函数 - 一键分析
            %
            % 示例:
            %   NEMTAnalyzer.run          % 一键运行（使用默认BTC_1h.csv）
            %   NEMTAnalyzer.run('ETH')   % 指定交易对
            %   NEMTAnalyzer.run('BTC', '4h')  % 指定周期
            
            if ~exist('symbol', 'var') || isempty(symbol)
                symbol = 'BTC';
            end
            if ~exist('interval', 'var') || isempty(interval)
                interval = '1h';
            end
            
            analyzer = NEMTAnalyzer(symbol, interval);
            
            % 自动查找数据文件
            if exist('datapath', 'var') && ~isempty(datapath)
                analyzer.loadData(datapath);
            else
                % 尝试多个可能的数据目录
                possiblePaths = {
                    'matlab_data', ...
                    fullfile(fileparts(mfilename('fullpath')), '..', 'matlab_data'), ...
                    fullfile(fileparts(mfilename('fullpath')), '..', '..', 'matlab_data')
                };
                
                loaded = false;
                for i = 1:length(possiblePaths)
                    if isfolder(possiblePaths{i})
                        testFile = fullfile(possiblePaths{i}, [symbol '_' interval '.csv']);
                        if isfile(testFile)
                            fprintf('找到数据文件: %s\n', testFile);
                            analyzer.loadData(testFile);
                            loaded = true;
                            break;
                        end
                    end
                end
                
                if ~loaded
                    error('未找到数据文件 %s_%s.csv\n请先用Python获取数据: python binance_fetcher.py %s -i %s', ...
                        symbol, interval, symbol, interval);
                end
            end
            
            % 运行实验
            analyzer.runNoiseScan();
            analyzer.runNonlinearScan();
            analyzer.visualize();
            analyzer.generateReport();
        end
    end
end