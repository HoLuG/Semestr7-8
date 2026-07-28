package com.example.svd

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.unit.dp
import com.example.svd.ui.theme.SvdTheme
import kotlin.math.abs
import kotlin.math.max
import kotlin.math.sqrt
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.ejml.simple.SimpleMatrix
import org.json.JSONArray
import org.json.JSONObject

// ==================== Класс Matrix ====================
class Matrix(val data: Array<DoubleArray>) {
    val rows: Int = data.size
    val cols: Int = if (data.isNotEmpty()) data[0].size else 0

    companion object {
        fun fromJson(json: String): Matrix {
            val trimmed = json.trim()
            val arr = if (trimmed.startsWith("[")) {
                JSONArray(trimmed)
            } else {
                JSONObject(trimmed).getJSONArray("data")
            }

            require(arr.length() > 0) { "Пустая матрица" }

            val rows = arr.length()
            val cols = arr.getJSONArray(0).length()
            require(cols > 0) { "Нулевая ширина матрицы" }

            val data = Array(rows) { i ->
                val row = arr.getJSONArray(i)
                require(row.length() == cols) {
                    "Неровные строки: строка $i имеет длину ${row.length()}, ожидалось $cols"
                }
                DoubleArray(cols) { j -> row.getDouble(j) }
            }

            return Matrix(data)
        }
    }

    fun transpose(): Matrix {
        val result = Array(cols) { DoubleArray(rows) }
        for (i in 0 until rows) {
            for (j in 0 until cols) {
                result[j][i] = data[i][j]
            }
        }
        return Matrix(result)
    }

    fun multiply(other: Matrix): Matrix {
        require(cols == other.rows) { "Несовместимые размеры матриц для умножения" }

        val result = Array(rows) { DoubleArray(other.cols) }
        for (i in 0 until rows) {
            for (j in 0 until other.cols) {
                var sum = 0.0
                for (k in 0 until cols) {
                    sum += data[i][k] * other.data[k][j]
                }
                result[i][j] = sum
            }
        }
        return Matrix(result)
    }

    override fun toString(): String {
        val sb = StringBuilder()
        sb.append("[\n")
        for (i in 0 until rows) {
            sb.append("  [")
            for (j in 0 until cols) {
                sb.append(String.format("%.6f", data[i][j]))
                if (j < cols - 1) sb.append(", ")
            }
            sb.append("]")
            if (i < rows - 1) sb.append(",\n")
        }
        sb.append("\n]")
        return sb.toString()
    }

    fun isApproximatelyEqual(other: Matrix, tolerance: Double = 1e-6): Boolean {
        if (rows != other.rows || cols != other.cols) return false
        for (i in 0 until rows) {
            for (j in 0 until cols) {
                if (abs(data[i][j] - other.data[i][j]) > tolerance) return false
            }
        }
        return true
    }
}

// ==================== EigenSolver ====================
class EigenSolver {

    fun solveUnsorted(matrix: Matrix): Pair<DoubleArray, Array<DoubleArray>> {
        require(matrix.rows == matrix.cols) { "Матрица должна быть квадратной" }

        val n = matrix.rows
        val A = Array(n) { i -> matrix.data[i].clone() }

        val (y, characteristicPoly) = krylovMethod(A, n)
        val eigenValues = findPolynomialRoots(characteristicPoly, n)
        val eigenvectors = findEigenvectorsKrylov(y, eigenValues, characteristicPoly, n)

        return eigenValues to eigenvectors
    }

    private fun krylovMethod(A: Array<DoubleArray>, n: Int): Pair<Array<DoubleArray>, DoubleArray> {
        val y = Array(n + 1) { DoubleArray(n) }
        for (i in 0 until n) y[0][i] = 1.0

        for (i in 1..n) {
            y[i] = multiplyMatrixVector(A, y[i - 1], n)
        }

        // Формируем матрицу системы по y[0]..y[n-1], правая часть = y[n]
        val AMatrixTemp = Array(n) { row ->
            DoubleArray(n) { j -> y[(n - 1) - row][j] }
        }
        val AMatrix = Array(n) { i ->
            DoubleArray(n) { j -> AMatrixTemp[j][i] }
        }

        val f = y[n].clone()
        val resP = solveLinearSystem(AMatrix, f, n)

        // polyDesc: [a_n, a_{n-1}, ..., a_0]
        // a_n = 1, дальше -resP[0..n-1]
        val polyDesc = DoubleArray(n + 1)
        polyDesc[0] = 1.0
        for (i in 0 until n) polyDesc[i + 1] = -resP[i]

        return Pair(y, polyDesc)
    }

    /**
     * Поиск корней (бисекция + сканирование).
     * ВАЖНО: добавлена защита от bound=Infinity/NaN и лимиты итераций, чтобы не зависало.
     */
    private fun findPolynomialRoots(poly: DoubleArray, n: Int): DoubleArray {
        // poly: [a_n, ..., a_0]
        // Bound по Коши: 1 + max(|a_{n-1}..a_0|)/|a_n|
        val an = poly[0]
        if (abs(an) < 1e-18) {
            // плохой многочлен -> безопасный выход
            return DoubleArray(n)
        }

        var maxCoeff = 0.0
        for (i in 1 until poly.size) maxCoeff = max(maxCoeff, abs(poly[i]))
        val bound = 1.0 + maxCoeff / abs(an)

        // Защита от Infinity / NaN / неадекватных границ
        if (!bound.isFinite() || bound <= 0.0 || bound > 1e6) {
            return DoubleArray(n)
        }

        val roots = mutableListOf<Double>()
        val eps = 1e-7

        fun addRoot(root: Double) {
            for (r0 in roots) if (abs(r0 - root) < 1e-6) return
            roots.add(root)
        }

        // стартовый шаг: не слишком мелкий, иначе долго
        var step = (bound / (n * 2000.0)).coerceIn(1e-4, 1e-2)

        repeat(4) {
            if (roots.size >= n) return@repeat

            var left = 0.0
            var fLeft = evaluatePolynomial(poly, left)

            var iter = 0
            val maxIter = 2_000_000

            while (left < bound && roots.size < n && iter < maxIter) {
                iter++

                val right = minOf(left + step, bound)
                val fRight = evaluatePolynomial(poly, right)

                if (abs(fLeft) < eps) addRoot(left)
                if (abs(fRight) < eps) addRoot(right)

                if (fLeft * fRight < 0.0) {
                    var a = left
                    var b = right
                    var fa = fLeft
                    var fb = fRight

                    var bisIter = 0
                    val maxBisIter = 200
                    while (b - a >= eps && bisIter < maxBisIter) {
                        bisIter++
                        val mid = (a + b) / 2.0
                        val fm = evaluatePolynomial(poly, mid)
                        if (fa * fm < 0.0) {
                            b = mid
                            fb = fm
                        } else {
                            a = mid
                            fa = fm
                        }
                    }
                    addRoot((a + b) / 2.0)
                }

                left = right
                fLeft = fRight
            }

            // уточнение сетки — но не уходим в микрошаги
            step = max(step / 10.0, 1e-5)
        }

        roots.sort()
        return DoubleArray(n) { i -> if (i < roots.size) roots[i] else 0.0 }
    }

    // poly хранится по убыванию степеней: [a_n, a_{n-1}, ..., a_0]
    private fun evaluatePolynomial(poly: DoubleArray, x: Double): Double {
        var acc = poly[0]
        for (i in 1 until poly.size) {
            acc = acc * x + poly[i]
        }
        return acc
    }

    private fun findEigenvectorsKrylov(
        y: Array<DoubleArray>,
        eigenValues: DoubleArray,
        poly: DoubleArray,
        n: Int
    ): Array<DoubleArray> {
        // eigenvectors[i] = i-й собственный вектор (строка)
        val eigenvectors = Array(n) { DoubleArray(n) }

        for (i in 0 until n) {
            val lambda = eigenValues[i]

            // x = y[n-1]
            val x = y[n - 1].clone()

            val q = mutableListOf(1.0)

            // j=2..n
            for (j in 2..n) {
                val qJ = lambda * q[j - 2] + poly[j - 1]
                q.add(qJ)

                val yIndex = n - j // y[n-2],...,y[0]
                for (k in 0 until n) x[k] += qJ * y[yIndex][k]
            }

            var norm = 0.0
            for (k in 0 until n) norm += x[k] * x[k]
            norm = sqrt(norm)

            if (norm > 1e-12) {
                for (k in 0 until n) eigenvectors[i][k] = x[k] / norm
            } else {
                eigenvectors[i][i] = 1.0
            }
        }

        return eigenvectors
    }

    private fun multiplyMatrixVector(A: Array<DoubleArray>, x: DoubleArray, n: Int): DoubleArray {
        val y = DoubleArray(n)
        for (i in 0 until n) {
            var sum = 0.0
            for (j in 0 until n) sum += A[i][j] * x[j]
            y[i] = sum
        }
        return y
    }

    private fun solveLinearSystem(A: Array<DoubleArray>, b: DoubleArray, n: Int): DoubleArray {
        val augmented = Array(n) { i ->
            DoubleArray(n + 1) { j -> if (j < n) A[i][j] else b[i] }
        }

        for (k in 0 until n - 1) {
            var maxRow = k
            var maxVal = abs(augmented[k][k])
            for (i in k + 1 until n) {
                val v = abs(augmented[i][k])
                if (v > maxVal) {
                    maxVal = v
                    maxRow = i
                }
            }
            if (maxVal < 1e-12) continue

            if (maxRow != k) {
                val tmp = augmented[k]
                augmented[k] = augmented[maxRow]
                augmented[maxRow] = tmp
            }

            for (i in k + 1 until n) {
                val piv = augmented[k][k]
                if (abs(piv) < 1e-12) continue
                val factor = augmented[i][k] / piv
                for (j in k until n + 1) augmented[i][j] -= factor * augmented[k][j]
            }
        }

        val x = DoubleArray(n)
        for (i in n - 1 downTo 0) {
            var sum = augmented[i][n]
            for (j in i + 1 until n) sum -= augmented[i][j] * x[j]
            val piv = augmented[i][i]
            x[i] = if (abs(piv) > 1e-12) sum / piv else 0.0
        }

        return x
    }
}

// ==================== SVD ====================
data class SVDResult(
    val U: Matrix,
    val S: Matrix,
    val Vt: Matrix
) {
    fun reconstruct(): Matrix {
        val m = U.rows
        val n = Vt.cols
        val r = minOf(S.rows, S.cols)
        val Arec = Array(m) { DoubleArray(n) }

        for (k in 0 until r) {
            val sigma = S.data[k][k]
            if (abs(sigma) < 1e-12) continue
            for (i in 0 until m) {
                val uik = U.data[i][k]
                for (j in 0 until n) {
                    Arec[i][j] += sigma * uik * Vt.data[k][j]
                }
            }
        }

        return Matrix(Arec)
    }
}

object SVD {
    fun decompose(A: Matrix): SVDResult {
        val m = A.rows
        val n = A.cols
        val r = minOf(m, n)

        val AArray = A.data
        val At = transpose(AArray)

        val B = multiply(At, AArray)  // n x n

        val eigenSolver = EigenSolver()
        val (eigValsB, Vfull) = eigenSolver.solveUnsorted(Matrix(B))

        for (v in eigValsB) {
            require(v >= -1e-10) { "Отрицательное собственное значение: $v" }
        }

        val idxB = eigValsB.indices.sortedByDescending { eigValsB[it] }.toIntArray()
        val lambdaSortedB = DoubleArray(n) { eigValsB[idxB[it]] }

        val sing = DoubleArray(r)
        for (i in 0 until r) sing[i] = sqrt(max(0.0, lambdaSortedB[i]))

        // V: столбцы = собственные векторы B
        // ВАЖНО: Vfull хранит векторы по строкам: Vfull[vecIndex][i]
        val V = Array(n) { DoubleArray(n) }
        for (col in 0 until n) {
            val vec = Vfull[idxB[col]]
            for (i in 0 until n) V[i][col] = vec[i]
            gramSchmidtColumnInPlace(V, col)
            normalizeColumnInPlace(V, col)
        }

        // U: u_k = A v_k / sigma_k
        val U = Array(m) { DoubleArray(m) }
        for (k in 0 until r) {
            val sigma = sing[k]
            if (sigma < 1e-12) continue

            val vk = DoubleArray(n) { i -> V[i][k] }
            val Avk = multiplyMatVec(AArray, vk)
            for (i in 0 until m) U[i][k] = Avk[i] / sigma
            normalizeColumnInPlace(U, k)
        }

        // дополняем U до ортонормального базиса
        for (k in 0 until m) {
            if (colNorm(U, k) < 1e-10) {
                U[k][k] = 1.0
                gramSchmidtColumnInPlace(U, k)
                normalizeColumnInPlace(U, k)
            }
        }

        val Vt = transpose(V)

        val SMatrix = Matrix(Array(m) { i ->
            DoubleArray(n) { j ->
                if (i == j && i < sing.size) sing[i] else 0.0
            }
        })

        return SVDResult(Matrix(U), SMatrix, Matrix(Vt))
    }

    private fun transpose(A: Array<DoubleArray>): Array<DoubleArray> {
        val m = A.size
        val n = A[0].size
        val T = Array(n) { DoubleArray(m) }
        for (i in 0 until m) for (j in 0 until n) T[j][i] = A[i][j]
        return T
    }

    private fun multiply(A: Array<DoubleArray>, B: Array<DoubleArray>): Array<DoubleArray> {
        val m = A.size
        val p = A[0].size
        val n = B[0].size
        require(B.size == p) { "Несовместимые размеры для умножения" }
        val C = Array(m) { DoubleArray(n) }
        for (i in 0 until m) {
            for (k in 0 until p) {
                val aik = A[i][k]
                for (j in 0 until n) C[i][j] += aik * B[k][j]
            }
        }
        return C
    }

    private fun multiplyMatVec(A: Array<DoubleArray>, x: DoubleArray): DoubleArray {
        val m = A.size
        val n = A[0].size
        require(x.size == n) { "Несовместимые размеры mat-vec" }
        val y = DoubleArray(m)
        for (i in 0 until m) {
            var s = 0.0
            for (j in 0 until n) s += A[i][j] * x[j]
            y[i] = s
        }
        return y
    }

    private fun colNorm(A: Array<DoubleArray>, k: Int): Double {
        var s = 0.0
        for (i in A.indices) s += A[i][k] * A[i][k]
        return sqrt(s)
    }

    private fun normalizeColumnInPlace(A: Array<DoubleArray>, k: Int) {
        val n = colNorm(A, k)
        if (n < 1e-18) return
        for (i in A.indices) A[i][k] /= n
    }

    private fun gramSchmidtColumnInPlace(V: Array<DoubleArray>, k: Int) {
        for (j in 0 until k) {
            val dot = dotColumns(V, j, k)
            for (i in V.indices) V[i][k] -= dot * V[i][j]
        }
    }

    private fun dotColumns(A: Array<DoubleArray>, c1: Int, c2: Int): Double {
        var s = 0.0
        for (i in A.indices) s += A[i][c1] * A[i][c2]
        return s
    }
}

// ==================== SVDValidator (EJML) ====================
data class ComparisonResult(
    val matricesMatch: Boolean,
    val singularValuesMatch: Boolean,
    val customSingularValues: DoubleArray,
    val ejmlSingularValues: DoubleArray
)

object SVDValidator {
    fun decomposeWithEJML(matrix: Matrix): Triple<Matrix, Matrix, Matrix> {
        val m = matrix.rows
        val n = matrix.cols

        val ejmlMatrix = SimpleMatrix(m, n)
        for (i in 0 until m) {
            for (j in 0 until n) {
                ejmlMatrix.set(i, j, matrix.data[i][j])
            }
        }

        val svd = ejmlMatrix.svd()
        val U_ejml: org.ejml.simple.SimpleMatrix = svd.u
        val W: org.ejml.simple.SimpleMatrix = svd.w
        val V: org.ejml.simple.SimpleMatrix = svd.v
        val Vt_ejml: org.ejml.simple.SimpleMatrix = V.transpose()

        val r = minOf(m, n)
        val singularValues = DoubleArray(r) { i -> W.get(i, i) }

        val U = Matrix(Array(m) { i ->
            DoubleArray(m) { j -> U_ejml.get(i, j) }
        })
        val S = Matrix(Array(m) { i ->
            DoubleArray(n) { j -> if (i == j && i < singularValues.size) singularValues[i] else 0.0 }
        })
        val Vt = Matrix(Array(n) { i ->
            DoubleArray(n) { j -> Vt_ejml.get(i, j) }
        })

        return Triple(U, S, Vt)
    }

    fun compareResults(
        customResult: SVDResult,
        ejmlResult: Triple<Matrix, Matrix, Matrix>,
        tolerance: Double = 1e-4
    ): ComparisonResult {
        val (ejmlU, ejmlS, ejmlVt) = ejmlResult

        val customReconstructed = customResult.reconstruct()
        val ejmlReconstructed = ejmlU.multiply(ejmlS).multiply(ejmlVt)

        val matricesMatch = customReconstructed.isApproximatelyEqual(ejmlReconstructed, tolerance)

        val customSingularValues = extractSingularValues(customResult.S)
        val ejmlSingularValues = extractSingularValues(ejmlS)

        val singularValuesMatch = compareSingularValues(customSingularValues, ejmlSingularValues, tolerance)

        return ComparisonResult(
            matricesMatch = matricesMatch,
            singularValuesMatch = singularValuesMatch,
            customSingularValues = customSingularValues,
            ejmlSingularValues = ejmlSingularValues
        )
    }

    private fun extractSingularValues(S: Matrix): DoubleArray {
        val minDim = minOf(S.rows, S.cols)
        return DoubleArray(minDim) { i -> S.data[i][i] }
    }

    private fun compareSingularValues(custom: DoubleArray, ejml: DoubleArray, tolerance: Double): Boolean {
        if (custom.size != ejml.size) return false
        for (i in custom.indices) {
            if (abs(custom[i] - ejml[i]) > tolerance) return false
        }
        return true
    }
}

// ==================== MainActivity ====================
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            SvdTheme {
                Scaffold(modifier = Modifier.fillMaxSize()) { innerPadding ->
                    SVDCalculatorScreen(modifier = Modifier.padding(innerPadding))
                }
            }
        }
    }
}

@Composable
fun SVDCalculatorScreen(modifier: Modifier = Modifier) {
    var matrixJson by remember {
        mutableStateOf(
            "[[8.02, 6.04, 4.58], [8.76, 5.32, 1.84], [5.01, 8.95, 5.16], [9.45, 8.26, 7.09], [1.30, 5.08, 9.43]]"
        )
    }
    var result by remember { mutableStateOf<SVDResult?>(null) }
    var errorMessage by remember { mutableStateOf<String?>(null) }
    var comparisonResult by remember { mutableStateOf<ComparisonResult?>(null) }
    var isCalculating by remember { mutableStateOf(false) }

    val scope = rememberCoroutineScope()

    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(16.dp)
            .verticalScroll(rememberScrollState()),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        Text(text = "SVD Calculator", style = MaterialTheme.typography.headlineLarge)

        Text(text = "Введите матрицу в формате JSON:", style = MaterialTheme.typography.bodyMedium)

        OutlinedTextField(
            value = matrixJson,
            onValueChange = { matrixJson = it },
            modifier = Modifier.fillMaxWidth(),
            label = { Text("Матрица (JSON)") },
            placeholder = { Text("[[1.0, 2.0], [3.0, 4.0]]") },
            minLines = 3,
            maxLines = 5
        )

        Button(
            onClick = {
                isCalculating = true
                errorMessage = null
                result = null
                comparisonResult = null

                scope.launch {
                    try {
                        val matrix = Matrix.fromJson(matrixJson)

                        val svdResult = withContext(Dispatchers.Default) {
                            SVD.decompose(matrix)
                        }

                        val ejmlResult = withContext(Dispatchers.Default) {
                            SVDValidator.decomposeWithEJML(matrix)
                        }

                        val comp = withContext(Dispatchers.Default) {
                            SVDValidator.compareResults(svdResult, ejmlResult)
                        }

                        result = svdResult
                        comparisonResult = comp
                    } catch (e: Exception) {
                        errorMessage = "Ошибка: ${e.message}"
                    } finally {
                        isCalculating = false
                    }
                }
            },
            modifier = Modifier.fillMaxWidth(),
            enabled = !isCalculating
        ) {
            if (isCalculating) {
                CircularProgressIndicator(modifier = Modifier.size(20.dp))
                Spacer(modifier = Modifier.width(8.dp))
            }
            Text("Вычислить SVD")
        }

        if (errorMessage != null) {
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.errorContainer)
            ) {
                Text(
                    text = errorMessage!!,
                    modifier = Modifier.padding(16.dp),
                    color = MaterialTheme.colorScheme.onErrorContainer
                )
            }
        }

        result?.let { svd ->
            Card(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text("Исходная матрица A:", style = MaterialTheme.typography.titleMedium)
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        text = Matrix.fromJson(matrixJson).toString(),
                        style = MaterialTheme.typography.bodySmall,
                        fontFamily = FontFamily.Monospace
                    )
                }
            }

            Card(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text("Матрица U:", style = MaterialTheme.typography.titleMedium)
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        text = svd.U.toString(),
                        style = MaterialTheme.typography.bodySmall,
                        fontFamily = FontFamily.Monospace
                    )
                }
            }

            Card(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text("Матрица S (сингулярные значения):", style = MaterialTheme.typography.titleMedium)
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        text = svd.S.toString(),
                        style = MaterialTheme.typography.bodySmall,
                        fontFamily = FontFamily.Monospace
                    )
                }
            }

            Card(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text("Матрица Vt:", style = MaterialTheme.typography.titleMedium)
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        text = svd.Vt.toString(),
                        style = MaterialTheme.typography.bodySmall,
                        fontFamily = FontFamily.Monospace
                    )
                }
            }

            Card(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text("Проверка: A = U * S * Vt", style = MaterialTheme.typography.titleMedium)
                    Spacer(modifier = Modifier.height(8.dp))
                    val reconstructed = svd.reconstruct()
                    Text(
                        text = reconstructed.toString(),
                        style = MaterialTheme.typography.bodySmall,
                        fontFamily = FontFamily.Monospace
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    val original = Matrix.fromJson(matrixJson)
                    val isEqual = reconstructed.isApproximatelyEqual(original, 1e-4)
                    Text(
                        text = if (isEqual) "✓ Матрицы совпадают!" else "✗ Матрицы не совпадают",
                        color = if (isEqual) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.error
                    )
                }
            }

            comparisonResult?.let { comp ->
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(
                        containerColor = if (comp.matricesMatch && comp.singularValuesMatch) {
                            MaterialTheme.colorScheme.primaryContainer
                        } else {
                            MaterialTheme.colorScheme.errorContainer
                        }
                    )
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text("Сравнение с библиотечным методом (EJML):", style = MaterialTheme.typography.titleMedium)
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            text = "Матрицы совпадают: ${if (comp.matricesMatch) "✓ Да" else "✗ Нет"}",
                            color = if (comp.matricesMatch) MaterialTheme.colorScheme.onPrimaryContainer else MaterialTheme.colorScheme.onErrorContainer
                        )
                        Text(
                            text = "Сингулярные значения совпадают: ${if (comp.singularValuesMatch) "✓ Да" else "✗ Нет"}",
                            color = if (comp.singularValuesMatch) MaterialTheme.colorScheme.onPrimaryContainer else MaterialTheme.colorScheme.onErrorContainer
                        )
                        Spacer(modifier = Modifier.height(8.dp))
                        Text("Наши сингулярные значения:", style = MaterialTheme.typography.bodySmall)
                        Text(
                            text = comp.customSingularValues.joinToString(", ") { "%.6f".format(it) },
                            style = MaterialTheme.typography.bodySmall,
                            fontFamily = FontFamily.Monospace
                        )
                        Text("EJML сингулярные значения:", style = MaterialTheme.typography.bodySmall)
                        Text(
                            text = comp.ejmlSingularValues.joinToString(", ") { "%.6f".format(it) },
                            style = MaterialTheme.typography.bodySmall,
                            fontFamily = FontFamily.Monospace
                        )
                    }
                }
            }
        }
    }
}
