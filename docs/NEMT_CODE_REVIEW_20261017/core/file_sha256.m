function h = file_sha256(path)
% file_sha256  SHA-256 of a file, as a lowercase hex string.
%
% Uses the JDK MessageDigest bundled with MATLAB. This avoids shell quoting
% problems when paths contain spaces (the previous lab directory does).

    if ~exist(path,'file')
        error('file_sha256: missing file %s', path);
    end
    md = java.security.MessageDigest.getInstance('SHA-256');
    fid = fopen(path,'r');
    if fid < 0
        error('file_sha256: cannot read %s', path);
    end
    cleaner = onCleanup(@() fclose(fid));
    while true
        buf = fread(fid, 1024*1024, '*uint8');
        if isempty(buf), break; end
        md.update(buf);
    end
    clear cleaner;
    d = typecast(md.digest(),'uint8');
    h = lower(reshape(dec2hex(d,2)',1,[]));
end
