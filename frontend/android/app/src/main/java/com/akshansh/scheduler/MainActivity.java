package com.akshansh.scheduler;

import android.os.Bundle;
import android.util.Log;
import android.webkit.WebSettings;
import android.webkit.WebView;
import com.chaquo.python.PyObject;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;
import com.getcapacitor.BridgeActivity;
import java.io.File;

public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        initPython();
    }

    private void initPython() {
        if (!Python.isStarted()) {
            Python.start(new AndroidPlatform(this));
        }
        
        // Run FastAPI in a background thread to prevent blocking the UI
        new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    Python py = Python.getInstance();
                    
                    // Set environment variables for database path
                    File filesDir = getFilesDir();
                    PyObject os = py.getModule("os");
                    os.get("environ").put("PYTHON_DATA_DIR", filesDir.getAbsolutePath());
                    
                    Log.d("PythonServer", "Starting Python server from start_server.py");
                    PyObject serverModule = py.getModule("start_server");
                    serverModule.callAttr("start_fastapi");
                } catch (Exception e) {
                    Log.e("PythonServer", "Error starting server", e);
                }
            }
        }).start();

        // Wait for server to be healthy before loading the app
        new Thread(new Runnable() {
            @Override
            public void run() {
                boolean healthy = false;
                int attempts = 0;
                while (!healthy && attempts < 30) {
                    try {
                        java.net.URL url = new java.net.URL("http://127.0.0.1:8000/health");
                        java.net.HttpURLConnection conn = (java.net.HttpURLConnection) url.openConnection();
                        conn.setConnectTimeout(1000);
                        if (conn.getResponseCode() == 200) {
                            healthy = true;
                            Log.d("PythonServer", "Server is healthy!");
                        }
                    } catch (Exception e) {
                        Log.d("PythonServer", "Waiting for server...");
                    }
                    if (!healthy) {
                        try { Thread.sleep(1000); } catch (InterruptedException e) {}
                        attempts++;
                    }
                }
                
                if (healthy) {
                    runOnUiThread(new Runnable() {
                        @Override
                        public void run() {
                            loadWebView();
                        }
                    });
                }
            }
        }).start();
    }

    private void loadWebView() {
        // BridgeActivity's bridge is initialized in onCreate, 
        // but we might need to trigger the initial load if we deferred it.
        // Since we can't easily defer the Capacitor bridge initialization without 
        // deeper changes, we just ensure it's ready.
        Log.d("PythonServer", "Reloading WebView now that backend is ready");
        getBridge().getWebView().reload();
    }

    @Override
    public void onStart() {
        super.onStart();
        WebView webView = getBridge().getWebView();
        if (webView != null) {
            WebSettings settings = webView.getSettings();
            settings.setJavaScriptEnabled(true);
            settings.setDomStorageEnabled(true);
            settings.setCacheMode(WebSettings.LOAD_DEFAULT);
            settings.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);
            
            // Hardware acceleration is usually on by default in Android 4.0+
            // but we ensure the layer type is set correctly.
            webView.setLayerType(WebView.LAYER_TYPE_HARDWARE, null);
        }
    }
}
