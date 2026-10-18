function s = utc_now()
% utc_now  Current UTC timestamp in ISO-8601 without fractional seconds.
    s = char(datetime('now','TimeZone','UTC', ...
        'Format','yyyy-MM-dd''T''HH:mm:ss''Z'''));
end
