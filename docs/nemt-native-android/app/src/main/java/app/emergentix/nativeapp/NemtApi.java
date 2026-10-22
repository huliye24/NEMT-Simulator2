package app.emergentix.nativeapp;

import android.content.Context;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

final class NemtApi {
    static final String BASE_URL = "https://postyouth.club/api/v1";
    private static final String PREFS = "emergentix_session";
    private static final String COOKIE_KEY = "session_cookie";
    private final Context context;

    NemtApi(Context context) {
        this.context = context.getApplicationContext();
    }

    AccountSnapshot balances() throws Exception {
        HttpURLConnection connection = open("/account/balances", "GET");
        JSONObject json = response(connection);
        JSONArray items = json.getJSONArray("balances");
        List<Balance> balances = new ArrayList<>();
        for (int i = 0; i < items.length(); i++) {
            JSONObject item = items.getJSONObject(i);
            double total = item.optDouble("total", 0d);
            if (Math.abs(total) < 0.00000001d) continue;
            balances.add(new Balance(
                    item.getString("asset"),
                    item.optDouble("free", 0d),
                    item.optDouble("locked", 0d),
                    total));
        }
        return new AccountSnapshot(
                json.optBoolean("connected", false),
                json.optString("source", "none"),
                json.optString("fetched_at", ""),
                json.optBoolean("stale", true),
                balances);
    }

    Ticker ticker(String symbol) throws Exception {
        HttpURLConnection connection = open("/market/ticker?symbol=" + symbol, "GET");
        JSONObject json = response(connection);
        return new Ticker(
                symbol,
                json.optDouble("last_price", 0d),
                json.optDouble("price_change_percent", 0d),
                json.optBoolean("stale", true));
    }

    void login(String username, String password) throws Exception {
        HttpURLConnection connection = open("/auth/login", "POST");
        connection.setDoOutput(true);
        JSONObject body = new JSONObject();
        body.put("username", username);
        body.put("password", password);
        byte[] bytes = body.toString().getBytes(StandardCharsets.UTF_8);
        try (OutputStream stream = connection.getOutputStream()) {
            stream.write(bytes);
        }
        response(connection);
        String setCookie = connection.getHeaderField("Set-Cookie");
        if (setCookie == null || setCookie.isEmpty()) {
            throw new ApiException(401, "服务器没有返回登录会话");
        }
        String cookie = setCookie.split(";", 2)[0];
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
                .edit().putString(COOKIE_KEY, cookie).apply();
    }

    void clearSession() {
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
                .edit().remove(COOKIE_KEY).apply();
    }

    private HttpURLConnection open(String path, String method) throws Exception {
        HttpURLConnection connection = (HttpURLConnection) new URL(BASE_URL + path).openConnection();
        connection.setRequestMethod(method);
        connection.setConnectTimeout(10000);
        connection.setReadTimeout(15000);
        connection.setRequestProperty("Accept", "application/json");
        connection.setRequestProperty("Content-Type", "application/json");
        connection.setRequestProperty("User-Agent", "Emergentix-Account/1.2.0 Android");
        String cookie = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE)
                .getString(COOKIE_KEY, "");
        if (!cookie.isEmpty()) connection.setRequestProperty("Cookie", cookie);
        return connection;
    }

    private JSONObject response(HttpURLConnection connection) throws Exception {
        int status = connection.getResponseCode();
        InputStream stream = status >= 200 && status < 300
                ? connection.getInputStream() : connection.getErrorStream();
        StringBuilder text = new StringBuilder();
        if (stream != null) {
            try (BufferedReader reader = new BufferedReader(
                    new InputStreamReader(stream, StandardCharsets.UTF_8))) {
                String line;
                while ((line = reader.readLine()) != null) text.append(line);
            }
        }
        if (status < 200 || status >= 300) {
            String message = "请求失败（HTTP " + status + "）";
            try {
                message = new JSONObject(text.toString())
                        .getJSONObject("error").optString("message", message);
            } catch (Exception ignored) { }
            throw new ApiException(status, message);
        }
        return new JSONObject(text.toString());
    }

    static final class ApiException extends Exception {
        final int status;
        ApiException(int status, String message) { super(message); this.status = status; }
    }

    static final class Balance {
        final String asset;
        final double free;
        final double locked;
        final double total;
        Balance(String asset, double free, double locked, double total) {
            this.asset = asset; this.free = free; this.locked = locked; this.total = total;
        }
    }

    static final class AccountSnapshot {
        final boolean connected;
        final String source;
        final String fetchedAt;
        final boolean stale;
        final List<Balance> balances;
        AccountSnapshot(boolean connected, String source, String fetchedAt, boolean stale, List<Balance> balances) {
            this.connected = connected; this.source = source; this.fetchedAt = fetchedAt;
            this.stale = stale; this.balances = balances;
        }
    }

    static final class Ticker {
        final String symbol;
        final double price;
        final double changePercent;
        final boolean stale;
        Ticker(String symbol, double price, double changePercent, boolean stale) {
            this.symbol = symbol; this.price = price; this.changePercent = changePercent; this.stale = stale;
        }
    }
}
