function manifest = finalize_run(runDir, status, message, env, startUtc)
% finalize_run  Write file hashes, SHA256SUMS.txt and run_manifest.json.
%
% runDir already contains tests/, exp4/, exp5/, exp6/ as applicable.

    if ~exist(runDir,'dir'), mkdir(runDir); end
    files=dir(fullfile(runDir,'**','*'));
    rec=struct('path',{},'bytes',{},'sha256',{});
    for i=1:numel(files)
        f=fullfile(files(i).folder,files(i).name);
        if files(i).isdir, continue; end
        rel=erase(f,[runDir filesep]);
        if strcmp(rel,'SHA256SUMS.txt')||strcmp(rel,'run_manifest.json')
            continue;
        end
        rec(end+1)=struct('path',rel,'bytes',files(i).bytes, ...
            'sha256',file_sha256(f)); %#ok<AGROW>
    end
    [~,ord]=sort({rec.path});
    rec=rec(ord);

    manifest=struct();
    manifest.runId=env.runId;
    manifest.status=status;
    manifest.message=message;
    manifest.startUtc=startUtc;
    manifest.finishedUtc=utc_now();
    manifest.environment=env;
    manifest.codeHash=env.codeHash;
    manifest.runDirectory=runDir;
    manifest.files=rec;
    manifest.verdicts=collect_verdicts(runDir);
    write_json_file(fullfile(runDir,'run_manifest.json'),manifest);

    fid=fopen(fullfile(runDir,'SHA256SUMS.txt'),'w','n','UTF-8');
    if fid>=0
        for i=1:numel(rec)
            fprintf(fid,'%s  %s\n',rec(i).sha256,rec(i).path);
        end
        fprintf(fid,'%s  %s\n',file_sha256(fullfile(runDir,'run_manifest.json')), ...
            'run_manifest.json');
        fclose(fid);
    end
end

function V=collect_verdicts(runDir)
    names={'exp4/exp4_verdict.csv','exp5/exp5_verdict.csv','exp6/exp6_verdict.csv'};
    V=struct('experiment',{},'path',{},'criteria',{},'statuses',{});
    for k=1:numel(names)
        f=fullfile(runDir,names{k});
        if ~exist(f,'file'), continue; end
        T=readtable(f,'Delimiter',',','TextType','string', ...
            'VariableNamingRule','preserve');
        V(end+1)=struct('experiment',erase(names{k},'/'), ...
            'path',names{k},'criteria',T.criterion,'statuses',T.status); %#ok<AGROW>
    end
end
