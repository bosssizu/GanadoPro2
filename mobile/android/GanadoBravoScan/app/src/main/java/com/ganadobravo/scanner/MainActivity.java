package com.ganadobravo.scanner;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.widget.TextView;

public class MainActivity extends Activity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        TextView tv = new TextView(this);
        tv.setText("GanadoBravo Scan (demo)\nRecibiendo deep links…");
        setContentView(tv);

        Intent intent = getIntent();
        Uri data = intent.getData();
        if (data != null) {
            // Handle ganadobravo://scan?category=...&return=...
            tv.setText("Deep link recibido: " + data.toString());
        }
    }
}
