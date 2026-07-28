package com.example.qr

import android.app.Activity
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import org.json.JSONArray
import org.json.JSONObject
import kotlin.math.abs
import kotlin.math.max
import kotlin.math.sqrt

class MainActivity : Activity() {

    private lateinit var matrixInput: EditText
    private lateinit var calculateButton: Button
    private lateinit var outputText: TextView
    private lateinit var scrollView: ScrollView

    private val EPS = 1e-9
    private val MAX_ITER_SAFETY = 1000  // Защита от бесконечного цикла

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        setContentView(R.layout.qr)

        // корректные inset'ы без enableEdgeToEdge()
        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.main)) { v, insets ->
            val bars = insets.getInsets(WindowInsetsCompat.Type.systemBars())
            v.setPadding(bars.left, bars.top, bars.right, bars.bottom)
            insets
        }

        matrixInput = findViewById(R.id.matrixInput)
        calculateButton = findViewById(R.id.calculateButton)
        outputText = findViewById(R.id.outputText)
        scrollView = findViewById(R.id.scrollView)

        matrixInput.setText("[[5, 1, 0], [1, 3, 0], [0, 0, 2]]")

        calculateButton.setOnClickListener { performQR() }
    }

    private fun performQR() {
        try {
            val json = matrixInput.text.toString().trim()
            if (json.isEmpty()) {
                showError("Пожалуйста, введите матрицу")
                return
            }

            val A = Matrix.fromJson(json)

            if (A.rows != A.cols) {
                showError("Матрица должна быть квадратной")
                return
            }
            if (!A.isSymmetric()) {
                showError("Матрица должна быть симметричной")
                return
            }

            val qr = QRDecomposition()
            val result = qr.findEigenvaluesVerbose(A, tolerance = EPS, maxIterSafety = MAX_ITER_SAFETY)

            outputText.text = buildOutput(A, result)
            
            // Прокручиваем в конец
            scrollView.post {
                scrollView.fullScroll(android.view.View.FOCUS_DOWN)
            }

            Toast.makeText(this, "Вычисления выполнены успешно!", Toast.LENGTH_SHORT).show()
        } catch (e: Exception) {
            showError("Ошибка: ${e.message}")
        }
    }

    private fun buildOutput(original: Matrix, result: QRDecomposition.EigenvalueResult): String {
        val sb = StringBuilder()

        sb.append("QR-АЛГОРИТМ ДЛЯ СИММЕТРИЧНОЙ МАТРИЦЫ (вращения Гивенса)\n")
        sb.append("Итерации до сходимости, eps=").append(EPS).append("\n")
        sb.append("------------------------------------------------------------\n")
        sb.append("Исходная матрица A0:\n")
        sb.append(original.toString(10)).append("\n")
        sb.append("\n")
        sb.append("Примечание: На каждой итерации проверяется Qk × Rk = Ak (текущая матрица),\n")
        sb.append("а не исходная A0. Финальная Ak подобна A0 и имеет те же собственные значения.\n")
        sb.append("------------------------------------------------------------\n\n")

        for ((idx, it) in result.iterations.withIndex()) {
            sb.append("Итерация ").append(it.iterationNumber).append("\n")
            sb.append("A").append(idx).append(":\n")
            sb.append(it.matrixBefore.toString(10)).append("\n\n")

            sb.append("--- QR-разложение: A").append(idx).append(" = Q").append(idx).append(" × R").append(idx).append(" ---\n\n")

            // Всегда показываем шаги вращений для каждой итерации (требование 1)
            sb.append("Шаги вращений Гивенса (каждое G и результат вращения):\n\n")
            for (step in it.qrSteps) {
                sb.append("Шаг ").append(step.stepNumber).append(": ").append(step.description).append("\n")
                if (step.rotationMatrix != null) {
                    sb.append("Матрица вращения G:\n")
                    sb.append(step.rotationMatrix.toString(10)).append("\n")
                    // Показываем результат "вращения" - умножение матрицы на матрицу вращения
                    sb.append("Результат вращения (G^T * R):\n")
                } else {
                    sb.append("Результат вращения:\n")
                }
                sb.append(step.currentMatrix.toString(10)).append("\n\n")
            }

            sb.append("Q").append(idx).append(" (ортогональная):\n")
            sb.append(it.Q.toString(10)).append("\n\n")

            sb.append("R").append(idx).append(" (верхнетреугольная):\n")
            sb.append(it.R.toString(10)).append("\n\n")

            // Проверка: Q * R должно равняться текущей матрице Ak
            val QR = it.Q.multiply(it.R)
            if (idx == 0) {
                sb.append("Проверка: Q0 × R0 = A0 (исходная матрица):\n")
            } else {
                sb.append("Проверка: Q").append(idx).append(" × R").append(idx).append(" = A").append(idx).append(" (текущая матрица на этой итерации):\n")
            }
            sb.append("Q").append(idx).append(" × R").append(idx).append(" =\n")
            sb.append(QR.toString(10)).append("\n")
            sb.append("Матрица A").append(idx).append(" (до QR-разложения):\n")
            sb.append(it.matrixBefore.toString(10)).append("\n")
            
            // Вычисляем максимальную разность для проверки точности
            var maxDiff = 0.0
            for (i in 0 until QR.rows) {
                for (j in 0 until QR.cols) {
                    val diff = abs(QR[i, j] - it.matrixBefore[i, j])
                    if (diff > maxDiff) maxDiff = diff
                }
            }
            sb.append("Максимальная разность: ").append(String.format("%.2e", maxDiff)).append("\n")
            if (maxDiff < 1e-6) {
                if (idx == 0) {
                    sb.append("✓ Проверка пройдена: Q0 × R0 = A0 (исходная матрица, с точностью до 1e-6)\n")
                } else {
                    sb.append("✓ Проверка пройдена: Q × R = A (с точностью до 1e-6)\n")
                }
            } else {
                sb.append("⚠ Внимание: различие превышает 1e-6\n")
            }
            sb.append("\n")

            sb.append("Формируем A").append(idx + 1).append(" = R").append(idx).append(" × Q").append(idx).append(":\n")
            sb.append(it.matrixAfter.toString(10)).append("\n\n")

            sb.append("||off(A").append(idx + 1).append(")||_F = ")
                .append(String.format("%.10e", it.offDiagonalNorm)).append("\n")

            if (it.offDiagonalNorm < EPS) {
                sb.append("СХОДИМОСТЬ ДОСТИГНУТА (||off|| < eps)\n")
            }

            sb.append("------------------------------------------------------------\n\n")
        }

        sb.append("ФИНАЛ:\n")
        sb.append("Финальная матрица Ak (почти диагональная):\n")
        sb.append(result.finalMatrix.toString(10)).append("\n\n")
        
        sb.append("Примечание: Финальная Ak не равна исходной A0, но подобна ей.\n")
        sb.append("Обе матрицы имеют одинаковые собственные значения.\n\n")

        sb.append("Собственные значения (диагональ Ak):\n")
        for (i in result.eigenvalues.indices) {
            sb.append("λ").append(i + 1).append(" = ")
                .append(String.format("%.10f", result.eigenvalues[i])).append("\n")
        }
        sb.append("\n")
        sb.append("Итераций выполнено: ").append(result.iterations.size).append("\n")
        sb.append("Сходимость: ").append(if (result.converged) "ДА" else "НЕТ").append("\n")

        return sb.toString()
    }

    private fun showError(message: String) {
        outputText.text = "ОШИБКА:\n$message"
        Toast.makeText(this, message, Toast.LENGTH_LONG).show()
    }

    // =====================================================================
    // =============================== Matrix ===============================
    // =====================================================================

    class Matrix(private val a: Array<DoubleArray>) {
        val rows: Int = a.size
        val cols: Int = if (a.isNotEmpty()) a[0].size else 0

        operator fun get(i: Int, j: Int): Double = a[i][j]
        operator fun set(i: Int, j: Int, v: Double) { a[i][j] = v }

        fun copy(): Matrix = Matrix(Array(rows) { i -> a[i].clone() })

        fun transpose(): Matrix {
            val t = Array(cols) { DoubleArray(rows) }
            for (i in 0 until rows) for (j in 0 until cols) t[j][i] = a[i][j]
            return Matrix(t)
        }

        fun multiply(other: Matrix): Matrix {
            require(this.cols == other.rows) { "Несовместимые размеры для умножения" }
            val r = Array(this.rows) { DoubleArray(other.cols) }
            for (i in 0 until this.rows) {
                for (j in 0 until other.cols) {
                    var s = 0.0
                    for (k in 0 until this.cols) s += this.a[i][k] * other.a[k][j]
                    r[i][j] = s
                }
            }
            return Matrix(r)
        }

        fun isSymmetric(tol: Double = 1e-9): Boolean {
            if (rows != cols) return false
            for (i in 0 until rows) {
                for (j in i + 1 until cols) {
                    if (abs(a[i][j] - a[j][i]) > tol) return false
                }
            }
            return true
        }

        fun offDiagonalNorm(): Double {
            require(rows == cols)
            var s = 0.0
            for (i in 0 until rows) for (j in 0 until cols) if (i != j) s += a[i][j] * a[i][j]
            return sqrt(s)
        }

        fun getDiagonal(): DoubleArray {
            require(rows == cols)
            return DoubleArray(rows) { i -> a[i][i] }
        }

        fun toString(decimals: Int): String {
            val fmt = "%.${decimals}f"
            val str = Array(rows) { i -> Array(cols) { j -> String.format(fmt, a[i][j]).trimEnd('0').trimEnd('.') } }
            var w = 0
            for (i in 0 until rows) for (j in 0 until cols) w = max(w, str[i][j].length)

            val sb = StringBuilder()
            for (i in 0 until rows) {
                sb.append("[ ")
                for (j in 0 until cols) {
                    sb.append(str[i][j].padStart(w, ' '))
                    if (j != cols - 1) sb.append("  ")
                }
                sb.append(" ]\n")
            }
            return sb.toString().trimEnd()
        }

        override fun toString(): String = toString(6)

        companion object {
            fun identity(n: Int): Matrix =
                Matrix(Array(n) { i -> DoubleArray(n) { j -> if (i == j) 1.0 else 0.0 } })

            fun fromJson(json: String): Matrix {
                val t = json.trim()
                val arr = if (t.startsWith("[")) JSONArray(t) else JSONObject(t).getJSONArray("data")

                require(arr.length() > 0) { "Пустая матрица" }
                val r = arr.length()
                val c = arr.getJSONArray(0).length()
                require(c > 0) { "Нулевая ширина матрицы" }

                val data = Array(r) { i ->
                    val row = arr.getJSONArray(i)
                    require(row.length() == c) { "Неровные строки: строка $i имеет длину ${row.length()}, ожидалось $c" }
                    DoubleArray(c) { j -> row.getDouble(j) }
                }
                return Matrix(data)
            }
        }
    }

    // =====================================================================
    // =========================== QRDecomposition ==========================
    // =====================================================================

    class QRDecomposition {

        data class QRStep(
            val stepNumber: Int,
            val description: String,
            val rotationMatrix: Matrix?,
            val currentMatrix: Matrix
        )

        data class QRResult(
            val Q: Matrix,
            val R: Matrix,
            val steps: List<QRStep>
        )

        fun decompose(A: Matrix): QRResult {
            require(A.rows == A.cols) { "Матрица должна быть квадратной" }
            val n = A.rows

            var R = A.copy()
            var Q = Matrix.identity(n)
            val steps = mutableListOf<QRStep>()
            var stepCount = 0

            // Стандартный метод Гивенса: обнуляем элементы слева направо, сверху вниз
            for (j in 0 until n - 1) {
                for (i in j + 1 until n) {
                    val a = R[j, j]  // диагональный элемент
                    val b = R[i, j]  // элемент под диагональю
                    
                    if (abs(b) < 1e-12) continue

                    val r = sqrt(a * a + b * b)
                    val c = a / r   // косинус
                    val s = b / r   // синус

                    // Создаем матрицу вращения Гивенса G
                    val G = Matrix.identity(n)
                    G[j, j] = c
                    G[j, i] = s
                    G[i, j] = -s
                    G[i, i] = c

                    stepCount++
                    steps.add(
                        QRStep(
                            stepNumber = stepCount,
                            description = "Вращение Гивенса для обнуления R[$i,$j]; c=%.10f, s=%.10f".format(c, s),
                            rotationMatrix = G.copy(),
                            currentMatrix = R.copy()
                        )
                    )

                    // Применяем вращение: R <- G^T * R
                    R = G.transpose().multiply(R)
                    // Обновляем Q: Q <- Q * G
                    Q = Q.multiply(G)

                    steps.add(
                        QRStep(
                            stepNumber = stepCount,
                            description = "Результат: R <- G^T * R",
                            rotationMatrix = null,
                            currentMatrix = R.copy()
                        )
                    )
                }
            }

            return QRResult(Q, R, steps)
        }

        data class EigenIteration(
            val iterationNumber: Int,
            val matrixBefore: Matrix, // Ak
            val Q: Matrix,
            val R: Matrix,
            val matrixAfter: Matrix,  // Ak+1
            val offDiagonalNorm: Double,
            val qrSteps: List<QRStep>
        )

        data class EigenvalueResult(
            val eigenvalues: DoubleArray,
            val finalMatrix: Matrix,
            val iterations: List<EigenIteration>,
            val converged: Boolean
        )

        fun findEigenvaluesVerbose(A: Matrix, tolerance: Double, maxIterSafety: Int = 1000): EigenvalueResult {
            require(A.isSymmetric()) { "Матрица должна быть симметричной" }

            var Ak = A.copy()
            val iterations = mutableListOf<EigenIteration>()

            var k = 0
            while (k < maxIterSafety) {
                val qr = decompose(Ak)
                val Q = qr.Q
                val R = qr.R

                val Ak1 = R.multiply(Q)
                val off = Ak1.offDiagonalNorm()

                iterations.add(
                    EigenIteration(
                        iterationNumber = k + 1,
                        matrixBefore = Ak.copy(),
                        Q = Q,
                        R = R,
                        matrixAfter = Ak1.copy(),
                        offDiagonalNorm = off,
                        qrSteps = qr.steps
                    )
                )

                Ak = Ak1
                k++
                
                // Останавливаемся при достижении сходимости
                if (off < tolerance) break
            }

            return EigenvalueResult(
                eigenvalues = Ak.getDiagonal(),
                finalMatrix = Ak,
                iterations = iterations,
                converged = Ak.offDiagonalNorm() < tolerance
            )
        }
    }
}
