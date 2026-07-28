package com.example.calculator


//import kotlinx.android.synthetic.main.activity_main.*
import android.os.Bundle
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import net.objecthunter.exp4j.ExpressionBuilder
import net.objecthunter.exp4j.function.Function

class MainActivity : AppCompatActivity()
{
    /**
     * Нормализует унарные операторы + и - в выражении
     * Поддерживает: +2, -2, -(-2), +(-2), и т.д.
     */
    private fun normalizeUnaryOperators(expression: String): String {
        if (expression.isEmpty()) return expression
        
        var result = StringBuilder(expression)
        var i = 0
        
        // Обработка унарного плюса в начале выражения: +2 -> 2
        if (result.isNotEmpty() && result[0] == '+') {
            result.deleteCharAt(0)
        }
        
        // Обработка унарных операторов в других позициях
        while (i < result.length) {
            val isOperator = i > 0 && (result[i - 1] == '+' || result[i - 1] == '-' || 
                                      result[i - 1] == '*' || result[i - 1] == '/' || 
                                      result[i - 1] == '(')
            
            when {
                // Унарный плюс после оператора или скобки: (+2) -> (2), 2+(+3) -> 2+(3)
                isOperator && i < result.length && result[i] == '+' -> {
                    result.deleteCharAt(i)
                    continue // не увеличиваем i, так как удалили символ
                }
                // Нормализация двойных операторов
                i + 1 < result.length && result[i] == '+' && result[i + 1] == '+' -> {
                    result.deleteCharAt(i + 1)
                    continue
                }
                i + 1 < result.length && result[i] == '+' && result[i + 1] == '-' -> {
                    result[i] = '-'
                    result.deleteCharAt(i + 1)
                    continue
                }
                i + 1 < result.length && result[i] == '-' && result[i + 1] == '+' -> {
                    result.deleteCharAt(i + 1)
                    continue
                }
            }
            i++
        }
        
        return result.toString()
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)


        /*Number Buttons*/
        val tvExpression: TextView = findViewById(R.id.tvExpression)

        val tvOne: TextView = findViewById(R.id.tvOne)
        tvOne.setOnClickListener {
            tvExpression.text = tvExpression.text.toString() + "1"
        }

        val tvTwo: TextView = findViewById(R.id.tvTwo)
        tvTwo.setOnClickListener {
            tvExpression.text = tvExpression.text.toString() + "2"
        }

        val tvThree: TextView = findViewById(R.id.tvThree)
        tvThree.setOnClickListener {
            tvExpression.text = tvExpression.text.toString() + "3"
        }

        val tvFour: TextView = findViewById(R.id.tvFour)
        tvFour.setOnClickListener {
            tvExpression.text = tvExpression.text.toString() + "4"
        }

        val tvFive: TextView = findViewById(R.id.tvFive)
        tvFive.setOnClickListener {
            tvExpression.text = tvExpression.text.toString() + "5"
        }

        val tvSix: TextView = findViewById(R.id.tvSix)
        tvSix.setOnClickListener {
            tvExpression.text = tvExpression.text.toString() + "6"
        }

        val tvSeven: TextView = findViewById(R.id.tvSeven)
        tvSeven.setOnClickListener {
            tvExpression.text = tvExpression.text.toString() + "7"
        }

        val tvEight: TextView = findViewById(R.id.tvEight)
        tvEight.setOnClickListener {
            tvExpression.text = tvExpression.text.toString() + "8"
        }

        val tvNine: TextView = findViewById(R.id.tvNine)
        tvNine.setOnClickListener {
            tvExpression.text = tvExpression.text.toString() + "9"
        }

        val tvZero: TextView = findViewById(R.id.tvZero)
        tvZero.setOnClickListener {
            tvExpression.text = tvExpression.text.toString() + "0"
        }

        /*Operators*/

        val tvPlus: TextView = findViewById(R.id.tvPlus)
        tvPlus.setOnClickListener {
            tvExpression.text = tvExpression.text.toString() + "+"
        }

        val tvMinus: TextView = findViewById(R.id.tvMinus)
        tvMinus.setOnClickListener {
            tvExpression.text = tvExpression.text.toString() + "-"
        }

        val tvMul: TextView = findViewById(R.id.tvMul)
        tvMul.setOnClickListener {
            tvExpression.text = tvExpression.text.toString() + "*"
        }

        val tvDivide: TextView = findViewById(R.id.tvDivide)
        tvDivide.setOnClickListener {
            tvExpression.text = tvExpression.text.toString() + "/"
        }

        val tvDot: TextView = findViewById(R.id.tvDot)
        tvDot.setOnClickListener {
            tvExpression.text = tvExpression.text.toString() + "."
        }

        val tvClear: TextView = findViewById(R.id.tvClear)

        val tvResult: TextView = findViewById(R.id.tvResult)
        tvClear.setOnClickListener {
            tvExpression.text = ""
            tvResult.text = ""
        }

        val tvEquals: TextView = findViewById(R.id.tvEquals)
        tvEquals.setOnClickListener {
            try {
                var text = tvExpression.text.toString().trim()
                
                // Функция для нормализации унарных операторов
                text = normalizeUnaryOperators(text)
                
                // Создаем функции sinh и signum
                val sinhFunction = object : Function("sinh", 1) {
                    override fun apply(vararg args: Double): Double {
                        return kotlin.math.sinh(args[0])
                    }
                }
                
                val signumFunction = object : Function("signum", 1) {
                    override fun apply(vararg args: Double): Double {
                        return when {
                            args[0] > 0 -> 1.0
                            args[0] < 0 -> -1.0
                            else -> 0.0
                        }
                    }
                }
                
                val expression = ExpressionBuilder(text)
                    .function(sinhFunction)
                    .function(signumFunction)
                    .build()

                val result = expression.evaluate()
                val longResult = result.toLong()
                if (result == longResult.toDouble()) {
                    tvResult.text = longResult.toString()
                } else {
                    tvResult.text = result.toString()
                }
            } catch (e: Exception) {
                tvResult.text = "Error"
            }
        }
        val tvBack: TextView = findViewById(R.id.tvBack)
        tvBack.setOnClickListener {
            val text = tvExpression.text.toString()
            if(text.isNotEmpty()) {
                tvExpression.text = text.drop(1)
            }

            tvResult.text = ""
        }

        // Новые кнопки для функций
        val tvSinh: TextView = findViewById(R.id.tvSinh)
        tvSinh.setOnClickListener {
            tvExpression.text = tvExpression.text.toString() + "sinh("
        }

        val tvSignum: TextView = findViewById(R.id.tvSignum)
        tvSignum.setOnClickListener {
            tvExpression.text = tvExpression.text.toString() + "signum("
        }

        val tvOpenBracket: TextView = findViewById(R.id.tvOpenBracket)
        tvOpenBracket.setOnClickListener {
            tvExpression.text = tvExpression.text.toString() + "("
        }

        val tvCloseBracket: TextView = findViewById(R.id.tvCloseBracket)
        tvCloseBracket.setOnClickListener {
            tvExpression.text = tvExpression.text.toString() + ")"
        }
    }







}