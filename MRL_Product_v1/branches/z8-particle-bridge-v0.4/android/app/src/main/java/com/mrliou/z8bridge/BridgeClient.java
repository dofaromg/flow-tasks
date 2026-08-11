package com.mrliou.z8bridge;

import android.content.Context;
import android.content.SharedPreferences;
import android.os.Handler;
import android.os.Looper;
import android.util.Base64;

import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;

public final class BridgeClient {
    public static final String PREFS = "mrl_z8_bridge";
    public static final String KEY_ENDPOINT = "endpoint";
    public static final String KEY_SECRET = "device_shared_secret";
    public static final String KEY_TARGET = "line_target";

    private static final ExecutorService EXECUTOR = Executors.newSingleThreadExecutor();
    private static final Handler MAIN = new Handler(Looper.getMainLooper());

    private BridgeClient() {}

    public interface Callback {
        void onSuccess(int status, String response);
        void onFailure(Exception error);
    }

    public static void send(Context context, JSONObject event, Callback callback) {
        Context appContext = context.getApplicationContext();
        EXECUTOR.execute(() -> {
            HttpURLConnection connection = null;
            try {
                SharedPreferences prefs = appContext.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
                String endpoint = prefs.getString(KEY_ENDPOINT, "").trim();
                String secret = prefs.getString(KEY_SECRET, "");
                if (endpoint.isEmpty()) throw new IllegalStateException("DL580 endpoint is not configured");
                if (secret.isEmpty()) throw new IllegalStateException("Device HMAC secret is not configured");

                byte[] body = event.toString().getBytes(StandardCharsets.UTF_8);
                URL url = new URL(endpoint.replaceAll("/+$", "") + "/v1/z8/events");
                connection = (HttpURLConnection) url.openConnection();
                connection.setRequestMethod("POST");
                connection.setConnectTimeout(10000);
                connection.setReadTimeout(30000);
                connection.setDoOutput(true);
                connection.setRequestProperty("Content-Type", "application/json; charset=utf-8");
                connection.setRequestProperty("X-MRL-Signature", sign(body, secret));
                connection.getOutputStream().write(body);

                int status = connection.getResponseCode();
                InputStream stream = status >= 200 && status < 400
                        ? connection.getInputStream()
                        : connection.getErrorStream();
                String response = readAll(stream);
                if (status < 200 || status >= 300) {
                    throw new IllegalStateException("DL580 returned HTTP " + status + ": " + response);
                }
                int finalStatus = status;
                MAIN.post(() -> callback.onSuccess(finalStatus, response));
            } catch (Exception error) {
                MAIN.post(() -> callback.onFailure(error));
            } finally {
                if (connection != null) connection.disconnect();
            }
        });
    }

    private static String sign(byte[] body, String secret) throws Exception {
        Mac mac = Mac.getInstance("HmacSHA256");
        mac.init(new SecretKeySpec(secret.getBytes(StandardCharsets.UTF_8), "HmacSHA256"));
        return Base64.encodeToString(mac.doFinal(body), Base64.NO_WRAP);
    }

    private static String readAll(InputStream stream) throws Exception {
        if (stream == null) return "";
        BufferedReader reader = new BufferedReader(new InputStreamReader(stream, StandardCharsets.UTF_8));
        StringBuilder result = new StringBuilder();
        String line;
        while ((line = reader.readLine()) != null) result.append(line);
        reader.close();
        return result.toString();
    }
}
