import 'package:ditredi/ditredi.dart';
import 'package:flutter/material.dart';
import 'package:vector_math/vector_math_64.dart' as vector;
import 'dart:math';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatefulWidget {
  const MyApp({Key? key}) : super(key: key);

  @override
  State<MyApp> createState() => _MyAppState();
}

class _MyAppState extends State<MyApp> {
  var leftHandZ = -5.0;
  var rightHandZ = 5.0;
  var handY = 0.0;

  var leftHandRotation = 0.0;
  var rightHandRotation = 0.0;

  final double leftHandX = -25.0;
  final double rightHandX = 25.0;

  var ironX = 0.0;
  var ironY = 0.0;
  var ironZ = 0.0;

  var ironSpeedX = 0.0;
  var ironSpeedY = 0.0;
  var ironSpeedZ = 0.0;

  bool gameStarted = false;
  bool gamePaused = false;
  int leftScore = 0;
  int rightScore = 0;

  final double ironSpeed = 0.8;
  final double ballRadius = 3.0;
  final double handRadius = 6.0;
  final double tableWidth = 60.0;
  final double tableHeight = 20.0;

  final Future<List<Mesh3D>> handMeshes = _generateHandPoints();
  final Future<Mesh3D> ironMesh = _generateIronPoints();

  final _controller = DiTreDiController(
    rotationX: -30,
    rotationY: 30,
    light: vector.Vector3(-0.5, -0.5, 0.5),
  );

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _controller.update(userScale: 1.0);
    });
  }

  void _startGame() {
    setState(() {
      gameStarted = true;
      gamePaused = false;
      leftScore = 0;
      rightScore = 0;
      Random random = Random();
      double angle = random.nextDouble() * 2 * pi;
      ironSpeedX = cos(angle) * ironSpeed;
      ironSpeedY = 0.0;
      ironSpeedZ = 0.0;
      ironX = 0.0;
      ironY = 0.0;
      ironZ = 0.0;
    });
    _gameLoop();
  }

  void _gameLoop() {
    Future.delayed(const Duration(milliseconds: 16), () {
      if (gameStarted && !gamePaused) {
        _updateGame();
        _gameLoop();
      }
    });
  }

  void _updateGame() {
    setState(() {
      ironX += ironSpeedX;
      ironZ += ironSpeedZ;
      ironY = 0.0;

      if (_checkSphereHandCollision(ironX, ironY, ironZ, leftHandX, handY, leftHandZ)) {
        _handleHandBounce(leftHandRotation, isLeft: true);
      }

      if (_checkSphereHandCollision(ironX, ironY, ironZ, rightHandX, handY, rightHandZ)) {
        _handleHandBounce(rightHandRotation, isLeft: false);
      }

      if (ironX < -tableWidth / 2) {
        rightScore++;
        _resetIron();
      } else if (ironX > tableWidth / 2) {
        leftScore++;
        _resetIron();
      }
    });
  }

  void _handleHandBounce(double handRotation, {required bool isLeft}) {
    double currentSpeed = sqrt(ironSpeedX * ironSpeedX + ironSpeedZ * ironSpeedZ);
    if (currentSpeed < ironSpeed) currentSpeed = ironSpeed;

    double baseSpeedX = -ironSpeedX;

    double angleEffect = handRotation.clamp(-1.0, 1.0);

    double newSpeedX = baseSpeedX.sign * currentSpeed * cos(angleEffect * pi/4);
    double newSpeedZ = currentSpeed * sin(angleEffect * pi/4);

    ironSpeedX = newSpeedX;
    ironSpeedZ = newSpeedZ;

    if (isLeft) {
      ironX = leftHandX + handRadius + ballRadius + 1.0;
    } else {
      ironX = rightHandX - handRadius - ballRadius - 1.0;
    }
  }

  void _resetIron() {
    setState(() {
      ironX = 0.0;
      ironY = 0.0;
      ironZ = 0.0;
      Random random = Random();
      ironSpeedX = (random.nextBool() ? 1 : -1) * ironSpeed;
      ironSpeedZ = 0.0;
    });
  }

  bool _checkSphereHandCollision(double bx, double by, double bz,
      double hx, double hy, double hz) {
    final dx = bx - hx;
    final dy = by - hy;
    final dz = bz - hz;
    final dist2 = dx * dx + dy * dy + dz * dz;
    final r = (ballRadius + handRadius);
    return dist2 <= r * r;
  }

  void _pauseGame() {
    setState(() {
      gamePaused = !gamePaused;
      if (!gamePaused) _gameLoop();
    });
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      darkTheme: ThemeData.dark(),
      title: 'Iron Pong — Z-axis movement',
      theme: ThemeData(primarySwatch: Colors.blue),
      home: Scaffold(
        body: SafeArea(
          child: Column(
            children: [
              Container(
                padding: const EdgeInsets.all(12),
                color: Colors.blueGrey[800],
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceAround,
                  children: [
                    Text('ЛЕВО: $leftScore',
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18, color: Colors.white)),
                    Column(
                      children: [
                        if (!gameStarted)
                          ElevatedButton(onPressed: _startGame, child: const Text('START GAME'))
                        else
                          ElevatedButton(onPressed: _pauseGame, child: Text(gamePaused ? 'RESUME' : 'PAUSE')),
                        Text(gameStarted ? (gamePaused ? 'ПАУЗА' : 'ИГРА') : 'ГОТОВ К ИГРЕ',
                            style: const TextStyle(color: Colors.white, fontSize: 12)),
                      ],
                    ),
                    Text('ПРАВО: $rightScore',
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18, color: Colors.white)),
                  ],
                ),
              ),

              Expanded(
                child: FutureBuilder(
                  future: Future.wait([handMeshes, ironMesh]),
                  builder: (BuildContext context, AsyncSnapshot<List<dynamic>> snapshot) {
                    if (snapshot.hasData) {
                      List<Mesh3D> handData = snapshot.data![0];
                      Mesh3D ironData = snapshot.data![1];

                      return DiTreDiDraggable(
                        controller: _controller,
                        child: DiTreDi(
                          figures: [
                            TransformModifier3D(
                              handData[0],
                              Matrix4.identity()
                                ..translate(leftHandX, handY, leftHandZ)
                                ..scale(1.5, 1.5, 1.5)
                                ..rotateX(-pi / 2)
                                ..rotateZ(leftHandRotation),
                            ),

                            TransformModifier3D(
                              handData[1],
                              Matrix4.identity()
                                ..translate(leftHandX, handY, leftHandZ)
                                ..scale(1.5, 1.5, 1.5)
                                ..rotateX(-pi / 2)
                                ..rotateZ(leftHandRotation)
                                ..translate(3.05, 1.15, 8.75)
                                ..translate(-0.2, -0.25, -2.2)
                                ..translate(0.2, 0.25, 2.2),
                            ),

                            TransformModifier3D(
                              handData[2],
                              Matrix4.identity()
                                ..translate(leftHandX, handY, leftHandZ)
                                ..scale(1.5, 1.5, 1.5)
                                ..rotateX(-pi / 2)
                                ..rotateZ(leftHandRotation)
                                ..translate(0.7, 0.0, 9.75)
                                ..translate(0.0, -0.5, -2.25)
                                ..translate(0.0, 0.5, 2.25),
                            ),

                            TransformModifier3D(
                              handData[3],
                              Matrix4.identity()
                                ..translate(leftHandX, handY, leftHandZ)
                                ..scale(1.5, 1.5, 1.5)
                                ..rotateX(-pi / 2)
                                ..rotateZ(leftHandRotation)
                                ..translate(-2.0, -0.56, 9.1)
                                ..translate(0.0, -0.25, -2.2)
                                ..translate(0.0, 0.25, 2.2),
                            ),

                            TransformModifier3D(
                              handData[4],
                              Matrix4.identity()
                                ..translate(leftHandX, handY, leftHandZ)
                                ..scale(1.5, 1.5, 1.5)
                                ..rotateX(-pi / 2)
                                ..rotateZ(leftHandRotation)
                                ..translate(-4.65, -1.0, 7.15)
                                ..translate(0.0, 0.0, -1.25)
                                ..translate(0.0, 0.0, 1.25),
                            ),

                            TransformModifier3D(
                              handData[0],
                              Matrix4.identity()
                                ..translate(rightHandX, handY, rightHandZ)
                                ..scale(-1.5, 1.5, 1.5)
                                ..rotateX(-pi / 2)
                                ..rotateZ(rightHandRotation),
                            ),

                            TransformModifier3D(
                              handData[1],
                              Matrix4.identity()
                                ..translate(rightHandX, handY, rightHandZ)
                                ..scale(-1.5, 1.5, 1.5)
                                ..rotateX(-pi / 2)
                                ..rotateZ(rightHandRotation)
                                ..translate(3.05, 1.15, 8.75)
                                ..translate(-0.2, -0.25, -2.2)
                                ..translate(0.2, 0.25, 2.2),
                            ),

                            TransformModifier3D(
                              handData[2],
                              Matrix4.identity()
                                ..translate(rightHandX, handY, rightHandZ)
                                ..scale(-1.5, 1.5, 1.5)
                                ..rotateX(-pi / 2)
                                ..rotateZ(rightHandRotation)
                                ..translate(0.7, 0.0, 9.75)
                                ..translate(0.0, -0.5, -2.25)
                                ..translate(0.0, 0.5, 2.25),
                            ),

                            TransformModifier3D(
                              handData[3],
                              Matrix4.identity()
                                ..translate(rightHandX, handY, rightHandZ)
                                ..scale(-1.5, 1.5, 1.5)
                                ..rotateX(-pi / 2)
                                ..rotateZ(rightHandRotation)
                                ..translate(-2.0, -0.56, 9.1)
                                ..translate(0.0, -0.25, -2.2)
                                ..translate(0.0, 0.25, 2.2),
                            ),

                            TransformModifier3D(
                              handData[4],
                              Matrix4.identity()
                                ..translate(rightHandX, handY, rightHandZ)
                                ..scale(-1.5, 1.5, 1.5)
                                ..rotateX(-pi / 2)
                                ..rotateZ(rightHandRotation)
                                ..translate(-4.65, -1.0, 7.15)
                                ..translate(0.0, 0.0, -1.25)
                                ..translate(0.0, 0.0, 1.25),
                            ),

                            TransformModifier3D(
                              ironData,
                              Matrix4.identity()
                                ..translate(ironX, ironY, ironZ)
                                ..scale(3.0, 3.0, 3.0)
                                ..rotateX(-pi / 2),
                            ),
                          ],
                          controller: _controller,
                        ),
                      );
                    } else {
                      return Center(
                        child: Column(mainAxisAlignment: MainAxisAlignment.center, children: const [
                          CircularProgressIndicator(),
                          SizedBox(height: 16),
                          Text("Загрузка 3D моделей..."),
                        ]),
                      );
                    }
                  },
                ),
              ),

              const Padding(padding: EdgeInsets.all(8.0), child: Text("Drag to rotate. Scroll to zoom")),

              Container(
                height: 250,
                child: SingleChildScrollView(
                  child: Column(
                    children: [
                      const Padding(
                        padding: EdgeInsets.all(8.0),
                        child: Text('Левая ракетка:', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                      ),
                      _buildPositionSlider('Позиция Z', leftHandZ, -10, 10, (v) => setState(() => leftHandZ = v)),
                      _buildRotationSlider('Поворот', leftHandRotation, -pi, pi, (v) => setState(() => leftHandRotation = v)),

                      const Padding(
                        padding: EdgeInsets.all(8.0),
                        child: Text('Правая ракетка:', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                      ),
                      _buildPositionSlider('Позиция Z', rightHandZ, -10, 10, (v) => setState(() => rightHandZ = v)),
                      _buildRotationSlider('Поворот', rightHandRotation, -pi, pi, (v) => setState(() => rightHandRotation = v)),


                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildPositionSlider(String label, double value, double min, double max, ValueChanged<double> onChanged) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4, horizontal: 16),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text('$label: ${value.toStringAsFixed(1)}'),
        Slider(value: value, min: min, max: max, divisions: 50, onChanged: onChanged),
      ]),
    );
  }

  Widget _buildRotationSlider(String label, double value, double min, double max, ValueChanged<double> onChanged) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4, horizontal: 16),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text('$label: ${(value * 180 / pi).toStringAsFixed(0)}°'),
        Slider(value: value, min: min, max: max, divisions: 72, onChanged: onChanged),
      ]),
    );
  }
}

Future<List<Mesh3D>> _generateHandPoints() async {
  try {
    return [
      Mesh3D(await ObjParser().loadFromResources("assets/hand/hand.obj")),
      Mesh3D(await ObjParser().loadFromResources("assets/hand/index.obj")),
      Mesh3D(await ObjParser().loadFromResources("assets/hand/middle.obj")),
      Mesh3D(await ObjParser().loadFromResources("assets/hand/ring.obj")),
      Mesh3D(await ObjParser().loadFromResources("assets/hand/pinky.obj")),
    ];
  } catch (e) {
    print("Error loading hand models: $e");
    return [Mesh3D([]), Mesh3D([]), Mesh3D([]), Mesh3D([]), Mesh3D([])];
  }
}

Future<Mesh3D> _generateIronPoints() async {
  try {
    final sceneObject = await ObjParser().loadFromResources("assets/iron/iron.obj");
    return Mesh3D(sceneObject);
  } catch (e) {
    print("Error loading iron: $e");
    return Mesh3D([]);
  }
}