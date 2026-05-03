% initNEMT.m - NEMT工具箱初始化脚本

fprintf('NEMT Toolbox - 初始化\n');

scriptDir = fileparts(mfilename('fullpath'));

% 添加工具箱根目录
addpath(scriptDir);

% 递归添加所有子目录
subdirs = genpath(scriptDir);
addpath(subdirs);

fprintf('类检查:\n');
classes = {'NEMTParams', 'NEMTSimulator', 'NoiseScanExperiment', ...
    'NonlinearScanExperiment', 'NEMTVisualizer', 'DataLoader', 'NEMTAnalyzer'};

for i = 1:length(classes)
    try
        eval([classes{i} '([]);']);
        fprintf('  OK: %s\n', classes{i});
    catch
        fprintf('  FAIL: %s\n', classes{i});
    end
end

fprintf('\n使用: NEMTAnalyzer.run\n');
