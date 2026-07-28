package com.example.usbcommunicator

interface IUsbCallback {
    fun onConnectionEstablished()
    fun onDeviceDisconnected()
    fun onDataReceived(data: ByteArray?, num: Int)
}