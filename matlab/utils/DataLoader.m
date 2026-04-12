classdef DataLoader
    %DataLoader 数据加载工具
    
    methods (Static)
        function data = loadMAT(filepath)
            % loadMAT 从.mat文件加载数据（推荐格式）
            %
            % 输入:
            %   filepath - .mat文件路径
            %
            % 输出:
            %   data - 结构体，包含:
            %       timestamp - datetime数组
            %       open - 开盘价
            %       high - 最高价
            %       low - 最低价
            %       close - 收盘价
            %       volume - 成交量
            %       symbol - 交易对
            %       interval - 周期
            
            fprintf('加载MAT文件: %s\n', filepath);
            
            if ~isfile(filepath)
                error('文件不存在: %s', filepath);
            end
            
            raw = load(filepath);
            
            % 提取数据字段
            fields = {'timestamp', 'open', 'high', 'low', 'close', 'volume'};
            data = struct();
            
            for i = 1:length(fields)
                field = fields{i};
                if isfield(raw, field)
                    data.(field) = raw.(field);
                end
            end
            
            % 显示时间范围
            if isfield(raw, 'timestamp') && ~isempty(raw.timestamp)
                if isdatetime(raw.timestamp(1))
                    fprintf('时间范围: %s ~ %s\n', ...
                        datestr(raw.timestamp(1)), datestr(raw.timestamp(end)));
                else
                    fprintf('时间范围: %s ~ %s\n', ...
                        datestr(raw.timestamp(1)), datestr(raw.timestamp(end)));
                end
            end
            
            fprintf('加载完成: %d 条数据\n', length(data.timestamp));
            
            % 显示附加信息
            if isfield(raw, 'symbol')
                fprintf('交易对: %s\n', raw.symbol);
            end
            if isfield(raw, 'interval')
                fprintf('周期: %s\n', raw.interval);
            end
        end
        
        function data = loadCSV(filepath)
            % loadCSV 从CSV文件加载数据
            %
            % 输入:
            %   filepath - CSV文件路径
            %
            % 输出:
            %   data - 结构体，包含:
            %       timestamp - 时间戳
            %       open - 开盘价
            %       high - 最高价
            %       low - 最低价
            %       close - 收盘价
            %       volume - 成交量
            
            fprintf('加载数据: %s\n', filepath);
            
            if ~isfile(filepath)
                error('文件不存在: %s', filepath);
            end
            
            opts = detectImportOptions(filepath);
            opts = setvartype(opts, 'double');
            
            T = readtable(filepath, opts);
            
            % 转换为结构体
            data = struct();
            data.timestamp = T.timestamp;
            data.open = T.open;
            data.high = T.high;
            data.low = T.low;
            data.close = T.close;
            data.volume = T.volume;
            
            fprintf('加载完成: %d 条数据\n', height(T));
            timeRange = [data.timestamp(1), data.timestamp(end)];
            fprintf('时间范围: %s ~ %s\n', datestr(timeRange(1)), datestr(timeRange(2)));
        end
        
        function data = load(filepath)
            % load 自动检测格式并加载
            %
            % 支持格式:
            %   - .mat 文件（推荐）
            %   - .csv 文件
            
            [~, ~, ext] = fileparts(filepath);
            
            switch lower(ext)
                case '.mat'
                    data = DataLoader.loadMAT(filepath);
                case '.csv'
                    data = DataLoader.loadCSV(filepath);
                otherwise
                    error('不支持的文件格式: %s', ext);
            end
        end
        
        function data = loadFromDir(dirpath, symbol, interval)
            % loadFromDir 从目录加载特定交易对和周期的数据
            
            filename = fullfile(dirpath, [symbol '_' interval '.csv']);
            data = DataLoader.loadCSV(filename);
        end
        
        function symbolList = listAvailableData(dirpath)
            % listAvailableData 列出可用的数据文件
            
            files = dir(fullfile(dirpath, '*.csv'));
            symbolList = unique(cellfun(@(x) strtok(x, '_'), {files.name}, 'UniformOutput', false));
            symbolList = symbolList(~strcmp(symbolList, 'btc'));  % 移除可能匹配的情况
            
            fprintf('可用数据:\n');
            for i = 1:length(files)
                [sym, remain] = strtok(files(i).name, '_');
                interval = strtok(remain, '.');
                fprintf('  %s %s\n', sym, interval);
            end
        end
    end
end
