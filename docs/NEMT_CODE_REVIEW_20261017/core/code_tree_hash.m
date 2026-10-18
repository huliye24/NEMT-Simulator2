function h = code_tree_hash(root)
% code_tree_hash  Combined SHA-256 of all .m and .py sources in the package.
%
% Excludes runs/, output/, data/ and hidden folders so results and downloaded
% files do not change the code identity.

    root=char(root);
    patterns={'**/*.m','**/*.py'};
    files={};
    for k=1:numel(patterns)
        d=dir(fullfile(root,patterns{k}));
        for i=1:numel(d)
            f=fullfile(d(i).folder,d(i).name);
            rel=erase(f,[root filesep]);
            if startsWith(rel,'runs')||startsWith(rel,'output')|| ...
               startsWith(rel,'data')||contains(rel,[filesep '.'])
                continue;
            end
            files{end+1}=f; %#ok<AGROW>
        end
    end
    files=sort(files);
    txt='';
    for i=1:numel(files)
        rel=erase(files{i},[root filesep]);
        txt=[txt rel ' ' file_sha256(files{i}) '\n']; %#ok<AGROW>
    end
    tmp=[tempname '.txt'];
    fid=fopen(tmp,'w'); fprintf(fid,'%s',txt); fclose(fid);
    h=file_sha256(tmp); delete(tmp);
end
