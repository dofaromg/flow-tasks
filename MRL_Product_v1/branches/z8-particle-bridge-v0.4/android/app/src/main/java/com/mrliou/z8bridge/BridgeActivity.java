package com.mrliou.z8bridge;

import android.app.Activity;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.text.InputType;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import org.json.JSONObject;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;
import java.util.UUID;

public final class BridgeActivity extends Activity {
    private EditText endpoint;
    private EditText secret;
    private EditText target;
    private EditText message;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        SharedPreferences prefs = getSharedPreferences(BridgeClient.PREFS, MODE_PRIVATE);

        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        int pad = Math.round(16 * getResources().getDisplayMetrics().density);
        panel.setPadding(pad, pad, pad, pad);

        TextView title = new TextView(this);
        title.setText("MRL Z8 ParticleBridge v0.4 — independent dry-run adapter");
        title.setTextSize(18);
        panel.addView(title);

        endpoint = field(panel, "DL580 endpoint", prefs.getString(BridgeClient.KEY_ENDPOINT, "http://192.168.1.2:8788"));
        secret = field(panel, "Device HMAC secret", prefs.getString(BridgeClient.KEY_SECRET, ""));
        secret.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD);
        target = field(panel, "LINE test target", prefs.getString(BridgeClient.KEY_TARGET, ""));
        message = field(panel, "微聊 dry-run text", "Z8 dry-run test");

        Button save = button(panel, "Save local settings");
        save.setOnClickListener(view -> {
            saveSettings();
            toast("Saved only inside the independent bridge app");
        });

        Button sendText = button(panel, "Send 微聊 mapping test");
        sendText.setOnClickListener(view -> {
            saveSettings();
            try {
                JSONObject event = baseEvent("weiliao", "text");
                event.put("text", message.getText().toString());
                addTarget(event);
                send(event);
            } catch (Exception error) {
                toast(error.getMessage());
            }
        });

        Button sendVoice = button(panel, "Send 小智 metadata test");
        sendVoice.setOnClickListener(view -> {
            saveSettings();
            try {
                JSONObject event = baseEvent("xiaozhi", "voice");
                JSONObject audio = new JSONObject();
                audio.put("ref", "local://owned-z8/evidence-required.amr");
                audio.put("codec", "unknown");
                audio.put("mime_type", "application/octet-stream");
                audio.put("duration_ms", 0);
                event.put("audio", audio);
                addTarget(event);
                send(event);
            } catch (Exception error) {
                toast(error.getMessage());
            }
        });

        TextView boundary = new TextView(this);
        boundary.setText("Automatic 小智/微聊 observation is intentionally not guessed. Run Collect-Z8Evidence.ps1, then bind the observed package/activity/intent/codec in this branch.");
        boundary.setPadding(0, pad, 0, 0);
        panel.addView(boundary);

        ScrollView scroll = new ScrollView(this);
        scroll.addView(panel);
        setContentView(scroll);
    }

    private EditText field(LinearLayout panel, String hint, String value) {
        EditText field = new EditText(this);
        field.setHint(hint);
        field.setText(value);
        panel.addView(field, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        return field;
    }

    private Button button(LinearLayout panel, String text) {
        Button button = new Button(this);
        button.setText(text);
        panel.addView(button, new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));
        return button;
    }

    private void saveSettings() {
        getSharedPreferences(BridgeClient.PREFS, MODE_PRIVATE).edit()
                .putString(BridgeClient.KEY_ENDPOINT, endpoint.getText().toString().trim())
                .putString(BridgeClient.KEY_SECRET, secret.getText().toString())
                .putString(BridgeClient.KEY_TARGET, target.getText().toString().trim())
                .apply();
    }

    private JSONObject baseEvent(String source, String kind) throws Exception {
        JSONObject event = new JSONObject();
        event.put("event_id", source + "-" + UUID.randomUUID().toString().replace("-", ""));
        event.put("source", source);
        event.put("kind", kind);
        event.put("device_id", "owned-z8");
        event.put("occurred_at", new SimpleDateFormat(
                "yyyy-MM-dd'T'HH:mm:ss.SSSXXX", Locale.US).format(new Date()));
        return event;
    }

    private void addTarget(JSONObject event) throws Exception {
        String id = target.getText().toString().trim();
        if (!id.isEmpty()) event.put("target", new JSONObject().put("type", "user").put("id", id));
    }

    private void send(JSONObject event) {
        BridgeClient.send(this, event, new BridgeClient.Callback() {
            @Override public void onSuccess(int status, String response) {
                toast("DL580 accepted: HTTP " + status);
            }

            @Override public void onFailure(Exception error) {
                toast(error.getMessage());
            }
        });
    }

    private void toast(String text) {
        Toast.makeText(this, text == null ? "Unknown error" : text, Toast.LENGTH_LONG).show();
    }
}
