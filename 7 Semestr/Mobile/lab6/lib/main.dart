import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:yandex_mapkit/yandex_mapkit.dart';
import 'dart:async';
import 'package:flutter/services.dart';

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
            const SizedBox(height: 12),
            CupertinoButton.filled(
              onPressed: () => open(context, const Lab6YandexMapPage()),
              padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 16),
              child: const Align(
                alignment: Alignment.centerLeft,
                child: Text('lab6 — Яндекс.Карты'),
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

// ------------------------ LAB6 (Яндекс.Карты) ------------------------
class _Place {
  final String name;
  final String address;
  final String tel;
  final Point point;
  _Place({required this.name, required this.address, required this.tel, required this.point});
}

class Lab6YandexMapPage extends StatefulWidget {
  const Lab6YandexMapPage({super.key});
  @override
  State<Lab6YandexMapPage> createState() => _Lab6YandexMapPageState();
}

class _Lab6YandexMapPageState extends State<Lab6YandexMapPage> {
  final urlCtrl = TextEditingController(
    text: 'http://pstgu.yss.su/iu9/mobiledev/lab4_yandex_map/2023.php?x=var16',
  );

  final Completer<YandexMapController> _controller = Completer();
  final List<MapObject> _mapObjects = [];
  final List<_Place> _items = [];

  int? _selectedIndex;
  bool _loading = false;
  String? _error;

  @override
  void dispose() {
    urlCtrl.dispose();
    super.dispose();
  }

  // Снять фокус + жёстко скрыть клавиатуру
  void _unfocus() {
    FocusManager.instance.primaryFocus?.unfocus();
    SystemChannels.textInput.invokeMethod('TextInput.hide');
  }

  Future<void> _loadData() async {
    _unfocus(); // скрыть клаву перед загрузкой
    setState(() {
      _loading = true;
      _error = null;
      _selectedIndex = null;
      _mapObjects.clear();
      _items.clear();
    });

    try {
      final resp = await http.get(Uri.parse(urlCtrl.text.trim()));
      if (resp.statusCode != 200) throw Exception('HTTP ${resp.statusCode}');
      final List<dynamic> raw = jsonDecode(utf8.decode(resp.bodyBytes));

      for (final e in raw) {
        final parts = (e['gps'] ?? '').toString().split(',');
        final lat = double.parse(parts[0].trim());
        final lon = double.parse(parts[1].trim());
        _items.add(_Place(
          name: (e['name'] ?? '').toString(),
          address: (e['address'] ?? '').toString(),
          tel: (e['tel'] ?? '').toString(),
          point: Point(latitude: lat, longitude: lon),
        ));
      }

      _rebuildMapObjects();
      await _fitAll(); // показать все точки в кадре
    } catch (e) {
      _error = 'Не удалось загрузить данные: $e';
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _rebuildMapObjects() {
    final objects = <MapObject>[];
    for (var i = 0; i < _items.length; i++) {
      final p = _items[i];
      final isSel = i == _selectedIndex;
      objects.add(
        PlacemarkMapObject(
          mapId: MapObjectId('place_$i'),
          point: p.point,
          icon: PlacemarkIcon.single(
            PlacemarkIconStyle(
              image: BitmapDescriptor.fromAssetImage('assets/marker.png'),
              // уменьшаем пины (при необходимости опусти до 0.06 / 0.05)
              scale: isSel ? 0.12 : 0.08,
              anchor: const Offset(0.5, 1.0),
            ),
          ),
          onTap: (_, __) => _onSelect(i, showSheet: true),
        ),
      );
    }
    setState(() {
      _mapObjects
        ..clear()
        ..addAll(objects);
    });
  }

  Future<void> _fitAll() async {
    if (_items.isEmpty) return;
    final lats = _items.map((e) => e.point.latitude);
    final lons = _items.map((e) => e.point.longitude);
    final sw = Point(latitude: lats.reduce((a,b)=>a<b?a:b), longitude: lons.reduce((a,b)=>a<b?a:b));
    final ne = Point(latitude: lats.reduce((a,b)=>a>b?a:b), longitude: lons.reduce((a,b)=>a>b?a:b));
    final c = await _controller.future;
    await c.moveCamera(
      CameraUpdate.newBounds(BoundingBox(southWest: sw, northEast: ne)),
      animation: const MapAnimation(type: MapAnimationType.smooth, duration: 0.6),
    );
  }

  Future<void> _onSelect(int index, {bool showSheet = false}) async {
    _unfocus(); // не даём клавиатуре всплывать
    _selectedIndex = index;
    _rebuildMapObjects();

    final c = await _controller.future;
    await c.moveCamera(
      CameraUpdate.newCameraPosition(
        CameraPosition(target: _items[index].point, zoom: 13),
      ),
      animation: const MapAnimation(type: MapAnimationType.smooth, duration: 0.4),
    );

    if (showSheet) _showDetails(_items[index]);
  }

  void _showDetails(_Place p) {
    _unfocus(); // и тут подстрахуемся
    showCupertinoModalPopup(
      context: context,
      builder: (_) => CupertinoActionSheet(
        title: Text(p.name, style: const TextStyle(color: Color(0xFF000000))),
        message: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 6),
            Text('Адрес:\n${p.address}', style: const TextStyle(color: Color(0xFF000000))),
            const SizedBox(height: 6),
            Text('Телефон:\n${p.tel}', style: const TextStyle(color: Color(0xFF000000))),
            const SizedBox(height: 6),
            Text(
              'Координаты: ${p.point.latitude.toStringAsFixed(6)}, ${p.point.longitude.toStringAsFixed(6)}',
              style: const TextStyle(color: Color(0xFF000000)),
            ),
          ],
        ),
        actions: [
          CupertinoActionSheetAction(
            onPressed: () => Navigator.pop(context),
            child: const Text('Закрыть'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return CupertinoPageScaffold(
      // явный светло-серый фон (чтобы не было белого на белом)
      backgroundColor: const Color(0xFFF2F2F7),
      navigationBar: const CupertinoNavigationBar(middle: Text('Lab6 — Яндекс.Карты')),
      child: SafeArea(
        child: GestureDetector( // тап по пустому месту — закрыть клаву
          behavior: HitTestBehavior.translucent,
          onTap: _unfocus,
          child: Column(
            children: [
              // Поле ввода URL + кнопка "Загрузить"
              Padding(
                padding: const EdgeInsets.fromLTRB(12, 8, 12, 6),
                child: Row(
                  children: [
                    Expanded(
                      child: CupertinoTextField(
                        controller: urlCtrl,
                        placeholder: 'Вставьте URL с JSON',
                        keyboardType: TextInputType.url,
                        autocorrect: false,
                        textInputAction: TextInputAction.done,
                        onSubmitted: (_) => _loadData(),   // Enter = загрузить
                        onTapOutside: (_) => _unfocus(),   // тап вне = скрыть клаву
                        // тоже зададим явный фон и чёрный текст
                        style: const TextStyle(color: Color(0xFF000000)),
                        decoration: BoxDecoration(
                          color: const Color(0xFFF2F2F7),
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: Color(0x33000000)),
                        ),
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                      ),
                    ),
                    const SizedBox(width: 8),
                    CupertinoButton.filled(
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                      onPressed: _loading ? null : () { _unfocus(); _loadData(); },
                      child: const Text('Загрузить'),
                    ),
                  ],
                ),
              ),

              // Карта
              Expanded(
                child: Stack(
                  children: [
                    YandexMap(
                      onMapCreated: (c) {
                        if (!_controller.isCompleted) _controller.complete(c);
                      },
                      onMapTap: (Point _) => _unfocus(),
                      mapObjects: _mapObjects,
                    ),
                    if (_loading)
                      const Align(
                        alignment: Alignment.topCenter,
                        child: Padding(
                          padding: EdgeInsets.all(12),
                          child: CupertinoActivityIndicator(),
                        ),
                      ),
                    if (_error != null)
                      Align(
                        alignment: Alignment.topCenter,
                        child: Container(
                          margin: const EdgeInsets.all(12),
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: const Color(0x26FF3B30), // красный с прозрачностью
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Text(
                            _error!,
                            style: const TextStyle(color: Color(0xFFFF3B30)),
                          ),
                        ),
                      ),
                  ],
                ),
              ),

              // Список объектов (явные контрасты и тени)
              SizedBox(
                height: 170,
                child: _items.isEmpty
                    ? const Center(child: Text('Нет данных', style: TextStyle(color: Color(0xFF000000))))
                    : ListView.separated(
                  padding: const EdgeInsets.fromLTRB(12, 8, 12, 12),
                  scrollDirection: Axis.horizontal,
                  itemCount: _items.length,
                  separatorBuilder: (_, __) => const SizedBox(width: 10),
                  itemBuilder: (_, i) {
                    final it = _items[i];
                    final sel = i == _selectedIndex;
                    return GestureDetector(
                      onTap: () => _onSelect(i, showSheet: true),
                      child: Container(
                        width: 280,
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: sel
                              ? const Color(0x1A007AFF) // синий с прозрачностью
                              : const Color(0xFFF7F7F7), // светло-серый фон карточки
                          borderRadius: BorderRadius.circular(14),
                          border: Border.all(
                            color: sel ? const Color(0xFF007AFF) : const Color(0x22000000),
                          ),
                          boxShadow: const [
                            BoxShadow(blurRadius: 6, offset: Offset(0, 2), color: Color(0x14000000)),
                          ],
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              it.name,
                              style: const TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.w600,
                                color: Color(0xFF000000), // чёрный текст
                              ),
                            ),
                            const SizedBox(height: 6),
                            Text(
                              it.address,
                              maxLines: 2,
                              overflow: TextOverflow.ellipsis,
                              style: const TextStyle(color: Color(0xFF000000)),
                            ),
                            const SizedBox(height: 6),
                            Text(it.tel, style: const TextStyle(color: Color(0xFF000000))),
                          ],
                        ),
                      ),
                    );
                  },
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
