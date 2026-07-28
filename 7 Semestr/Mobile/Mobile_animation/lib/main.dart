import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

void main() => runApp(const Lab3App());

class Lab3App extends StatelessWidget {
  const Lab3App({super.key});

  @override
  Widget build(BuildContext context) {
    return const CupertinoApp(
      debugShowCheckedModeBanner: false,
      title: 'Lab3',
      home: Lab3Home(),
    );
  }
}

/// LAB3
class Lab3Home extends StatelessWidget {
  const Lab3Home({super.key});

  void open(BuildContext context, Widget page) {
    Navigator.of(context).push(CupertinoPageRoute(builder: (_) => page));
  }

  @override
  Widget build(BuildContext context) {
    return CupertinoPageScaffold(
      navigationBar: const CupertinoNavigationBar(middle: Text('Меню')),
      child: SafeArea(
        minimum: const EdgeInsets.all(16),
        child: ListView(
          children: [
            const SizedBox(height: 12),
            CupertinoButton.filled(
              onPressed: () => open(context, const Lab1Page(title: 'Arinin Matvey')),
              padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 16),
              child: const Align(
                alignment: Alignment.centerLeft,
                child: Text('lab1 — Кликер'),
              ),
            ),
            const SizedBox(height: 12),
            CupertinoButton.filled(
              onPressed: () => open(context, const IoControlPageCupertino()),
              padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 16),
              child: const Align(
                alignment: Alignment.centerLeft,
                child: Text('lab2 — IoControl'),
              ),
            ),
            const SizedBox(height: 12),
            CupertinoButton.filled(
              onPressed: () => open(context, const EmptyPage(title: 'Lab4 Placeholder')),
              padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 16),
              child: const Align(
                alignment: Alignment.centerLeft,
                child: Text('lab4 — Заглушка'),
              ),
            ),
            const SizedBox(height: 12),
            CupertinoButton.filled(
              onPressed: () => open(context, const Lab4SegmentsPage()),
              padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 16),
              child: const Align(
                alignment: Alignment.centerLeft,
                child: Text('lab4 — Множество отрезков'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// LAB1
class Lab1Page extends StatefulWidget {
  const Lab1Page({super.key, required this.title});
  final String title;

  @override
  State<Lab1Page> createState() => Lab1PageState();
}

class Lab1PageState extends State<Lab1Page> {
  int counter = 0;
  void incrementCounter() => setState(() => counter++);

  @override
  Widget build(BuildContext context) {
    return CupertinoPageScaffold(
      navigationBar: const CupertinoNavigationBar(
        middle: Text('Lab1 — Кликер'),
      ),
      child: SafeArea(
        child: Localizations(
          locale: const Locale('en', 'US'),
          delegates: const [
            DefaultWidgetsLocalizations.delegate,
            DefaultMaterialLocalizations.delegate,
            DefaultCupertinoLocalizations.delegate,
          ],
          child: Theme(
            data: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple)),
            child: Material(
              type: MaterialType.transparency,
              child: Scaffold(
                body: Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: <Widget>[
                      const Text('Вы нажали на кнопку столько раз:'),
                      Text('$counter', style: Theme.of(context).textTheme.headlineMedium),
                    ],
                  ),
                ),
                floatingActionButton: FloatingActionButton(
                  onPressed: incrementCounter,
                  tooltip: 'Increment',
                  child: const Icon(Icons.add),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

/// LAB2
class IoControlPageCupertino extends StatefulWidget {
  const IoControlPageCupertino({super.key});

  @override
  State<IoControlPageCupertino> createState() => IoControlPageCupertinoState();
}

class IoControlPageCupertinoState extends State<IoControlPageCupertino> {
  final String board = "Arinin";
  final String switchVar = "Switch";
  final String leftVar = "left";
  final String rightVar = "right";

  bool isOn = false;
  int left = 0;
  int right = 0;
  bool busy = false;

  static const int minV = 0;
  static const int maxV = 100;

  Uri send(String varName, [String? value]) => Uri.parse(
      value == null
          ? "http://iocontrol.ru/api/sendData/$board/$varName"
          : "http://iocontrol.ru/api/sendData/$board/$varName/$value");

  Uri read(String varName) =>
      Uri.parse("http://iocontrol.ru/api/readData/$board/$varName");

  @override
  void initState() {
    super.initState();
    initLoad();
  }

  Future<void> initLoad() async {
    await readSwitch();
    await Future.wait([readLeft(), readRight()]);
    if (mounted) setState(() {});
  }

  Future<void> readSwitch() async {
    try {
      final r = await http.get(read(switchVar));
      if (r.statusCode == 200) {
        final data = jsonDecode(r.body);
        isOn = (data["value"] ?? "").toString().trim() == "1";
      }
    } catch (_) {}
  }

  Future<void> setSwitch(bool on) async {
    setState(() => busy = true);
    try {
      final r = await http.get(send(switchVar, on ? "1" : "0"));
      if (r.statusCode == 200) {
        setState(() => isOn = on);
        if (on) {
          await Future.wait([sendLeft(left), sendRight(right)]);
        }
      }
    } catch (_) {} finally {
      if (mounted) setState(() => busy = false);
    }
  }

  Future<void> readLeft() async {
    try {
      final r = await http.get(read(leftVar));
      if (r.statusCode == 200) {
        final data = jsonDecode(r.body);
        left = (int.tryParse((data["value"] ?? "0").toString()) ?? 0)
            .clamp(minV, maxV);
      }
    } catch (_) {}
  }

  Future<void> readRight() async {
    try {
      final r = await http.get(read(rightVar));
      if (r.statusCode == 200) {
        final data = jsonDecode(r.body);
        right = (int.tryParse((data["value"] ?? "0").toString()) ?? 0)
            .clamp(minV, maxV);
      }
    } catch (_) {}
  }

  Future<void> sendLeft(int value) async {
    final v = value.clamp(minV, maxV);
    try {
      await http.get(send(leftVar, "$v"));
    } catch (_) {}
  }

  Future<void> sendRight(int value) async {
    final v = value.clamp(minV, maxV);
    try {
      await http.get(send(rightVar, "$v"));
    } catch (_) {}
  }

  Future<void> changeLeft(int value) async {
    setState(() => left = value.clamp(minV, maxV));
    if (isOn) await sendLeft(left);
  }

  Future<void> changeRight(int value) async {
    setState(() => right = value.clamp(minV, maxV));
    if (isOn) await sendRight(right);
  }

  Future<void> resetBoth() async {
    setState(() {
      left = 0;
      right = 0;
    });
    if (isOn) {
      await Future.wait([sendLeft(0), sendRight(0)]);
    }
  }

  String movementStatus() {
    if (!isOn) return "Выключено";
    if (left == 0 && right == 0) return "Покой";
    if (left == right && left > 0) return "Прямо";
    if (left > right) return "Влево";
    return "Вправо";
  }

  Widget counterRow({
    required String label,
    required int value,
    required Future<void> Function(int) onChange,
  }) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Text("$label: $value", style: const TextStyle(fontSize: 16)),
        const SizedBox(width: 16),
        CupertinoButton(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
          onPressed: () => onChange(value - 1),
          child: const Text("−", style: TextStyle(fontSize: 20)),
        ),
        const SizedBox(width: 4),
        CupertinoButton(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
          onPressed: () => onChange(value + 1),
          child: const Text("+", style: TextStyle(fontSize: 20)),
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    final statusColor = !isOn
        ? CupertinoColors.systemRed
        : (left == 0 && right == 0)
        ? CupertinoColors.systemGrey
        : CupertinoColors.activeGreen;

    return CupertinoPageScaffold(
      navigationBar: const CupertinoNavigationBar(middle: Text('Lab2 — IoControl')),
      child: SafeArea(
        minimum: const EdgeInsets.all(16),
        child: Column(
          children: [
            Row(
              children: [
                const Text("Питание (Switch): ", style: TextStyle(fontSize: 16)),
                Text(
                  isOn ? "ON" : "OFF",
                  style: TextStyle(color: statusColor, fontWeight: FontWeight.w600),
                ),
                const Spacer(),
                IgnorePointer(
                  ignoring: busy,
                  child: CupertinoSwitch(
                    value: isOn,
                    onChanged: (v) => setSwitch(v),
                  ),
                ),
              ],
            ),
            if (busy) ...[
              const SizedBox(height: 8),
              const CupertinoActivityIndicator(),
            ],
            const SizedBox(height: 24),
            counterRow(label: "left", value: left, onChange: changeLeft),
            const SizedBox(height: 12),
            counterRow(label: "right", value: right, onChange: changeRight),
            const SizedBox(height: 24),
            Text("Статус прибора: ${movementStatus()}",
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w500)),
            const Spacer(),
            CupertinoButton(
              onPressed: resetBoth,
              color: CupertinoColors.systemOrange,
              child: const Text("Обнулить оба"),
            ),
          ],
        ),
      ),
    );
  }
}


/// LAB4
class Lab4SegmentsPage extends StatefulWidget {
  const Lab4SegmentsPage({super.key});

  @override
  State<Lab4SegmentsPage> createState() => Lab4SegmentsPageState();
}

class LineSegment {
  final Offset a;
  final Offset b;
  final Color color;
  final double width;
  LineSegment({required this.a, required this.b, required this.color, required this.width});
}

class Lab4SegmentsPageState extends State<Lab4SegmentsPage> {
  final List<LineSegment> segments = [];

  Offset? dragStart;
  Offset? dragNow;

  double r = 255, g = 0, b = 0;
  final double strokeWidth = 7;

  Offset? lastA;
  Offset? lastB;

  int colorKey = 1;
  bool isColorButtonPressed = false;

  void setColor(int key) {
    setState(() {
      colorKey = key;
      isColorButtonPressed = true;
      switch (key) {
        case 1:
          r = 255; g = 0; b = 0;
          break;
        case 2:
          r = 0; g = 255; b = 0;
          break;
        case 3:
          r = 0; g = 0; b = 255;
          break;
        default:
          r = 255; g = 0; b = 0;
          break;
      }
    });
  }

  Color currentColor() => Color.fromARGB(255, r.toInt(), g.toInt(), b.toInt());

  void onPanStart(DragStartDetails d) {
    setState(() {
      dragStart = d.localPosition;
      dragNow = d.localPosition;
    });
  }

  void onPanUpdate(DragUpdateDetails d) {
    setState(() {
      dragNow = d.localPosition;
    });
  }

  void onPanEnd(DragEndDetails d) {
    if (dragStart != null && dragNow != null && (dragStart! - dragNow!).distance > 0.5) {
      final seg = LineSegment(
        a: dragStart!,
        b: dragNow!,
        color: currentColor(),
        width: strokeWidth,
      );
      setState(() {
        segments.add(seg);
        lastA = seg.a;
        lastB = seg.b;
      });
    }
    setState(() {
      dragStart = null;
      dragNow = null;
      isColorButtonPressed = false;
    });
  }

  String fmt(Offset? p) =>
      p == null ? "—" : "(${p.dx.toStringAsFixed(0)}, ${p.dy.toStringAsFixed(0)})";

  @override
  Widget build(BuildContext context) {
    final preview = (dragStart != null && dragNow != null)
        ? LineSegment(a: dragStart!, b: dragNow!, color: currentColor().withOpacity(0.6), width: strokeWidth)
        : null;

    return CupertinoPageScaffold(
      navigationBar: const CupertinoNavigationBar(
        middle: Text('Lab4 — Множество отрезков'),
      ),
      child: SafeArea(
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(12, 8, 12, 4),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const Text('Цвет (RGB)', style: TextStyle(fontSize: 14)),
                  Row(
                    children: [
                      const Text("R"),
                      Expanded(
                        child: CupertinoSlider(
                          min: 0,
                          max: 255,
                          value: r,
                          onChanged: (v) {
                            setState(() {
                              r = v;
                              isColorButtonPressed = false;
                            });
                          },
                        ),
                      ),
                      Text(r.toInt().toString()),
                    ],
                  ),
                  Row(
                    children: [
                      const Text("G"),
                      Expanded(
                        child: CupertinoSlider(
                          min: 0,
                          max: 255,
                          value: g,
                          onChanged: (v) {
                            setState(() {
                              g = v;
                              isColorButtonPressed = false;
                            });
                          },
                        ),
                      ),
                      Text(g.toInt().toString()),
                    ],
                  ),
                  Row(
                    children: [
                      const Text("B"),
                      Expanded(
                        child: CupertinoSlider(
                          min: 0,
                          max: 255,
                          value: b,
                          onChanged: (v) {
                            setState(() {
                              b = v;
                              isColorButtonPressed = false;
                            });
                          },
                        ),
                      ),
                      Text(b.toInt().toString()),
                    ],
                  ),
                  const SizedBox(height: 8),
                  const Text('Выберите цвет:', style: TextStyle(fontSize: 14)),
                  CupertinoSlidingSegmentedControl<int>(
                    groupValue: colorKey,
                    children: {
                      1: CupertinoButton.filled(
                        onPressed: () => setColor(1),
                        child: const Text("Красный"),
                      ),
                      2: CupertinoButton.filled(
                        onPressed: () => setColor(2),
                        child: const Text("Зелёный"),
                      ),
                      3: CupertinoButton.filled(
                        onPressed: () => setColor(3),
                        child: const Text("Синий"),
                      ),
                    },
                    onValueChanged: (v) {
                      setColor(v ?? 0);
                    },
                  ),
                ],
              ),
            ),

            // Канва
            Expanded(
              child: LayoutBuilder(
                builder: (context, constraints) {
                  return GestureDetector(
                    behavior: HitTestBehavior.opaque,
                    onPanStart: onPanStart,
                    onPanUpdate: onPanUpdate,
                    onPanEnd: onPanEnd,
                    child: CustomPaint(
                      painter: SegmentsPainter(segments: segments, preview: preview),
                      size: Size(constraints.maxWidth, constraints.maxHeight),
                    ),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class SegmentsPainter extends CustomPainter {
  final List<LineSegment> segments;
  final LineSegment? preview;

  SegmentsPainter({required this.segments, this.preview});

  @override
  void paint(Canvas canvas, Size size) {
    final bg = Paint()..color = const Color(0xFFF8F8F8);
    canvas.drawRect(Offset.zero & size, bg);

    for (final s in segments) {
      final p = Paint()
        ..color = s.color
        ..strokeWidth = s.width
        ..strokeCap = StrokeCap.round
        ..style = PaintingStyle.stroke;
      canvas.drawLine(s.a, s.b, p);
    }

    if (preview != null) {
      final p = Paint()
        ..color = preview!.color
        ..strokeWidth = preview!.width
        ..strokeCap = StrokeCap.round
        ..style = PaintingStyle.stroke;
      canvas.drawLine(preview!.a, preview!.b, p);
    }
  }

  @override
  bool shouldRepaint(covariant SegmentsPainter oldDelegate) {
    return oldDelegate.segments != segments || oldDelegate.preview != preview;
  }
}

class EmptyPage extends StatelessWidget {
  final String title;
  const EmptyPage({super.key, required this.title});

  @override
  Widget build(BuildContext context) {
    return CupertinoPageScaffold(
      navigationBar: CupertinoNavigationBar(middle: Text(title)),
      child: const SafeArea(child: Center(child: Text('Пустая страница'))),
    );
  }
}