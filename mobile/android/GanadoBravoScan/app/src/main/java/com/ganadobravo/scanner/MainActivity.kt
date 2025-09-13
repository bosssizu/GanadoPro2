package com.ganadobravo.scanner

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import android.widget.Button
import android.widget.TextView
import androidx.activity.ComponentActivity
import androidx.activity.result.contract.ActivityResultContracts
import androidx.core.app.ActivityCompat
import com.google.ar.core.ArCoreApk
import com.google.ar.core.Config
import com.google.ar.core.Session

class MainActivity : ComponentActivity() {

    private val backendUrl = "https://YOUR-DEPLOY-URL/api/evaluate" // TODO: set
    private var arSupported = false
    private var depthSupported = false

    private val perms = registerForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        if (!granted) finish()
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(layout())

        if (ActivityCompat.checkSelfPermission(this, Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED) {
            perms.launch(Manifest.permission.CAMERA)
        }

        val availability = ArCoreApk.getInstance().checkAvailability(this)
        arSupported = availability.isSupported
        depthSupported = try {
            val session = Session(this)
            val ok = session.isDepthModeSupported(Config.DepthMode.AUTOMATIC)
            session.close(); ok
        } catch (e: Exception) { false }

        val tv = findViewById<TextView>(1002)
        val btn = findViewById<Button>(1001)
        if (!arSupported || !depthSupported) {
            tv.text = "Escaneo 3D no soportado en este dispositivo. Usa análisis 2D o fotogrametría externa."
            btn.isEnabled = false
        } else {
            tv.text = "Listo para escanear 6–20 s, 120–270°"
            btn.isEnabled = true
            btn.setOnClickListener {
                // TODO: implementar captura Depth + PLY + upload (idéntico a iOS)
                tv.text = "Demo: captura Depth pendiente en este starter."
            }
        }
    }

    private fun layout(): android.widget.LinearLayout {
        val root = android.widget.LinearLayout(this).apply {
            orientation = android.widget.LinearLayout.VERTICAL
            setPadding(32,48,32,32)
        }
        val tv = TextView(this).apply { id = 1002; textSize = 16f; text = "Comprobando soporte ARCore/Depth…" }
        val btn = Button(this).apply { id = 1001; text = "Escanear"; isAllCaps = false; isEnabled = false }
        root.addView(tv, android.widget.LinearLayout.LayoutParams.MATCH_PARENT, android.widget.LinearLayout.LayoutParams.WRAP_CONTENT)
        root.addView(btn, android.widget.LinearLayout.LayoutParams.MATCH_PARENT, android.widget.LinearLayout.LayoutParams.WRAP_CONTENT)
        return root
    }
}
