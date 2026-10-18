function write_verdict(path, rows)
% write_verdict  Write the frozen verdict schema.
%
%   rows : n x 5 cell array
%          {criterion, observed, threshold, status, notes}
%
%   status is one of PASS, FAIL, INCONCLUSIVE, BLOCKED, INVALID, PENDING.
%   All values are written as UTF-8 CSV. Floats use 17 significant digits
%   through write_csv_table.

    allowed = {'PASS','FAIL','INCONCLUSIVE','BLOCKED','INVALID','PENDING','FRAGILE'};
    if size(rows,2) ~= 5
        error('write_verdict: rows must have five columns');
    end
    for i = 1:size(rows,1)
        st = upper(char(rows{i,4}));
        if ~any(strcmp(st,allowed))
            error('write_verdict: bad status "%s" for %s', st, char(rows{i,1}));
        end
        rows{i,4} = st;
    end
    write_csv_table(path, ...
        {'criterion','observed','threshold','status','notes'}, rows);
end
