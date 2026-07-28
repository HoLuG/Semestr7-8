package com.example.kotlin_auth5_klicker_fb

import android.content.Intent
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.database.FirebaseDatabase

class MainActivity : AppCompatActivity() {
    
    private var counter = 0
    private lateinit var fbAuth: FirebaseAuth

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        
        // Инициализация Firebase Auth
        fbAuth = FirebaseAuth.getInstance()
        
        val et_user_name = findViewById<EditText>(R.id.et_user_name)
        val et_password = findViewById<EditText>(R.id.et_password)
        val btn_reset = findViewById<Button>(R.id.btn_reset)
        val btn_submit = findViewById<Button>(R.id.btn_submit)
        val tvCounter = findViewById<TextView>(R.id.tvCounter)
        
        // Обновление счетчика при загрузке
        updateCounter(tvCounter)
        
        btn_reset.setOnClickListener {
            et_user_name.setText("")
            et_password.setText("")
        }
        
        btn_submit.setOnClickListener {
            val user_name = et_user_name.text.toString().trim()
            val password = et_password.text.toString().trim()
            
            // Проверка на пустые поля
            if (user_name.isEmpty() || password.isEmpty()) {
                Toast.makeText(this@MainActivity, "Please fill in all fields", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }
            
            Toast.makeText(this@MainActivity, user_name, Toast.LENGTH_LONG).show()
            
            // Попытка авторизации через Firebase
            fbAuth.signInWithEmailAndPassword(user_name, password)
                .addOnCompleteListener(this) { task ->
                    if (task.isSuccessful) {
                        counter++
                        updateCounter(tvCounter)

                        val myRef = FirebaseDatabase.getInstance("https://mobilki2025-default-rtdb.asia-southeast1.firebasedatabase.app/").reference
                        myRef.child("counter").setValue(counter)
                            .addOnCompleteListener { dbTask ->
                                if (dbTask.isSuccessful) {
                                    Toast.makeText(this, "Authorization successful! Counter updated: $counter", Toast.LENGTH_SHORT).show()

                                    val intent = Intent(this, MusicListActivity::class.java)
                                    startActivity(intent)
                                } else {
                                    Toast.makeText(this, "Error saving counter", Toast.LENGTH_SHORT).show()
                                }
                            }
                    } else {
                        val errorMessage = task.exception?.message ?: "Authorization failed"
                        Toast.makeText(this, "Authorization failed: $errorMessage", Toast.LENGTH_LONG).show()
                    }
                }
        }
    }
    
    private fun updateCounter(tvCounter: TextView) {
        tvCounter.text = "Counter: $counter"
    }
}