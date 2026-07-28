import 'package:flutter/material.dart';
import 'package:flutter_cube/flutter_cube.dart';

void main() => runApp(const MyApp());

class MyApp extends StatelessWidget {
  const MyApp({super.key});
  @override
  Widget build(BuildContext context) {
    return const MaterialApp(
      home: TrepDemo(),
      debugShowCheckedModeBanner: false,
      title: 'Трепанация Черепа',
    );
  }
}

class TrepDemo extends StatefulWidget {
  const TrepDemo({super.key});
  @override
  State<TrepDemo> createState() => _TrepDemoState();
}

class _TrepDemoState extends State<TrepDemo> {
  late Scene _scene;
  Object? skullBase;
  Object? skullLid;

  double lift = 0.0;
  bool _isSceneReady = false;

  static const double maxLiftHeight = 1.0;
  static const double maxRotation = 0.3;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Трепанация Черепа'),
        backgroundColor: Colors.blueGrey.shade800,
      ),
      body: Column(
        children: [
          Expanded(
            child: Cube(
              onSceneCreated: (Scene scene) {
                _scene = scene;
                _scene.camera.position.setValues(0, 0, 8);
                _scene.camera.zoom = 12;

                final sceneObject = Object(
                  fileName: 'assets/trepanation/My_skull.obj',
                  isAsset: true,
                );

                _scene.world.add(sceneObject);

                Future.delayed(const Duration(milliseconds: 1000), () {
                  _findAndSetupObjects(sceneObject);
                });
              },
            ),
          ),
          Container(
            padding: const EdgeInsets.all(16),
            color: Colors.blueGrey.shade50,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const Text(
                  'Открытие черепа:',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 10),
                Slider(
                  value: lift,
                  min: 0,
                  max: 1,
                  divisions: 100,
                  activeColor: Colors.red.shade700,
                  inactiveColor: Colors.red.shade200,
                  onChanged: _isSceneReady ? (value) {
                    setState(() {
                      lift = value;
                      _applyLift();
                    });
                  } : null,
                ),
                const SizedBox(height: 10),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      _isSceneReady
                          ? 'Открытие: ${(lift * 100).round()}%'
                          : 'Загрузка...',
                      style: const TextStyle(fontWeight: FontWeight.w500),
                    ),
                    ElevatedButton.icon(
                      onPressed: _isSceneReady ? () {
                        setState(() {
                          lift = 0;
                          _applyLift();
                        });
                      } : null,
                      icon: const Icon(Icons.refresh, size: 20),
                      label: const Text('Сбросить'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.blueGrey.shade600,
                        foregroundColor: Colors.white,
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  void _findAndSetupObjects(Object sceneObject) {
    for (var child in sceneObject.children) {
      print('Found object: ${child.name}');

      if (child.name?.toLowerCase().contains('base') == true ||
          child.name?.toLowerCase().contains('skull_base') == true) {
        skullBase = child;
        print('Found skull base: ${child.name}');
      } else if (child.name?.toLowerCase().contains('lid') == true ||
          child.name?.toLowerCase().contains('skull_lid') == true) {
        skullLid = child;
        print('Found skull lid: ${child.name}');
      }
    }

    if (skullBase == null && sceneObject.children.length >= 2) {
      skullBase = sceneObject.children[0];
      skullLid = sceneObject.children[1];
      print('Using first two objects: ${skullBase!.name} and ${skullLid!.name}');
    }

    setState(() {
      _isSceneReady = skullBase != null && skullLid != null;
    });

    if (_isSceneReady) {
      print('Successfully loaded both objects!');
      sceneObject.position.setValues(0.0, -1.0, 0.0);
      sceneObject.updateTransform();
      _applyLift();
    } else {
      print('Failed to find both objects. Available: ${sceneObject.children.map((e) => e.name)}');
    }
  }

  void _applyLift() {
    if (skullLid == null || !_isSceneReady) return;

    final liftHeight = lift * maxLiftHeight;
    final rotationAngle = lift * maxRotation;

    skullLid!.position.setValues(0.0, liftHeight, 0.0);
    skullLid!.rotation.setValues(rotationAngle, 0.0, 0.0);

    skullLid!.updateTransform();

    print('Lid position: Y=${skullLid!.position.y}');
  }
}