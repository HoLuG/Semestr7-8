import 'package:flutter/material.dart';
import 'package:ditredi/ditredi.dart';
import 'package:vector_math/vector_math_64.dart' hide Colors;
import 'dart:math';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Gradient Descent 3D',
      theme: ThemeData(
        primarySwatch: Colors.indigo,
        scaffoldBackgroundColor: const Color(0xFF0D1117),
        sliderTheme: const SliderThemeData(
          thumbColor: Colors.cyan,
          activeTrackColor: Colors.cyan,
          inactiveTrackColor: Color(0xFF21262D),
          overlayColor: Colors.cyanAccent,
        ),
        elevatedButtonTheme: ElevatedButtonThemeData(
          style: ElevatedButton.styleFrom(
            backgroundColor: Colors.indigo,
            foregroundColor: Colors.white,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(20),
            ),
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
          ),
        ),
        outlinedButtonTheme: OutlinedButtonThemeData(
          style: OutlinedButton.styleFrom(
            foregroundColor: Colors.cyan,
            side: BorderSide(color: Colors.cyan.withOpacity(0.5)),
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(20),
            ),
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
          ),
        ),
      ),
      home: const GradientDescentApp(),
    );
  }
}

class GradientDescentApp extends StatefulWidget {
  const GradientDescentApp({super.key});

  @override
  State<GradientDescentApp> createState() => _GradientDescentAppState();
}

class _GradientDescentAppState extends State<GradientDescentApp> {
  final double a1 = -400.0, b1 = 400.0, a2 = -400.0, b2 = 400.0;
  double h = 15.0;
  List<Point3D> points = [];
  List<Point3D> path = [];
  List<Point3D> xyProjection = [];
  Vector3? startPoint;
  bool isDescending = false;
  final modelController = DiTreDiController();

  @override
  void initState() {
    super.initState();
    generateSurface();
  }

  double function(double x, double y) {
    return 418.9829 * 2 - (x * sin(sqrt(x.abs())) + y * sin(sqrt(y.abs())));
  }

  void generateSurface() {
    points.clear();
    for (double x = a1; x <= b1; x += h) {
      for (double y = a2; y <= b2; y += h) {
        points.add(Point3D(
          Vector3(x, y, function(x, y)),
          color: const Color(0xFF1F6FEB).withOpacity(0.6),
          width: 3.0,
        ));
      }
    }
  }

  void findMinimum(Vector3 start) {
    setState(() {
      path = [Point3D(Vector3(start.x, start.y, function(start.x, start.y)),
          color: Colors.limeAccent, width: 10.0)];
      xyProjection = [Point3D(Vector3(start.x, start.y, 0),
          color: Colors.limeAccent.withAlpha(100), width: 8.0)];
      isDescending = true;
    });

    Future<void> step() async {
      while (true) {
        final current = path.last.position;
        final neighbors = [
          Vector3(current.x + h, current.y, function(current.x + h, current.y)),
          Vector3(current.x - h, current.y, function(current.x - h, current.y)),
          Vector3(current.x, current.y + h, function(current.x, current.y + h)),
          Vector3(current.x, current.y - h, function(current.x, current.y - h)),
        ].where((p) => p.x >= a1 && p.x <= b1 && p.y >= a2 && p.y <= b2).toList();

        final currentValue = function(current.x, current.y);
        Vector3? nextPoint;
        double minValue = currentValue;

        for (var neighbor in neighbors) {
          final value = function(neighbor.x, neighbor.y);
          if (value < minValue) {
            minValue = value;
            nextPoint = neighbor;
          }
        }

        if (nextPoint == null) {
          setState(() {
            path.last = Point3D(Vector3(current.x, current.y, current.z),
                color: Colors.greenAccent, width: 12.0);
            xyProjection.last = Point3D(Vector3(current.x, current.y, 0),
                color: Colors.greenAccent.withAlpha(120), width: 8.0);
            isDescending = false;
          });
          break;
        }

        setState(() {
          path.add(Point3D(Vector3(nextPoint!.x, nextPoint.y, function(nextPoint.x, nextPoint.y)),
              color: Colors.amber, width: 10.0));
          xyProjection.add(Point3D(Vector3(nextPoint.x, nextPoint.y, 0),
              color: Colors.amber.withAlpha(100), width: 8.0));
        });

        await Future.delayed(const Duration(milliseconds: 300));
      }
    }

    step();
  }

  void updateStepSize(double newValue) {
    setState(() {
      h = newValue;
      generateSurface();
      path.clear();
      xyProjection.clear();
      isDescending = false;
    });
  }

  void resetAll() {
    setState(() {
      path.clear();
      xyProjection.clear();
      startPoint = null;
      isDescending = false;
      generateSurface();
    });
  }

  List<Line3D> get axes {
    return [
      Line3D(Vector3(a1, 0, 0), Vector3(b1, 0, 0), color: Colors.redAccent, width: 4),
      Line3D(Vector3(0, a2, 0), Vector3(0, b2, 0), color: Colors.greenAccent, width: 4),
      Line3D(Vector3(0, 0, -200), Vector3(0, 0, 800), color: Colors.blueAccent, width: 4),
    ];
  }

  List<Line3D> get grid {
    List<Line3D> gridLines = [];
    final gridColor = const Color(0xFF30363D).withAlpha(100);

    for (double y = a2; y <= b2; y += 40) {
      gridLines.add(Line3D(
        Vector3(a1, y, 0),
        Vector3(b1, y, 0),
        color: gridColor,
        width: 1.5,
      ));
    }

    for (double x = a1; x <= b1; x += 40) {
      gridLines.add(Line3D(
        Vector3(x, a2, 0),
        Vector3(x, b2, 0),
        color: gridColor,
        width: 1.5,
      ));
    }

    return gridLines;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Метод наискорейшего спуска',
          style: TextStyle(
            fontWeight: FontWeight.bold,
            fontSize: 18,
          ),
        ),
        centerTitle: true,
        backgroundColor: const Color(0xFF161B22),
        elevation: 0,
        flexibleSpace: Container(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              colors: [Colors.indigo.shade900, Colors.indigo.shade700],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
          ),
        ),
      ),
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [Color(0xFF0D1117), Color(0xFF161B22), Color(0xFF21262D)],
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
          ),
        ),
        child: Column(
          children: [
            Expanded(
              child: DiTreDiDraggable(
                controller: modelController,
                child: DiTreDi(
                  figures: [
                    ...axes,
                    ...grid,
                    ...points,
                    ...path,
                    ...xyProjection,
                  ],
                  controller: modelController,
                  config: const DiTreDiConfig(supportZIndex: false),
                ),
              ),
            ),
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: const Color(0xFF21262D).withOpacity(0.9),
                borderRadius: const BorderRadius.only(
                  topLeft: Radius.circular(24),
                  topRight: Radius.circular(24),
                ),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.3),
                    blurRadius: 20,
                    offset: const Offset(0, -5),
                  ),
                ],
              ),
              child: Column(
                children: [
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: const Color(0xFF30363D),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(color: Colors.cyan.withOpacity(0.2)),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            const Text(
                              'Размер шага',
                              style: TextStyle(
                                color: Colors.white,
                                fontSize: 16,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                              decoration: BoxDecoration(
                                color: Colors.cyan.withOpacity(0.2),
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: Text(
                                h.toStringAsFixed(0),
                                style: const TextStyle(
                                  color: Colors.cyan,
                                  fontWeight: FontWeight.bold,
                                  fontSize: 14,
                                ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),
                        Slider(
                          value: h,
                          min: 5.0,
                          max: 40.0,
                          divisions: 35,
                          onChanged: isDescending ? null : updateStepSize,
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 20),

                  Row(
                    children: [
                      Expanded(
                        child: Container(
                          padding: const EdgeInsets.all(16),
                          decoration: BoxDecoration(
                            color: const Color(0xFF30363D),
                            borderRadius: BorderRadius.circular(16),
                            border: Border.all(color: Colors.indigo.withOpacity(0.3)),
                          ),
                          child: Column(
                            children: [
                              TextField(
                                style: const TextStyle(color: Colors.white),
                                decoration: InputDecoration(
                                  labelText: 'X',
                                  labelStyle: TextStyle(color: Colors.grey.shade400),
                                  filled: true,
                                  fillColor: const Color(0xFF1F2937),
                                  border: OutlineInputBorder(
                                    borderRadius: BorderRadius.circular(12),
                                    borderSide: BorderSide(color: Colors.indigo.withOpacity(0.5)),
                                  ),
                                  enabledBorder: OutlineInputBorder(
                                    borderRadius: BorderRadius.circular(12),
                                    borderSide: BorderSide(color: Colors.indigo.withOpacity(0.3)),
                                  ),
                                ),
                                keyboardType: TextInputType.number,
                                onChanged: (value) {
                                  if (value.isNotEmpty) {
                                    final x = double.tryParse(value) ?? 0.0;
                                    setState(() {
                                      startPoint = Vector3(x, startPoint?.y ?? 0.0,
                                          function(x, startPoint?.y ?? 0.0));
                                    });
                                  }
                                },
                              ),
                              const SizedBox(height: 12),
                              TextField(
                                style: const TextStyle(color: Colors.white),
                                decoration: InputDecoration(
                                  labelText: 'Y',
                                  labelStyle: TextStyle(color: Colors.grey.shade400),
                                  filled: true,
                                  fillColor: const Color(0xFF1F2937),
                                  border: OutlineInputBorder(
                                    borderRadius: BorderRadius.circular(12),
                                    borderSide: BorderSide(color: Colors.indigo.withOpacity(0.5)),
                                  ),
                                  enabledBorder: OutlineInputBorder(
                                    borderRadius: BorderRadius.circular(12),
                                    borderSide: BorderSide(color: Colors.indigo.withOpacity(0.3)),
                                  ),
                                ),
                                keyboardType: TextInputType.number,
                                onChanged: (value) {
                                  if (value.isNotEmpty) {
                                    final y = double.tryParse(value) ?? 0.0;
                                    setState(() {
                                      startPoint = Vector3(startPoint?.x ?? 0.0, y,
                                          function(startPoint?.x ?? 0.0, y));
                                    });
                                  }
                                },
                              ),
                            ],
                          ),
                        ),
                      ),
                      const SizedBox(width: 16),
                      Column(
                        children: [
                          ElevatedButton(
                            onPressed: startPoint != null && !isDescending
                                ? () => findMinimum(startPoint!)
                                : null,
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Colors.cyan,
                              foregroundColor: Colors.black,
                            ),
                            child: const Text('▶️ Старт'),
                          ),
                          const SizedBox(height: 12),
                          OutlinedButton(
                            onPressed: isDescending ? resetAll : null,
                            style: OutlinedButton.styleFrom(
                              backgroundColor: Colors.red.shade900,
                              foregroundColor: Colors.redAccent,
                            ),
                            child: const Text('🔄 Сброс'),
                          ),
                        ],
                      ),
                    ],
                  ),

                  // Статус
                  if (isDescending) ...[
                    const SizedBox(height: 16),
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Colors.amber.withOpacity(0.2),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: Colors.amber.withOpacity(0.5)),
                      ),
                      child: Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.all(8),
                            decoration: const BoxDecoration(
                              color: Colors.amber,
                              shape: BoxShape.circle,
                            ),
                            child: const Icon(Icons.play_arrow,
                                color: Colors.black, size: 16),
                          ),
                          const SizedBox(width: 12),
                          const Text(
                            'Поиск минимума...',
                            style: TextStyle(
                              color: Colors.amber,
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}