function write_json_file(path, s)
% write_json_file  Write a MATLAB struct/array to UTF-8 JSON.
    if nargin < 2
        error('write_json_file: need path and value');
    end
    d = fileparts(path);
    if ~isempty(d) && ~exist(d,'dir'), mkdir(d); end
    txt = jsonencode(s);
    fid = fopen(path,'w','n','UTF-8');
    if fid < 0
        error('write_json_file: cannot write %s', path);
    end
    fprintf(fid,'%s\n',txt);
    fclose(fid);
end
