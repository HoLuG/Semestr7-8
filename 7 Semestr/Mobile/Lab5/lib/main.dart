import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'WS Dot Product',
      theme: ThemeData(
        colorSchemeSeed: Colors.blue,
        useMaterial3: true,
      ),
      home: const HomePage(),
    );
  }
}

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => HomePageState();
}

class HomePageState extends State<HomePage> {
  static const String wsUrl = 'ws://10.217.159.169:8090/';

  WebSocketChannel? channel;
  StreamSubscription? sub;
  Timer? reconnectTimer;

  int retryAttempt = 0;
  final int maxBackoffSeconds = 30;

  String status = 'Connecting…';

  int n = 3;
  final List<TextEditingController> aCtrls = [];
  final List<TextEditingController> bCtrls = [];

  String resultText = '';
  double? resultValue;

  @override
  void initState() {
    super.initState();
    _setDimension(n);
    connect();
  }

  @override
  void dispose() {
    sub?.cancel();
    channel?.sink.close();
    reconnectTimer?.cancel();
    _disposeCtrls(aCtrls);
    _disposeCtrls(bCtrls);
    super.dispose();
  }

  void _disposeCtrls(List<TextEditingController> ctrls) {
    for (final c in ctrls) {
      c.dispose();
    }
  }

  void _setDimension(int dim) {
    dim = dim.clamp(1, 100);
    while (aCtrls.length < dim) {
      aCtrls.add(TextEditingController(text: '0'));
    }
    while (bCtrls.length < dim) {
      bCtrls.add(TextEditingController(text: '0'));
    }
    while (aCtrls.length > dim) {
      aCtrls.removeLast().dispose();
    }
    while (bCtrls.length > dim) {
      bCtrls.removeLast().dispose();
    }
    setState(() => n = dim);
  }

  void connect() {
    reconnectTimer?.cancel();
    sub?.cancel();
    channel?.sink.close();

    setState(() => status = 'Connecting…');

    try {
      channel = WebSocketChannel.connect(Uri.parse(wsUrl));
      sub = channel!.stream.listen(
            (data) {
          final msg = parseMessage(data);
          switch (msg['type']) {
            case 'pong':
              setState(() => status = 'Connected');
              break;
            case 'dot_result':
              setState(() {
                final res = (msg['result'] as num).toDouble();
                resultValue = res;
                resultText = 'A·B = $res';
                status = 'Connected';
              });
              break;
            case 'error':
              setState(() => status = 'Error: ${msg['message']}');
              break;
            default:
              setState(() => status = 'Unknown message');
          }
        },
        onDone: () => scheduleReconnect('Disconnected'),
        onError: (err) => scheduleReconnect('Error: $err'),
      );

      send({'type': 'ping'});

      retryAttempt = 0;
    } catch (e) {
      scheduleReconnect('Error: $e');
    }
  }

  void scheduleReconnect(String newStatus) {
    setState(() => status = newStatus);
    retryAttempt++;
    final seconds = (1 << (retryAttempt - 1));
    final delay =
    Duration(seconds: seconds > maxBackoffSeconds ? maxBackoffSeconds : seconds);
    reconnectTimer?.cancel();
    reconnectTimer = Timer(delay, () {
      if (!mounted) return;
      connect();
    });
  }

  Map<String, dynamic> parseMessage(dynamic data) {
    if (data is String) {
      return json.decode(data) as Map<String, dynamic>;
    } else if (data is List<int>) {
      return json.decode(utf8.decode(data)) as Map<String, dynamic>;
    } else {
      return {'type': 'error', 'message': 'Unsupported format'};
    }
  }

  double _parseNum(String s) {
    final t = s.trim().replaceAll(',', '.');
    return double.tryParse(t) ?? 0.0;
  }

  List<double> _readVector(List<TextEditingController> ctrls) {
    return ctrls.map((c) => _parseNum(c.text)).toList(growable: false);
  }

  void send(Map<String, dynamic> msg) {
    final ch = channel;
    if (ch == null) return;
    try {
      ch.sink.add(json.encode(msg));
    } catch (_) {
      scheduleReconnect('Disconnected');
    }
  }

  void computeDot() {
    final a = _readVector(aCtrls);
    final b = _readVector(bCtrls);
    if (a.length != b.length || a.isEmpty) {
      setState(() => resultText = 'Ошибка: длины должны совпадать и быть > 0');
      return;
    }
    send({'type': 'dot', 'a': a, 'b': b});
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('WS Dot Product'),
        actions: [
          IconButton(
            onPressed: connect,
            icon: const Icon(Icons.refresh),
            tooltip: 'Reconnect now',
          ),
        ],
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text('Status: $status'),
              const SizedBox(height: 12),
              Row(
                children: [
                  const Text('Dimension n:'),
                  const SizedBox(width: 8),
                  IconButton(
                    onPressed: () => _setDimension(n - 1),
                    icon: const Icon(Icons.remove),
                  ),
                  Text('$n', style: Theme.of(context).textTheme.titleMedium),
                  IconButton(
                    onPressed: () => _setDimension(n + 1),
                    icon: const Icon(Icons.add),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Expanded(
                child: ListView.separated(
                  itemCount: n,
                  separatorBuilder: (_, __) => const SizedBox(height: 8),
                  itemBuilder: (context, i) {
                    return Row(
                      children: [
                        SizedBox(
                          width: 28,
                          child: Center(
                            child: Text('${i + 1}',
                                style: Theme.of(context).textTheme.bodySmall),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: TextField(
                            controller: aCtrls[i],
                            decoration: const InputDecoration(
                              labelText: 'A[i]',
                              border: OutlineInputBorder(),
                            ),
                            keyboardType: const TextInputType.numberWithOptions(
                                decimal: true, signed: true),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: TextField(
                            controller: bCtrls[i],
                            decoration: const InputDecoration(
                              labelText: 'B[i]',
                              border: OutlineInputBorder(),
                            ),
                            keyboardType: const TextInputType.numberWithOptions(
                                decimal: true, signed: true),
                          ),
                        ),
                      ],
                    );
                  },
                ),
              ),
              const SizedBox(height: 12),
              FilledButton(
                onPressed: computeDot,
                child: const Text('Compute A·B'),
              ),
              const SizedBox(height: 12),
              Text(
                resultText.isEmpty ? 'A·B will appear here' : resultText,
                style: Theme.of(context).textTheme.titleLarge,
              ),
              const SizedBox(height: 12),
              if (resultValue != null)
                Container(
                  height: 20,
                  decoration: BoxDecoration(
                    color: resultValue! > 0
                        ? Colors.blue
                        : (resultValue! < 0 ? Colors.red : Colors.grey),
                    borderRadius: BorderRadius.circular(4),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}
