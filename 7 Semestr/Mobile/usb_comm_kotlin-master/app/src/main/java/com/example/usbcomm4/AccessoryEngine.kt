package com.example.usbcommunicator

import android.annotation.SuppressLint
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.hardware.usb.UsbManager
import android.os.ParcelFileDescriptor
import android.util.Log
import java.io.FileInputStream
import java.io.FileOutputStream
import java.io.IOException
import java.nio.charset.StandardCharsets
import java.util.Arrays

class AccessoryEngine(private val mContext: Context, private val mCallback: IUsbCallback) {
    private val usbManager: UsbManager
    private val componentName = "AccessoryEngine"

    @Volatile
    var isConnected = false
    private var pd: ParcelFileDescriptor? = null
    private var inputStream: FileInputStream? = null
    private var outputStream: FileOutputStream? = null
    private val accessoryReader = Runnable {
        val buf = ByteArray(1024)
        while (isConnected) {
            try {
                val read = inputStream!!.read(buf)
                if (read < 0) {
                    Log.d(componentName, "End of stream reached")
                    break
                }
                if (read > 0) {
                    mCallback.onDataReceived(buf, read)
                }
            } catch (exc: Exception) {
                Log.d(componentName, "read error: " + exc.message)
                Log.d(componentName, "exiting reader thread")
                break
            }
        }
        disconnect()
    }

    init {
        usbManager = mContext.getSystemService(Context.USB_SERVICE) as UsbManager
    }

    fun disconnect() {
        isConnected = false
        if (pd != null) {
            try {
                pd!!.close()
            } catch (exc: IOException) {
                Log.d(componentName, "Disconnect: unable to close ParcelFD")
            }
        }
        if (inputStream != null) {
            try {
                inputStream!!.close()
            } catch (exc: IOException) {
                Log.d(componentName, "Disconnect: unable to close InputStream")
            }
        }
        if (outputStream != null) {
            try {
                outputStream!!.close()
            } catch (var3: IOException) {
                Log.d(componentName, "Disconnect: unable to close OutputStream")
            }
        }
    }

    fun write(data: ByteArray) {
        if (outputStream == null || !isConnected) {
            Log.d(componentName, "Cannot write: not connected!")
            return
        }
        try {
            outputStream!!.write(data)
            outputStream!!.flush()
            Log.d(componentName, "Data written: ${data.size} bytes - ${String(data, StandardCharsets.UTF_8)}")
        } catch (exc: IOException) {
            Log.d(componentName, "Could not write: " + exc.message)
        }
    }

    @SuppressLint("UnspecifiedRegisterReceiverFlag")
    fun maybeConnect() {
        if (isConnected && outputStream != null && inputStream != null) {
            Log.d(componentName, "Already connected!")
            return
        }
        Log.d(componentName, "Discovering accessories...")
        val accessoryList = usbManager.accessoryList
        if (accessoryList == null || accessoryList.size == 0) {
            Log.d(componentName, "No accessories found.")
            return
        }
        val mAccessory = accessoryList[0]
        if (!usbManager.hasPermission(mAccessory)) {
            Log.d(componentName, "Permission missing, requesting...")
            val pi = PendingIntent.getBroadcast(
                mContext,
                0,
                Intent("com.example.usbcommunicator.USB_PERMISSION"),
                0
            )
            usbManager.requestPermission(mAccessory, pi)
            return
        }
        Log.d(componentName, "Permission available, connecting...")
        pd = usbManager.openAccessory(mAccessory)
        if (pd == null) {
            Log.e(componentName, "Unable to open accessory!")
            return
        }
        val pd = pd
        val mFileDescriptor = pd!!.fileDescriptor
        inputStream = FileInputStream(mFileDescriptor)
        outputStream = FileOutputStream(mFileDescriptor)
        isConnected = true
        mCallback.onConnectionEstablished()
        val sAccessoryThread = Thread(accessoryReader, "Reader Thread")
        sAccessoryThread.start()
        Log.d(componentName, "Connection established.")
    }
}