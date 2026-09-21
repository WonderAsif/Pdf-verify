package com.example.pdfstamp

import com.chaquo.python.Python
import com.chaquo.python.android.AndroidPlatform
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity: FlutterActivity() {
    private val CHANNEL = "com.example.pdfstamp/python"

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        
        if (!Python.isStarted()) {
            Python.start(AndroidPlatform(this))
        }

        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, CHANNEL).setMethodCallHandler { call, result ->
            if (call.method == "stampPdf") {
                val inputBytes = call.argument<ByteArray>("pdfBytes")
                val password = call.argument<String>("password") ?: ""
                
                try {
                    val py = Python.getInstance()
                    val module = py.getModule("stamper") 
                    val resultBytes = module.callAttr("flawless_exact_tick_injection", inputBytes, password).toJava(ByteArray::class.java)
                    
                    if (resultBytes != null) {
                        result.success(resultBytes)
                    } else {
                        result.error("NO_SIGNATURE", "No signature field found.", null)
                    }
                } catch (e: Exception) {
                    result.error("PYTHON_ERROR", e.message, null)
                }
            } else {
                result.notImplemented()
            }
        }
    }
}
