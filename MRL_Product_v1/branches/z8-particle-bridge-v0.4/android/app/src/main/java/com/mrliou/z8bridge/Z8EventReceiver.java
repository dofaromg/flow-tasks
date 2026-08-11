package com.mrliou.z8bridge;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.util.Log;

import org.json.JSONObject;

import java.util.UUID;

public final class Z8EventReceiver extends BroadcastReceiver {
    public static final String ACTION_EVENT = "com.mrliou.z8bridge.EVENT";
    private static final String TAG = "MRL-Z8-Bridge";

    @Override
    public void onReceive(Context context, Intent intent) {
        if (!ACTION_EVENT.equals(intent.getAction())) return;
        PendingResult pending = goAsync();
        try {
            String source = value(intent, "source");
            String kind = value(intent, "kind");
            JSONObject event = new JSONObject();
            event.put("event_id", optional(intent, "event_id", source + "-" + UUID.randomUUID()));
            event.put("source", source);
            event.put("kind", kind);
            event.put("device_id", optional(intent, "device_id", "owned-z8"));
            event.put("occurred_at", new java.text.SimpleDateFormat(
                    "yyyy-MM-dd'T'HH:mm:ss.SSSXXX", java.util.Locale.US).format(new java.util.Date()));

            String target = intent.getStringExtra("target_id");
            if (target != null && !target.trim().isEmpty()) {
                event.put("target", new JSONObject().put("type", "user").put("id", target.trim()));
            }
            if ("weiliao".equals(source) && "text".equals(kind)) {
                event.put("text", value(intent, "text"));
            } else if ("xiaozhi".equals(source) && "voice".equals(kind)) {
                JSONObject audio = new JSONObject();
                audio.put("ref", value(intent, "audio_ref"));
                audio.put("codec", optional(intent, "codec", "unknown"));
                audio.put("mime_type", optional(intent, "mime_type", "application/octet-stream"));
                audio.put("duration_ms", intent.getLongExtra("duration_ms", 0));
                event.put("audio", audio);
            } else {
                throw new IllegalArgumentException("Unsupported source/kind: " + source + "/" + kind);
            }

            BridgeClient.send(context, event, new BridgeClient.Callback() {
                @Override public void onSuccess(int status, String response) {
                    Log.i(TAG, "Event accepted by DL580: HTTP " + status);
                    pending.finish();
                }

                @Override public void onFailure(Exception error) {
                    Log.e(TAG, "Event delivery failed", error);
                    pending.finish();
                }
            });
        } catch (Exception error) {
            Log.e(TAG, "Invalid bridge event", error);
            pending.finish();
        }
    }

    private static String value(Intent intent, String name) {
        String value = intent.getStringExtra(name);
        if (value == null || value.trim().isEmpty()) {
            throw new IllegalArgumentException(name + " is required");
        }
        return value.trim();
    }

    private static String optional(Intent intent, String name, String fallback) {
        String value = intent.getStringExtra(name);
        return value == null || value.trim().isEmpty() ? fallback : value.trim();
    }
}
