package com.example.lab6

import android.app.Application
import com.yandex.mapkit.MapKitFactory

class MainApplication : Application() {
    override fun onCreate() {
        super.onCreate()
        MapKitFactory.setApiKey("70bb15d4-296c-4eba-a75c-07aaf86d013a")
    }
}
