package com.example.usbcommunicator

import android.annotation.SuppressLint
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.hardware.usb.UsbManager
import android.util.Log
import android.widget.Toast

class UsbEngine @SuppressLint("UnspecifiedRegisterReceiverFlag") constructor(
    private val context: Context,
    private val callback: IUsbCallback
) {
    private val componentName = "UsbEngine"
    var serialEngine: SerialEngine
    var accessoryEngine: AccessoryEngine

    init {
        serialEngine = SerialEngine(context, callback)
        accessoryEngine = AccessoryEngine(context, callback)
        val detachedFilter = IntentFilter()
        detachedFilter.addAction(UsbManager.ACTION_USB_ACCESSORY_DETACHED)
        detachedFilter.addAction(UsbManager.ACTION_USB_DEVICE_DETACHED)
        context.registerReceiver(object : BroadcastReceiver() {
            override fun onReceive(context: Context, intent: Intent) {
                if (intent.action == UsbManager.ACTION_USB_ACCESSORY_DETACHED) {
                    Log.d(componentName, "Accessory detached.")
                    accessoryEngine.disconnect()
                    callback.onDeviceDisconnected()
                } else if (intent.action == UsbManager.ACTION_USB_DEVICE_DETACHED) {
                    Log.d(componentName, "Device detached.")
                    serialEngine.disconnect()
                    callback.onDeviceDisconnected()
                }
            }
        }, detachedFilter)
        context.registerReceiver(object : BroadcastReceiver() {
            override fun onReceive(context: Context, intent: Intent) {
                if (intent.getBooleanExtra(UsbManager.EXTRA_PERMISSION_GRANTED, false)) {
                    Log.d(componentName, "USB Permission granted! Let's try to connect.")
                    serialEngine.maybeConnect()
                    accessoryEngine.maybeConnect()
                } else {
                    Log.d(componentName, "Permission denied!")
                    Toast.makeText(
                        context,
                        "Permission denied! Please give permission!",
                        Toast.LENGTH_SHORT
                    ).show()
                }
            }
        }, IntentFilter("com.example.usbcommunicator.USB_PERMISSION"))
    }

    fun onNewIntent(intent: Intent?) {
        Log.d(componentName, "Processing intent...")
        serialEngine.maybeConnect()
        accessoryEngine.maybeConnect()
    }

    val isConnected: Boolean
        get() = serialEngine.isConnected || accessoryEngine.isConnected

    fun write(data: ByteArray) {
        if (serialEngine.isConnected) {
            serialEngine.write(data)
        } else if (accessoryEngine.isConnected) {
            accessoryEngine.write(data)
        } else {
            Log.d(componentName, "Unable to write: not connected!")
            Toast.makeText(context, "Not connected!", Toast.LENGTH_SHORT).show()
        }
    }

    fun connectionStatus(): String {
        return if (serialEngine.isConnected) {
            "Connected to Serial"
        } else if (accessoryEngine.isConnected) {
            "Connected to Accessory"
        } else {
            "Disconnected"
        }
    }
}