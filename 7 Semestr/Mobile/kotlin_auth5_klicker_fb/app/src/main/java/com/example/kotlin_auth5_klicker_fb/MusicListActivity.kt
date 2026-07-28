package com.example.kotlin_auth5_klicker_fb

import android.os.Build
import android.os.Bundle
import android.os.StrictMode
import android.os.StrictMode.ThreadPolicy
import android.widget.ListView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import org.json.JSONArray
import java.net.HttpURLConnection
import java.net.URL

class MusicListActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_music_list)

        // Разрешить внешние соединения
        if (Build.VERSION.SDK_INT > 9) {
            val policy = ThreadPolicy.Builder().permitAll().build()
            StrictMode.setThreadPolicy(policy)
        }

        val url = "https://mysafeinfo.com/api/data?list=musicstyles&format=json"
        val connection = URL(url).openConnection() as HttpURLConnection
        val responseCode = connection.responseCode

        try {
            val data = connection.inputStream.bufferedReader().use { it.readText() }
            handleJson(data)
        } catch (e: Exception) {
            Toast.makeText(applicationContext, "Error loading data: ${e.message}", Toast.LENGTH_LONG).show()
        } finally {
            connection.disconnect()
        }
    }

    private fun handleJson(jsonString: String?) {
        try {
            val jsonArray = JSONArray(jsonString)
            val list = ArrayList<MusicStyle>()
            var x = 0
            
            while (x < jsonArray.length()) {
                val jsonObject = jsonArray.getJSONObject(x)
                
                list.add(
                    MusicStyle(
                        jsonObject.getInt("ID"),
                        jsonObject.getString("MusicType"),
                        jsonObject.getString("Genre"),
                        jsonObject.getString("Url")
                    )
                )
                x++
            }

            val adapter = MusicListAdapter(this, list)
            val listView: ListView = findViewById(R.id.music_list)
            listView.adapter = adapter

            Toast.makeText(applicationContext, "Loaded ${x} music styles", Toast.LENGTH_SHORT).show()
        } catch (e: Exception) {
            Toast.makeText(applicationContext, "Error parsing JSON: ${e.message}", Toast.LENGTH_LONG).show()
        }
    }
}


