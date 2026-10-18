function E = environment_info(root)
% environment_info  Reproducibility environment block.
    E=struct();
    E.createdAtUtc=utc_now();
    E.matlabVersion=version;
    E.matlabRelease=version('-release');
    E.computer=computer;
    E.platform=system_dependent('getos');
    E.javaVersion=version('-java');
    E.maxNumCompThreads=maxNumCompThreads;
    E.workingDirectory=root;
    try
        rt=java.lang.Runtime.getRuntime();
        E.javaMaxMemoryBytes=double(rt.maxMemory());
        E.javaAvailableProcessors=double(rt.availableProcessors());
    catch
        E.javaMaxMemoryBytes=NaN;
        E.javaAvailableProcessors=NaN;
    end
    E.gitCommit=git_commit(root);
    E.codeTreeSha256=code_tree_hash(root);
end

function s=git_commit(root)
    [st,out]=system(sprintf('git -C "%s" rev-parse HEAD 2>/dev/null',root));
    if st==0
        s=strtrim(out);
    else
        s='not-a-git-repository';
    end
end
