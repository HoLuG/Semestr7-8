import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

void main() {
  runApp(const AoapApp());
}

class AoapApp extends StatelessWidget {
  const AoapApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'PyAndroidCompanion',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
        useMaterial3: true,
      ),
      home: const AoapHomePage(),
    );
  }
}

class AoapHomePage extends StatefulWidget {
  const AoapHomePage({super.key});

  @override
  State<AoapHomePage> createState() => _AoapHomePageState();
}

class _AoapHomePageState extends State<AoapHomePage> {
  static const MethodChannel _platform = MethodChannel('aoap_channel');

  String _status = 'Disconnected';
  final List<String> _messages = [];
  final TextEditingController _controller = TextEditingController();

  @override
  void initState() {
    super.initState();

    _platform.setMethodCallHandler((call) async {
      try {
        switch (call.method) {
          case 'onMessage':
            final String text = call.arguments as String;
            setState(() {
              _messages.add('PC: $text');
            });
            break;
          case 'onStatus':
            final String text = call.arguments as String;
            setState(() {
              _status = text;
            });
            break;
          default:
            break;
        }
      } catch (e, st) {
        debugPrint('MethodChannel error: $e\n$st');
      }
    });
  }


  Future<void> _connect() async {
    try {
      await _platform.invokeMethod('connect');
    } on PlatformException catch (e) {
      setState(() {
        _status = 'Error: ${e.message}';
      });
    }
  }

  Future<void> _send() async {
    final text = _controller.text.trim();
    if (text.isEmpty) return;

    try {
      await _platform.invokeMethod('send', {'text': text});
      setState(() {
        _messages.add('Me: $text');
        _controller.clear();
      });
    } on PlatformException catch (e) {
      setState(() {
        _status = 'Send error: ${e.message}';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('PyAndroidCompanion'),
      ),
      body: Column(
        children: [
          ListTile(
            title: const Text('Connection status'),
            subtitle: Text(_status),
            trailing: ElevatedButton(
              onPressed: _connect,
              child: const Text('Connect'),
            ),
          ),
          const Divider(),
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.all(8),
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                return Text(_messages[index]);
              },
            ),
          ),
          const Divider(),
          Padding(
            padding: const EdgeInsets.all(8.0),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _controller,
                    decoration: const InputDecoration(
                      labelText: 'Message to PC',
                    ),
                    onSubmitted: (_) => _send(),
                  ),
                ),
                const SizedBox(width: 8),
                ElevatedButton(
                  onPressed: _send,
                  child: const Text('Send'),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
