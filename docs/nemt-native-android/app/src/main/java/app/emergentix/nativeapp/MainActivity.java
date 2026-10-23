package app.emergentix.nativeapp;

import android.app.Activity;
import android.app.AlertDialog;
import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.text.InputType;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.widget.FrameLayout;
import android.widget.EditText;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public final class MainActivity extends Activity {
    private static final int INK = Color.rgb(19, 24, 32);
    private static final int MUTED = Color.rgb(100, 116, 139);
    private static final int PAPER = Color.rgb(245, 247, 249);
    private static final int CYAN = Color.rgb(0, 175, 199);
    private static final int RED = Color.rgb(239, 68, 68);
    private static final int GREEN = Color.rgb(5, 150, 105);

    private FrameLayout content;
    private final List<TextView> tabs = new ArrayList<>();
    private final ExecutorService network = Executors.newSingleThreadExecutor();
    private final Handler main = new Handler(Looper.getMainLooper());
    private NemtApi api;
    private NemtApi.AccountSnapshot account;
    private final List<NemtApi.Ticker> tickers = new ArrayList<>();
    private int currentPage = 0;
    private boolean syncing = false;
    private String syncMessage = "等待同步";
    private TextView minimalBalance;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        api = new NemtApi(this);
        showMinimalHome();
        syncMinimal(false);
    }

    private void showMinimalHome() {
        getWindow().setStatusBarColor(Color.TRANSPARENT);
        getWindow().setNavigationBarColor(Color.TRANSPARENT);
        getWindow().getDecorView().setSystemUiVisibility(
                View.SYSTEM_UI_FLAG_FULLSCREEN
                        | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                        | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
                        | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                        | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                        | View.SYSTEM_UI_FLAG_LAYOUT_STABLE);

        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(Color.WHITE);

        ImageView character = new ImageView(this);
        character.setImageResource(R.drawable.emergentix_account_muse);
        character.setScaleType(ImageView.ScaleType.FIT_CENTER);
        character.setContentDescription("Emergentix muse");
        root.addView(character, new FrameLayout.LayoutParams(-1, -1));

        minimalBalance = text("1.09 U", 34, INK, true);
        minimalBalance.setGravity(Gravity.CENTER);
        minimalBalance.setPadding(dp(18), dp(10), dp(18), dp(10));
        minimalBalance.setBackgroundColor(Color.argb(225, 255, 255, 255));
        minimalBalance.setOnClickListener(view -> syncMinimal(false));
        FrameLayout.LayoutParams valueParams = new FrameLayout.LayoutParams(-2, -2, Gravity.BOTTOM | Gravity.CENTER_HORIZONTAL);
        valueParams.bottomMargin = dp(38);
        root.addView(minimalBalance, valueParams);

        setContentView(root);
    }

    private void syncMinimal(boolean afterLogin) {
        if (syncing) return;
        syncing = true;
        network.execute(() -> {
            try {
                NemtApi.AccountSnapshot snapshot = api.balances();
                double usdt = 0d;
                for (NemtApi.Balance balance : snapshot.balances) {
                    if (balance.asset.equals("USDT")) usdt += balance.total;
                }
                final double value = usdt;
                main.post(() -> {
                    account = snapshot;
                    syncing = false;
                    minimalBalance.setText(String.format(Locale.US, "%.2f U", value));
                });
            } catch (NemtApi.ApiException exception) {
                main.post(() -> {
                    syncing = false;
                    if (exception.status == 401 && !afterLogin) {
                        api.clearSession();
                        showMinimalLogin();
                    }
                });
            } catch (Exception ignored) {
                main.post(() -> syncing = false);
            }
        });
    }

    private void showMinimalLogin() {
        LinearLayout fields = column();
        fields.setPadding(dp(24), 0, dp(24), 0);
        EditText username = new EditText(this);
        username.setHint("账户");
        username.setSingleLine(true);
        EditText password = new EditText(this);
        password.setHint("密码");
        password.setSingleLine(true);
        password.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD);
        fields.addView(username);
        fields.addView(password);
        AlertDialog dialog = new AlertDialog.Builder(this)
                .setView(fields)
                .setNegativeButton("取消", null)
                .setPositiveButton("连接", null)
                .create();
        dialog.setOnShowListener(unused -> dialog.getButton(AlertDialog.BUTTON_POSITIVE)
                .setOnClickListener(view -> {
                    String user = username.getText().toString().trim();
                    String pass = password.getText().toString();
                    if (user.isEmpty() || pass.isEmpty()) return;
                    network.execute(() -> {
                        try {
                            api.login(user, pass);
                            main.post(() -> { dialog.dismiss(); syncMinimal(true); });
                        } catch (Exception ignored) { }
                    });
                }));
        dialog.show();
    }

    private View header() {
        LinearLayout bar = row();
        bar.setGravity(Gravity.CENTER_VERTICAL);
        bar.setPadding(dp(18), dp(10), dp(18), dp(10));
        bar.setBackgroundColor(Color.WHITE);

        ImageView logo = new ImageView(this);
        logo.setImageResource(R.drawable.emergentix_icon);
        logo.setScaleType(ImageView.ScaleType.CENTER_INSIDE);
        bar.addView(logo, new LinearLayout.LayoutParams(dp(42), dp(42)));

        LinearLayout names = column();
        names.setPadding(dp(10), 0, 0, 0);
        names.addView(text("EMERGENTIX", 18, INK, true));
        names.addView(tracking("ACCOUNT MONITOR · v1.1.0", 9, CYAN));
        bar.addView(names, new LinearLayout.LayoutParams(0, -2, 1f));

        TextView status = chip("●  CLOUD READY", CYAN, Color.rgb(232, 249, 251));
        bar.addView(status);
        return bar;
    }

    private View bottomNavigation() {
        LinearLayout nav = row();
        nav.setGravity(Gravity.CENTER);
        nav.setPadding(dp(8), dp(5), dp(8), dp(7));
        nav.setBackgroundColor(Color.WHITE);
        String[] icons = {"◫", "▥", "◇", "○"};
        String[] labels = {"总览", "资产", "策略", "提醒"};
        for (int i = 0; i < labels.length; i++) {
            final int index = i;
            TextView tab = text(icons[i] + "\n" + labels[i], 12, MUTED, false);
            tab.setGravity(Gravity.CENTER);
            tab.setPadding(0, dp(5), 0, dp(4));
            tab.setOnClickListener(view -> showPage(index));
            tabs.add(tab);
            nav.addView(tab, new LinearLayout.LayoutParams(0, -1, 1f));
        }
        return nav;
    }

    private void showPage(int index) {
        currentPage = index;
        content.removeAllViews();
        for (int i = 0; i < tabs.size(); i++) {
            tabs.get(i).setTextColor(i == index ? CYAN : MUTED);
            tabs.get(i).setTypeface(null, i == index ? Typeface.BOLD : Typeface.NORMAL);
        }
        View page;
        if (index == 0) page = portfolioPage();
        else if (index == 1) page = positionsPage();
        else if (index == 2) page = strategiesPage();
        else page = alertsPage();
        content.addView(page, new FrameLayout.LayoutParams(-1, -1));
    }

    private View portfolioPage() {
        LinearLayout page = page("账户总览", "ACCOUNT / OVERVIEW");
        page.addView(portfolioHero(), match(dp(390)));
        page.addView(sectionTitle("资产分布"));
        if (account == null || account.balances.isEmpty()) {
            page.addView(note("登录后显示币安账户中的非零资产。"));
        } else {
            for (NemtApi.Balance balance : account.balances) {
                page.addView(metricRow(balance.asset, quantity(balance.total),
                        balance.locked > 0 ? INK : GREEN));
            }
        }
        page.addView(sectionTitle("表现"));
        LinearLayout performance = card();
        performance.addView(tracking("PORTFOLIO PERFORMANCE", 9, CYAN));
        TextView unavailable = text("净值曲线等待历史快照", 18, INK, true);
        unavailable.setPadding(0, dp(14), 0, dp(8));
        performance.addView(unavailable);
        performance.addView(text("连接后从今天开始记录真实账户净值，不补造历史数据。", 12, MUTED, false));
        page.addView(performance, matchWrap());
        page.addView(sectionTitle("运行策略"));
        page.addView(strategyStatusCard());
        page.addView(sectionTitle("账户状态"));
        page.addView(note(syncMessage + "\n只读模式已开启，手机端不提供下单与策略部署。"));
        return scroll(page);
    }

    private View portfolioHero() {
        FrameLayout hero = new FrameLayout(this);
        hero.setBackgroundColor(Color.WHITE);

        ImageView character = new ImageView(this);
        character.setImageResource(R.drawable.emergentix_account_muse);
        character.setScaleType(ImageView.ScaleType.CENTER_CROP);
        character.setContentDescription("Emergentix account muse");
        hero.addView(character, new FrameLayout.LayoutParams(-1, -1));

        TextView refresh = chip(syncing ? "同步中…" : "↻  BINANCE", CYAN, Color.argb(235, 232, 249, 251));
        refresh.setOnClickListener(view -> refreshData(false));
        FrameLayout.LayoutParams refreshParams = new FrameLayout.LayoutParams(-2, -2, Gravity.TOP | Gravity.END);
        refreshParams.setMargins(0, dp(14), dp(14), 0);
        hero.addView(refresh, refreshParams);

        LinearLayout balance = column();
        balance.setPadding(dp(18), dp(14), dp(18), dp(14));
        balance.setBackgroundColor(Color.argb(238, 255, 255, 255));
        balance.addView(tracking("TOTAL BALANCE", 9, MUTED));
        balance.addView(text(account == null ? "—" : money(estimateNetValue()), 34, INK, true));
        balance.addView(text("USDT  ·  READ ONLY", 11, GREEN, true));
        FrameLayout.LayoutParams balanceParams = new FrameLayout.LayoutParams(dp(250), -2, Gravity.BOTTOM | Gravity.START);
        balanceParams.setMargins(dp(14), 0, 0, dp(14));
        hero.addView(balance, balanceParams);

        return hero;
    }

    private View positionsPage() {
        LinearLayout page = page("资产明细", "BINANCE / BALANCES");
        page.addView(syncControl());
        if (account == null || account.balances.isEmpty()) {
            page.addView(note("尚未取得币安余额，请登录或刷新。"));
        } else {
            for (NemtApi.Balance balance : account.balances) {
                LinearLayout card = card();
                card.addView(text(balance.asset, 22, INK, true));
                card.addView(metricRow("可用", quantity(balance.free), GREEN));
                card.addView(metricRow("锁定", quantity(balance.locked), MUTED));
                pageGap(card);
                page.addView(card);
            }
        }
        return scroll(page);
    }

    private View activityPage() {
        LinearLayout page = page("账户记录", "ACCOUNT / ACTIVITY");
        page.addView(syncControl());
        page.addView(activityCard(account == null ? "等待账户登录" : account.fetchedAt,
                "币安账户同步", account != null && account.connected ? "连接正常" : "未连接",
                account != null && account.connected ? GREEN : RED));
        page.addView(sectionTitle("说明"));
        page.addView(note("当前云端接口提供实时余额，但尚未提供账户净值历史。后续版本会由服务端保存快照，再显示真实日变化曲线。"));
        return scroll(page);
    }

    private View marketsPage() {
        LinearLayout page = page("市场", "MARKET / LIVE");
        page.addView(syncControl());
        if (tickers.isEmpty()) {
            page.addView(note("登录后同步币安实时行情。"));
        } else {
            for (NemtApi.Ticker ticker : tickers) {
                int color = ticker.changePercent < 0 ? RED : GREEN;
                page.addView(marketCard(ticker.symbol.replace("USDT", " / USDT"),
                        money(ticker.price), String.format(Locale.US, "%+.2f%%", ticker.changePercent), color));
            }
        }
        page.addView(sectionTitle("NEMT 市场结构"));
        page.addView(note("行情来自香港云端的 Binance 数据适配器。账户与行情均为只读同步。"));
        return scroll(page);
    }

    private View syncControl() {
        TextView control = chip(syncing ? "同步中…" : "↻  刷新账户", CYAN, Color.rgb(232, 249, 251));
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(-2, -2);
        params.bottomMargin = dp(12);
        control.setLayoutParams(params);
        control.setOnClickListener(view -> refreshData(false));
        return control;
    }

    private void refreshData(boolean afterLogin) {
        if (syncing) return;
        syncing = true;
        syncMessage = "正在连接币安账户…";
        showPage(currentPage);
        network.execute(() -> {
            try {
                NemtApi.AccountSnapshot nextAccount = api.balances();
                List<NemtApi.Ticker> nextTickers = new ArrayList<>();
                for (String symbol : new String[]{"BTCUSDT", "ETHUSDT", "SOLUSDT"}) {
                    try { nextTickers.add(api.ticker(symbol)); } catch (Exception ignored) { }
                }
                main.post(() -> {
                    account = nextAccount;
                    tickers.clear();
                    tickers.addAll(nextTickers);
                    syncing = false;
                    syncMessage = nextAccount.connected
                            ? "Binance 已连接 · " + nextAccount.fetchedAt
                            : "Binance 未连接";
                    showPage(currentPage);
                });
            } catch (NemtApi.ApiException exception) {
                main.post(() -> {
                    syncing = false;
                    if (exception.status == 401) {
                        api.clearSession();
                        if (!afterLogin) showLogin();
                    } else {
                        syncMessage = exception.getMessage();
                        showPage(currentPage);
                    }
                });
            } catch (Exception exception) {
                main.post(() -> {
                    syncing = false;
                    syncMessage = "同步失败，请检查网络";
                    showPage(currentPage);
                });
            }
        });
    }

    private void showLogin() {
        LinearLayout fields = column();
        fields.setPadding(dp(24), dp(8), dp(24), 0);
        EditText username = new EditText(this);
        username.setHint("Emergentix 账户");
        username.setSingleLine(true);
        EditText password = new EditText(this);
        password.setHint("密码");
        password.setSingleLine(true);
        password.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD);
        fields.addView(username);
        fields.addView(password);
        AlertDialog dialog = new AlertDialog.Builder(this)
                .setTitle("连接币安账户")
                .setMessage("通过 Emergentix 云端进行只读同步。App 不接触 Binance API Key。")
                .setView(fields)
                .setNegativeButton("稍后", null)
                .setPositiveButton("登录并同步", null)
                .create();
        dialog.setOnShowListener(unused -> dialog.getButton(AlertDialog.BUTTON_POSITIVE)
                .setOnClickListener(view -> {
                    String user = username.getText().toString().trim();
                    String pass = password.getText().toString();
                    if (user.isEmpty() || pass.isEmpty()) {
                        Toast.makeText(this, "请输入账户和密码", Toast.LENGTH_SHORT).show();
                        return;
                    }
                    dialog.getButton(AlertDialog.BUTTON_POSITIVE).setEnabled(false);
                    network.execute(() -> {
                        try {
                            api.login(user, pass);
                            main.post(() -> { dialog.dismiss(); refreshData(true); });
                        } catch (Exception exception) {
                            main.post(() -> {
                                dialog.getButton(AlertDialog.BUTTON_POSITIVE).setEnabled(true);
                                Toast.makeText(this, "登录失败：" + exception.getMessage(), Toast.LENGTH_LONG).show();
                            });
                        }
                    });
                }));
        dialog.show();
    }

    private double estimateNetValue() {
        if (account == null) return 0d;
        double result = 0d;
        for (NemtApi.Balance balance : account.balances) {
            if (balance.asset.equals("USDT") || balance.asset.equals("USDC") || balance.asset.equals("FDUSD")) {
                result += balance.total;
            } else {
                NemtApi.Ticker ticker = findTicker(balance.asset + "USDT");
                if (ticker != null) result += balance.total * ticker.price;
            }
        }
        return result;
    }

    private NemtApi.Ticker findTicker(String symbol) {
        for (NemtApi.Ticker ticker : tickers) if (ticker.symbol.equals(symbol)) return ticker;
        return null;
    }

    private String money(double value) { return String.format(Locale.US, "%,.2f", value); }
    private String quantity(double value) {
        if (Math.abs(value) >= 100d) return String.format(Locale.US, "%,.2f", value);
        return String.format(Locale.US, "%,.8f", value).replaceAll("0+$", "").replaceAll("\\.$", "");
    }

    private View strategiesPage() {
        LinearLayout page = page("策略", "AUTOMATION / CONTROL");
        page.addView(strategyStatusCard());
        page.addView(sectionTitle("可用策略"));
        page.addView(strategyChoice("NEMT 临界动量", "等待 Freqtrade 接入", "当前设计基线"));
        page.addView(strategyChoice("均线趋势", "尚未部署", "低频趋势跟随"));
        page.addView(strategyChoice("均值回归", "尚未部署", "震荡市场观察"));
        page.addView(sectionTitle("切换规则"));
        page.addView(note("只有在网站完成回测并发布的策略才会出现在这里。切换前检查持仓，手机端不能编辑参数或上传代码。"));
        return scroll(page);
    }

    private View alertsPage() {
        LinearLayout page = page("提醒", "ACCOUNT / ALERTS");
        page.addView(activityCard("实时", "账户连接", account != null && account.connected ? "Binance 正常" : "等待登录",
                account != null && account.connected ? GREEN : MUTED));
        page.addView(activityCard("安全", "只读保护", "已开启", GREEN));
        page.addView(activityCard("策略", "运行状态", "待接入", MUTED));
        page.addView(sectionTitle("以后只提醒重要变化"));
        page.addView(note("净值明显变化、策略启动或停止、持仓建立或关闭、风险保护触发。普通价格波动不打扰你。"));
        return scroll(page);
    }

    private View strategyStatusCard() {
        LinearLayout card = card();
        LinearLayout top = row();
        top.setGravity(Gravity.CENTER_VERTICAL);
        top.addView(tracking("ACTIVE STRATEGY", 9, CYAN), new LinearLayout.LayoutParams(0, -2, 1f));
        top.addView(chip("未连接", MUTED, Color.rgb(241, 245, 249)));
        card.addView(top);
        TextView title = text("策略引擎待接入", 21, INK, true);
        title.setPadding(0, dp(14), 0, dp(7));
        card.addView(title);
        card.addView(text("账户同步与策略执行分离，避免 App 误操作资金。", 12, MUTED, false));
        return card;
    }

    private View strategyChoice(String name, String status, String description) {
        LinearLayout card = card();
        LinearLayout top = row();
        top.setGravity(Gravity.CENTER_VERTICAL);
        top.addView(text(name, 17, INK, true), new LinearLayout.LayoutParams(0, -2, 1f));
        top.addView(chip(status, MUTED, Color.rgb(241, 245, 249)));
        card.addView(top);
        TextView detail = text(description, 12, MUTED, false);
        detail.setPadding(0, dp(9), 0, 0);
        card.addView(detail);
        pageGap(card);
        return card;
    }

    private View executionPage() {
        LinearLayout page = page("模拟盘", "PAPER TRADING / SAFE");
        LinearLayout hero = card();
        hero.addView(tracking("BUILT-IN NEMT", 10, CYAN));
        hero.addView(text("自动交易监控", 24, INK, true));
        hero.addView(text("策略运行中 · 当前无持仓", 13, MUTED, false));
        page.addView(hero, matchWrap());
        page.addView(sectionTitle("运行状态"));
        page.addView(metricRow("策略", "NEMT 临界动量", INK));
        page.addView(metricRow("风控", "已启用", GREEN));
        page.addView(metricRow("保证金率", "0.00%", MUTED));
        page.addView(metricRow("今日交易", "0", MUTED));
        page.addView(note("纯原生版不会自动继承网页缓存。实盘能力必须经过独立 API 鉴权与设备风控后才能开启。"));
        return scroll(page);
    }

    private LinearLayout page(String title, String eyebrow) {
        LinearLayout page = column();
        page.setPadding(dp(16), dp(18), dp(16), dp(24));
        page.addView(tracking(eyebrow, 9, CYAN));
        TextView heading = text(title, 28, INK, true);
        heading.setPadding(0, dp(5), 0, dp(18));
        page.addView(heading);
        return page;
    }

    private View marketCard(String symbol, String price, String change, int color) {
        LinearLayout card = card();
        LinearLayout top = row();
        top.setGravity(Gravity.CENTER_VERTICAL);
        top.addView(text(symbol, 16, INK, true), new LinearLayout.LayoutParams(0, -2, 1f));
        top.addView(chip(change, color, color == RED ? Color.rgb(254, 242, 242) : Color.rgb(236, 253, 245)));
        card.addView(top);
        TextView priceView = text(price, 30, INK, true);
        priceView.setPadding(0, dp(16), 0, 0);
        card.addView(priceView);
        pageGap(card);
        return card;
    }

    private View strategyCard(String number, String name, String version, String result, String sharpe, String risk) {
        LinearLayout card = card();
        LinearLayout title = row();
        title.setGravity(Gravity.CENTER_VERTICAL);
        title.addView(tracking(number, 10, CYAN));
        TextView nameView = text(name, 17, INK, true);
        nameView.setPadding(dp(14), 0, 0, 0);
        title.addView(nameView, new LinearLayout.LayoutParams(0, -2, 1f));
        title.addView(chip(risk + "风险", risk.equals("高") ? RED : CYAN, Color.rgb(239, 250, 252)));
        card.addView(title);
        card.addView(text(version + "  ·  BTC/USDT", 11, MUTED, false));
        LinearLayout stats = row();
        stats.setPadding(0, dp(14), 0, 0);
        stats.addView(text(result, 21, GREEN, true), new LinearLayout.LayoutParams(0, -2, 1f));
        stats.addView(text(sharpe, 12, MUTED, true));
        card.addView(stats);
        pageGap(card);
        return card;
    }

    private View metricRow(String label, String value, int color) {
        LinearLayout row = row();
        row.setGravity(Gravity.CENTER_VERTICAL);
        row.setPadding(dp(16), dp(15), dp(16), dp(15));
        row.setBackgroundColor(Color.WHITE);
        row.addView(text(label, 13, MUTED, false), new LinearLayout.LayoutParams(0, -2, 1f));
        row.addView(text(value, 14, color, true));
        return row;
    }

    private View changeRow(String date, String change, String balance) {
        LinearLayout row = row();
        row.setGravity(Gravity.CENTER_VERTICAL);
        row.setPadding(dp(16), dp(13), dp(16), dp(13));
        row.setBackgroundColor(Color.WHITE);
        row.addView(text(date, 13, MUTED, false), new LinearLayout.LayoutParams(0, -2, 1f));
        TextView delta = text(change + " USDT", 13, change.startsWith("-") ? RED : GREEN, true);
        delta.setGravity(Gravity.END);
        row.addView(delta, new LinearLayout.LayoutParams(dp(100), -2));
        TextView total = text(balance, 13, INK, true);
        total.setGravity(Gravity.END);
        row.addView(total, new LinearLayout.LayoutParams(dp(100), -2));
        return row;
    }

    private View activityCard(String time, String title, String value, int color) {
        LinearLayout card = card();
        LinearLayout line = row();
        line.setGravity(Gravity.CENTER_VERTICAL);
        LinearLayout copy = column();
        copy.addView(text(title, 16, INK, true));
        TextView timeView = text(time, 11, MUTED, false);
        timeView.setPadding(0, dp(5), 0, 0);
        copy.addView(timeView);
        line.addView(copy, new LinearLayout.LayoutParams(0, -2, 1f));
        line.addView(text(value, 14, color, true));
        card.addView(line);
        pageGap(card);
        return card;
    }

    private View note(String value) {
        TextView note = text(value, 13, MUTED, false);
        note.setLineSpacing(dp(3), 1f);
        note.setPadding(dp(16), dp(16), dp(16), dp(16));
        note.setBackgroundColor(Color.WHITE);
        return note;
    }

    private TextView sectionTitle(String value) {
        TextView title = tracking(value.toUpperCase(), 10, INK);
        title.setPadding(0, dp(24), 0, dp(10));
        return title;
    }

    private LinearLayout card() {
        LinearLayout card = column();
        card.setPadding(dp(18), dp(18), dp(18), dp(18));
        card.setBackgroundColor(Color.WHITE);
        return card;
    }

    private void pageGap(LinearLayout view) {
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(-1, -2);
        params.bottomMargin = dp(12);
        view.setLayoutParams(params);
    }

    private ScrollView scroll(View child) {
        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        scroll.setBackgroundColor(PAPER);
        scroll.addView(child, new ScrollView.LayoutParams(-1, -2));
        return scroll;
    }

    private LinearLayout row() { LinearLayout view = new LinearLayout(this); view.setOrientation(LinearLayout.HORIZONTAL); return view; }
    private LinearLayout column() { LinearLayout view = new LinearLayout(this); view.setOrientation(LinearLayout.VERTICAL); return view; }
    private LinearLayout.LayoutParams matchWrap() { return new LinearLayout.LayoutParams(-1, -2); }
    private LinearLayout.LayoutParams match(int height) { return new LinearLayout.LayoutParams(-1, height); }

    private TextView text(String value, int size, int color, boolean bold) {
        TextView view = new TextView(this);
        view.setText(value);
        view.setTextSize(size);
        view.setTextColor(color);
        view.setTypeface(Typeface.create("sans", bold ? Typeface.BOLD : Typeface.NORMAL));
        return view;
    }

    private TextView tracking(String value, int size, int color) {
        TextView view = text(value, size, color, true);
        view.setLetterSpacing(.12f);
        return view;
    }

    private TextView chip(String value, int color, int background) {
        TextView view = text(value, 9, color, true);
        view.setGravity(Gravity.CENTER);
        view.setPadding(dp(9), dp(6), dp(9), dp(6));
        view.setBackgroundColor(background);
        return view;
    }

    private int dp(int value) { return Math.round(value * getResources().getDisplayMetrics().density); }
}
