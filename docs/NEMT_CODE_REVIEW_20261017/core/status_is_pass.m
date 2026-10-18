function tf = status_is_pass(path, criterionPrefix)
% status_is_pass  Read a frozen-schema verdict and test one criterion.
%
%   tf = status_is_pass(path, 'C4.3')
%
% Missing file or criterion -> false. Comparison is on the exact prefix.

    tf = false;
    if ~exist(path,'file'), return; end
    T = readtable(path,'Delimiter',',','TextType','string', ...
                  'VariableNamingRule','preserve');
    if isempty(T) || ~all(ismember({'criterion','status'},T.Properties.VariableNames))
        return;
    end
    idx = find(startsWith(T.criterion, criterionPrefix),1);
    if isempty(idx), return; end
    tf = strcmpi(T.status(idx),'PASS');
end
