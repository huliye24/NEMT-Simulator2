function write_csv_table(path, header, rows)
% write_csv_table  Write a header plus a mixed numeric/text table to CSV.
%
%   write_csv_table(path, header, rows)
%
%   header : cell array of column names
%   rows   : numeric matrix, or cell array with one row per record.
%            Numeric cells are written with 17 significant digits; char and
%            string cells are written verbatim. NaN is written as NaN.
%
%   This helper exists so experiments do not each reinvent CSV writing; the
%   golden sample writer in io_tools.m keeps its own fixed numeric format.

    if nargin < 3
        error('write_csv_table: needs path, header, rows');
    end

    if isnumeric(rows)
        rows = num2cell(rows);
    end
    if ~iscell(rows)
        error('write_csv_table: rows must be numeric or a cell array');
    end
    if size(rows, 2) ~= numel(header)
        error('write_csv_table: %d columns of data but %d header names', ...
              size(rows,2), numel(header));
    end

    fid = fopen(path, 'w');
    if fid < 0
        error('write_csv_table: cannot write %s', path);
    end

    fprintf(fid, '%s', header{1});
    for c = 2:numel(header)
        fprintf(fid, ',%s', header{c});
    end
    fprintf(fid, '\n');

    for r = 1:size(rows, 1)
        for c = 1:size(rows, 2)
            v = rows{r,c};
            if isnumeric(v) || islogical(v)
                if isempty(v)
                    fprintf(fid, 'NaN');
                elseif isscalar(v)
                    if isnan(double(v))
                        fprintf(fid, 'NaN');
                    elseif isinf(double(v))
                        if v > 0, fprintf(fid, 'Inf'); else, fprintf(fid, '-Inf'); end
                    elseif islogical(v)
                        fprintf(fid, '%d', v);
                    else
                        fprintf(fid, '%.17g', double(v));
                    end
                else
                    error('write_csv_table: numeric cell values must be scalar');
                end
            elseif ischar(v)
                if contains(v, ',')
                    fprintf(fid, '"%s"', v);
                else
                    fprintf(fid, '%s', v);
                end
            elseif isstring(v)
                s = char(v);
                if contains(s, ',')
                    fprintf(fid, '"%s"', s);
                else
                    fprintf(fid, '%s', s);
                end
            else
                error('write_csv_table: unsupported cell type %s', class(v));
            end
            if c < size(rows,2)
                fprintf(fid, ',');
            end
        end
        fprintf(fid, '\n');
    end
    fclose(fid);
end
