package com.example.usbcommunicator

import android.annotation.SuppressLint
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.hardware.usb.UsbManager
import android.util.Log
import com.felhr.usbserial.UsbSerialDevice
import com.felhr.usbserial.UsbSerialInterface
import java.util.Arrays

class SerialEngine(private val mContext: Context, private val mCallback: IUsbCallback) {
    private val mUsbManager: UsbManager
    private val componentName = "DeviceEngine"

    @Volatile
    var isConnected = false
    private var serialDevice: UsbSerialDevice? = null

    init {
        mUsbManager = mContext.getSystemService(Context.USB_SERVICE) as UsbManager
    }

    fun disconnect() {
        isConnected = false
        serialDevice!!.close()
    }

    fun write(data: ByteArray?) {
        serialDevice!!.write(data)
        Log.d(componentName, "Data written: " + Arrays.toString(data))
    }

    @SuppressLint("UnspecifiedRegisterReceiverFlag")
    fun maybeConnect() {
        if (isConnected) {
            Log.d(componentName, "Already connected!")
            return
        }
        Log.d(componentName, "Discovering devices...")
        val deviceList = mUsbManager.deviceList
        if (deviceList.isEmpty()) {
            Log.d(componentName, "No accessories found.")
            return
        }
        val device = deviceList.entries.iterator().next().value
        if (!mUsbManager.hasPermission(device)) {
            Log.d(componentName, "Permission missing, requesting...")
            val pi = PendingIntent.getBroadcast(
                mContext,
                0,
                Intent("com.example.usbcommunicator.USB_PERMISSION"),
                PendingIntent.FLAG_IMMUTABLE
            )
            mUsbManager.requestPermission(device, pi)
            return
        }
        Log.d(componentName, "Permission available, connecting...")
        val connection = mUsbManager.openDevice(device)
        if (connection == null) {
            Log.e(componentName, "Unable to open device!")
            return
        }
        serialDevice = UsbSerialDevice.createUsbSerialDevice(device, connection)
        serialDevice?.open()
        serialDevice?.setBaudRate(9600)
        serialDevice?.setDataBits(UsbSerialInterface.DATA_BITS_8)
        serialDevice?.setStopBits(UsbSerialInterface.STOP_BITS_1)
        serialDevice?.setParity(UsbSerialInterface.PARITY_NONE)
        serialDevice?.setFlowControl(UsbSerialInterface.FLOW_CONTROL_OFF)
        isConnected = true
        mCallback.onConnectionEstablished()
        Log.d(componentName, "Connection established.")
    }
}