package com.example.usbcomm4

import android.content.Intent
import android.graphics.Color
import android.os.Bundle
import android.util.Log
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import com.example.usbcommunicator.IUsbCallback
import com.example.usbcommunicator.UsbEngine
import java.nio.charset.StandardCharsets

class MainActivity : AppCompatActivity() {
    private val mCallback: IUsbCallback = object : IUsbCallback {
        override fun onConnectionEstablished() {
            val tv = findViewById<TextView>(R.id.textView)
            tv.text = usbEngine!!.connectionStatus()
            tv.setTextColor(Color.GREEN)
        }

        override fun onDeviceDisconnected() {
            val tv = findViewById<TextView>(R.id.textView)
            tv.text = usbEngine!!.connectionStatus()
            tv.setTextColor(Color.RED)
        }

        override fun onDataReceived(data: ByteArray?, num: Int) {
            val tv = findViewById<TextView>(R.id.textView2)
            if (data == null || num <= 0) {
                Log.d("App", "Received empty data!")
                return
            }
            val text = String(data, 0, num, StandardCharsets.UTF_8)
            Log.d("App", "Received: $text (${num} bytes)")
            runOnUiThread {
                tv.text = text
            }
        }
    }
    private var usbEngine: UsbEngine? = null
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        usbEngine = UsbEngine(applicationContext, mCallback)
        onNewIntent(this.intent)
        
        val editTextMessage = findViewById<EditText>(R.id.editTextMessage)
        val buttonSend = findViewById<Button>(R.id.buttonSend)
        
        buttonSend.setOnClickListener {
            val message = editTextMessage.text.toString()
            if (message.isNotEmpty()) {
                usbEngine?.write(message.toByteArray(StandardCharsets.UTF_8))
                editTextMessage.text.clear()
            }
        }

        editTextMessage.setOnEditorActionListener { _, _, _ ->
            buttonSend.performClick()
            true
        }
    }

    override fun onNewIntent(intent: Intent?) {
        super.onNewIntent(intent)
        usbEngine!!.onNewIntent(intent)
    }

    override fun onResume() {
        super.onResume()
        val intent = this.intent
        onNewIntent(intent)
    }
}