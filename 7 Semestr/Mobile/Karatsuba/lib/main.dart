import 'dart:math';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

void main() => runApp(const MyApp());

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Двоичное умножение',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(useMaterial3: true, colorSchemeSeed: Colors.blue),
      home: const MultiplicationPage(),
    );
  }
}

class MultiplicationPage extends StatefulWidget {
  const MultiplicationPage({super.key});

  @override
  State<MultiplicationPage> createState() => _MultiplicationPageState();
}

class _MultiplicationPageState extends State<MultiplicationPage> {
  final _aCtrl = TextEditingController();
  final _bCtrl = TextEditingController();

  String _error = '';
  String _schoolRes = '';
  String _karaRes = '';
  String _schoolTime = '';
  String _karaTime = '';
  String _note = '';

  static const int _threshold = 64;

  @override
  void dispose() {
    _aCtrl.dispose();
    _bCtrl.dispose();
    super.dispose();
  }

  void _multiply() {
    setState(() {
      _error = '';
      _schoolRes = '';
      _karaRes = '';
      _schoolTime = '';
      _karaTime = '';
      _note = '';
    });

    try {
      final aStr = _sanitize(_aCtrl.text);
      final bStr = _sanitize(_bCtrl.text);

      _validateBinary(aStr, 'первого числа');
      _validateBinary(bStr, 'второго числа');

      final aBits = _parseBinaryToBitsLE(aStr);
      final bBits = _parseBinaryToBitsLE(bStr);

      final sw1 = Stopwatch()..start();
      final schoolBits = _schoolbookMulBits(aBits, bBits);
      sw1.stop();

      final sw2 = Stopwatch()..start();
      final karaBits = _karatsubaMulBits(aBits, bBits, threshold: _threshold);
      sw2.stop();

      final schoolBin = _bitsToBinaryStringBE(schoolBits);
      final karaBin = _bitsToBinaryStringBE(karaBits);

      final same = schoolBin == karaBin;

      setState(() {
        _schoolRes = schoolBin;
        _karaRes = karaBin;
        _schoolTime = _formatDuration(sw1.elapsedMicroseconds);
        _karaTime = _formatDuration(sw2.elapsedMicroseconds);
        _note = same
            ? 'Результаты совпадают'
            : 'ВНИМАНИЕ: результаты НЕ совпадают';
      });
    } catch (e) {
      setState(() => _error = e.toString());
    }
  }

  void _copy(String text) async {
    if (text.isEmpty) return;
    await Clipboard.setData(ClipboardData(text: text));
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Скопировано в буфер обмена')),
    );
  }

  String _sanitize(String s) {
    return s.replaceAll(RegExp(r'\s+'), '');
  }

  void _validateBinary(String s, String which) {
    if (s.isEmpty) {
      throw Exception('Пустой ввод для $which.');
    }
    if (!RegExp(r'^[01]+$').hasMatch(s)) {
      throw Exception('Ввод для $which должен быть только из 0 и 1.');
    }
  }

  List<int> _parseBinaryToBitsLE(String s) {
    final bits = <int>[];
    for (int i = s.length - 1; i >= 0; i--) {
      bits.add(s.codeUnitAt(i) == 49 ? 1 : 0); // '1' => 49
    }
    return _trim(bits);
  }

  String _bitsToBinaryStringBE(List<int> bitsLE) {
    final t = _trim(List<int>.from(bitsLE));
    final sb = StringBuffer();
    for (int i = t.length - 1; i >= 0; i--) {
      sb.write(t[i] == 1 ? '1' : '0');
    }
    return sb.toString();
  }

  String _formatDuration(int micros) {
    final ms = micros / 1000.0;
    return '${micros} мкс  (~${ms.toStringAsFixed(3)} мс)';
  }

  List<int> _trim(List<int> a) {
    int i = a.length - 1;
    while (i > 0 && a[i] == 0) i--;
    return a.sublist(0, i + 1);
  }

  List<int> _addBits(List<int> a, List<int> b) {
    final n = max(a.length, b.length);
    final res = List<int>.filled(n + 1, 0);
    int carry = 0;
    for (int i = 0; i < n; i++) {
      final ai = (i < a.length) ? a[i] : 0;
      final bi = (i < b.length) ? b[i] : 0;
      final s = ai + bi + carry;
      res[i] = s & 1;
      carry = s >> 1;
    }
    res[n] = carry;
    return _trim(res);
  }

  int _compareBits(List<int> a, List<int> b) {
    final aa = _trim(List<int>.from(a));
    final bb = _trim(List<int>.from(b));
    if (aa.length != bb.length) return aa.length.compareTo(bb.length);
    for (int i = aa.length - 1; i >= 0; i--) {
      if (aa[i] != bb[i]) return aa[i].compareTo(bb[i]);
    }
    return 0;
  }

  List<int> _subBits(List<int> a, List<int> b) {
    if (_compareBits(a, b) < 0) {
      throw Exception('Ошибка вычитания: a < b (это не должно случиться в Карацубе).');
    }
    final res = List<int>.filled(a.length, 0);
    int borrow = 0;
    for (int i = 0; i < a.length; i++) {
      final ai = a[i];
      final bi = (i < b.length) ? b[i] : 0;
      int d = ai - bi - borrow;
      if (d < 0) {
        d += 2;
        borrow = 1;
      } else {
        borrow = 0;
      }
      res[i] = d;
    }
    return _trim(res);
  }

  List<int> _shiftLeft(List<int> a, int k) {
    if (k <= 0) return _trim(List<int>.from(a));
    final t = _trim(List<int>.from(a));
    if (t.length == 1 && t[0] == 0) return t;
    return List<int>.filled(k, 0)..addAll(t);
  }

  ({List<int> high, List<int> low}) _splitBits(List<int> a, int m) {
    final t = _trim(List<int>.from(a));
    if (m >= t.length) {
      return (high: [0], low: t);
    }
    final low = t.sublist(0, m);
    final high = _trim(t.sublist(m));
    return (high: high, low: _trim(low));
  }

  List<int> _schoolbookMulBits(List<int> x, List<int> y) {
    final a = _trim(List<int>.from(x));
    final b = _trim(List<int>.from(y));

    if ((a.length == 1 && a[0] == 0) || (b.length == 1 && b[0] == 0)) return [0];

    final res = List<int>.filled(a.length + b.length + 1, 0);
    for (int i = 0; i < a.length; i++) {
      if (a[i] == 0) continue;
      for (int j = 0; j < b.length; j++) {
        if (b[j] == 0) continue;
        res[i + j] += 1; // 1*1
      }
    }

    int carry = 0;
    for (int i = 0; i < res.length; i++) {
      final s = res[i] + carry;
      res[i] = s & 1;
      carry = s >> 1;
    }
    return _trim(res);
  }

  List<int> _karatsubaMulBits(List<int> x, List<int> y, {required int threshold}) {
    final a = _trim(List<int>.from(x));
    final b = _trim(List<int>.from(y));

    if ((a.length == 1 && a[0] == 0) || (b.length == 1 && b[0] == 0)) return [0];

    final maxLen = max(a.length, b.length);
    if (maxLen <= threshold) {
      return _schoolbookMulBits(a, b);
    }

    final k = maxLen ~/ 2;

    final sa = _splitBits(a, k);
    final sb = _splitBits(b, k);

    final xl = sa.low;
    final xh = sa.high;
    final yl = sb.low;
    final yh = sb.high;

    final z0 = _karatsubaMulBits(xl, yl, threshold: threshold);
    final z2 = _karatsubaMulBits(xh, yh, threshold: threshold);
    final z1 = _karatsubaMulBits(_addBits(xl, xh), _addBits(yl, yh), threshold: threshold);

    final t1 = _subBits(z1, z2);
    final middle = _subBits(t1, z0);

    final term1 = _shiftLeft(z2, 2 * k);
    final term2 = _shiftLeft(middle, k);

    return _addBits(_addBits(term1, term2), z0);
  }


  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Умножение двоичных чисел (Карацуба / Столбик)'),
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            const Text(
              'Вводите только 0 и 1. Пробелы и переносы строк игнорируются.',
              style: TextStyle(fontSize: 13),
            ),
            const SizedBox(height: 12),

            _bigBinaryField(
              controller: _aCtrl,
              label: 'Число A (bin)',
              hint: 'например: 101010001011...',
            ),
            const SizedBox(height: 12),
            _bigBinaryField(
              controller: _bCtrl,
              label: 'Число B (bin)',
              hint: 'например: 111000101...',
            ),

            const SizedBox(height: 12),
            Row(
              children: [
                FilledButton(
                  onPressed: _multiply,
                  child: const Text('Умножить'),
                ),
                const SizedBox(width: 12),
                OutlinedButton(
                  onPressed: () {
                    setState(() {
                      _aCtrl.clear();
                      _bCtrl.clear();
                      _error = '';
                      _schoolRes = '';
                      _karaRes = '';
                      _schoolTime = '';
                      _karaTime = '';
                      _note = '';
                    });
                  },
                  child: const Text('Очистить'),
                ),
              ],
            ),

            const SizedBox(height: 12),
            if (_error.isNotEmpty)
              Text(_error, style: const TextStyle(color: Colors.red)),

            if (_note.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(_note, style: TextStyle(color: _note.contains('НЕ') ? Colors.red : Colors.green)),
            ],

            const SizedBox(height: 16),

            if (_schoolRes.isNotEmpty) _resultCard(
              title: 'Столбик (O(n²))',
              time: _schoolTime,
              value: _schoolRes,
              onCopy: () => _copy(_schoolRes),
            ),

            if (_karaRes.isNotEmpty) _resultCard(
              title: 'Карацуба (O(n^log2(3)))',
              time: _karaTime,
              value: _karaRes,
              onCopy: () => _copy(_karaRes),
            ),
          ],
        ),
      ),
    );
  }

  Widget _bigBinaryField({
    required TextEditingController controller,
    required String label,
    required String hint,
  }) {
    return TextField(
      controller: controller,
      maxLines: 6,
      minLines: 4,
      keyboardType: TextInputType.multiline,
      textInputAction: TextInputAction.newline,
      style: const TextStyle(fontFamily: 'monospace', fontSize: 14),
      decoration: InputDecoration(
        labelText: label,
        hintText: hint,
        border: const OutlineInputBorder(),
        alignLabelWithHint: true,
      ),
    );
  }

  Widget _resultCard({
    required String title,
    required String time,
    required String value,
    required VoidCallback onCopy,
  }) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(child: Text(title, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600))),
                IconButton(
                  tooltip: 'Скопировать результат',
                  onPressed: onCopy,
                  icon: const Icon(Icons.copy),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Text('Время: $time'),
            const SizedBox(height: 10),
            const Text('Результат (bin):'),
            const SizedBox(height: 6),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: Colors.black12),
              ),
              child: SelectableText(
                value,
                style: const TextStyle(fontFamily: 'monospace', fontSize: 13, height: 1.25),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
