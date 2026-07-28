package com.example.usb

import android.hardware.usb.UsbAccessory
import android.hardware.usb.UsbManager
import android.os.Bundle
import android.os.ParcelFileDescriptor
import android.util.Log
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel
import java.io.FileInputStream
import java.io.FileOutputStream
import java.io.IOException
import java.io.InputStream
import java.io.OutputStream

class MainActivity : FlutterActivity() {

    private val CHANNEL = "aoap_channel"

    private lateinit var usbManager: UsbManager
    private var accessory: UsbAccessory? = null
    private var fileDescriptor: ParcelFileDescriptor? = null
    private var inputStream: InputStream? = null
    private var outputStream: OutputStream? = null

    private var methodChannel: MethodChannel? = null

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)

        usbManager = getSystemService(USB_SERVICE) as UsbManager

        methodChannel = MethodChannel(
            flutterEngine.dartExecutor.binaryMessenger,
            CHANNEL
        )

        methodChannel?.setMethodCallHandler { call, result ->
            when (call.method) {
                "connect" -> {
                    connectAccessory()
                    result.success(null)
                }

                "send" -> {
                    val text = (call.argument<String>("text") ?: "") + "\n"
                    sendToHost(text)
                    result.success(null)
                }

                else -> result.notImplemented()
            }
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        handleIntent(intent)
    }

    override fun onNewIntent(intent: android.content.Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        handleIntent(intent)
    }

    private fun handleIntent(intent: android.content.Intent) {
        if (UsbManager.ACTION_USB_ACCESSORY_ATTACHED == intent.action) {
            val acc = intent.getParcelableExtra<UsbAccessory>(UsbManager.EXTRA_ACCESSORY)
            if (acc != null) {
                logStatus("Accessory attached via intent")
                openAccessory(acc)
            }
        }
    }

    private fun connectAccessory() {
        val accessories = usbManager.accessoryList
        if (accessories != null && accessories.isNotEmpty()) {
            logStatus("Accessory found from list")
            openAccessory(accessories[0])
        } else {
            logStatus("No accessory found (run Python host)")
        }
    }

    private fun openAccessory(acc: UsbAccessory) {
        try {
            val fd = usbManager.openAccessory(acc)
            if (fd == null) {
                logStatus("openAccessory returned null")
                return
            }

            accessory = acc
            fileDescriptor = fd
            inputStream = FileInputStream(fd.fileDescriptor)
            outputStream = FileOutputStream(fd.fileDescriptor)

            logStatus("Accessory opened")

            startReadThread()
        } catch (e: Exception) {
            Log.e("AOAP", "Error openAccessory", e)
            logStatus("Error openAccessory: ${e.message}")
        }
    }

    private fun startReadThread() {
        Thread {
            val buffer = ByteArray(1024)
            try {
                while (true) {
                    val ins = inputStream ?: break
                    val len = ins.read(buffer)
                    if (len <= 0) {
                        // 0 или -1 – конец потока
                        break
                    }
                    val text = String(buffer, 0, len, Charsets.UTF_8)
                    Log.d("AOAP", "Received from host: [$text]")

                    // ВСЕ вызовы MethodChannel – только с UI-потока
                    runOnUiThread {
                        methodChannel?.invokeMethod("onMessage", text)
                    }
                }
            } catch (e: IOException) {
                Log.e("AOAP", "Read thread IO error", e)
                runOnUiThread {
                    logStatus("Read error: ${e.message}")
                }
            } catch (e: Exception) {
                Log.e("AOAP", "Read thread fatal error", e)
                runOnUiThread {
                    logStatus("Fatal read error: ${e.message}")
                }
            }
        }.start()
    }

    private fun sendToHost(text: String) {
        try {
            val outs = outputStream
            if (outs == null) {
                logStatus("Not connected (no outputStream)")
                return
            }
            outs.write(text.toByteArray(Charsets.UTF_8))
            outs.flush()
        } catch (e: IOException) {
            Log.e("AOAP", "Send error", e)
            logStatus("Send error: ${e.message}")
        } catch (e: Exception) {
            Log.e("AOAP", "Send fatal error", e)
            logStatus("Fatal send error: ${e.message}")
        }
    }

    private fun logStatus(msg: String) {
        Log.d("AOAP", msg)
        // тоже с UI-потока
        runOnUiThread {
            methodChannel?.invokeMethod("onStatus", msg)
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        try {
            inputStream?.close()
            outputStream?.close()
            fileDescriptor?.close()
        } catch (_: IOException) {
        }
    }
}
