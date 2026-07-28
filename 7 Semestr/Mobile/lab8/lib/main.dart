import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:dartssh2/dartssh2.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Simple SSH Client',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF1E88E5),
          brightness: Brightness.dark,
        ),
        scaffoldBackgroundColor: const Color(0xFF0F172A),
        appBarTheme: const AppBarTheme(
          centerTitle: true,
          elevation: 0,
          backgroundColor: Colors.transparent,
        ),
        inputDecorationTheme: const InputDecorationTheme(
          filled: true,
          fillColor: Color(0xFF111827),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.all(Radius.circular(12)),
          ),
        ),
      ),
      home: const SshPage(),
    );
  }
}

class SshPage extends StatefulWidget {
  const SshPage({super.key});

  @override
  State<SshPage> createState() => _SshPageState();
}

class _SshPageState extends State<SshPage> {
  static const String _defaultHost = '185.102.139.168';
  static const int _port = 22;
  static const String _defaultUsername = 'root';
  static const String _defaultPassword = 'gOsQ5p7FUJ9w';

  late final TextEditingController _hostController;
  late final TextEditingController _usernameController;
  late final TextEditingController _passwordController;

  final TextEditingController _commandController =
  TextEditingController(text: 'uname -a');

  String _output = '';
  bool _isRunning = false;

  @override
  void initState() {
    super.initState();
    _hostController = TextEditingController(text: _defaultHost);
    _usernameController = TextEditingController(text: _defaultUsername);
    _passwordController = TextEditingController(text: _defaultPassword);
  }

  @override
  void dispose() {
    _hostController.dispose();
    _usernameController.dispose();
    _passwordController.dispose();
    _commandController.dispose();
    super.dispose();
  }

  Future<void> _runCommand() async {
    final host = _hostController.text.trim();
    final username = _usernameController.text.trim();
    final password = _passwordController.text;

    final command = _commandController.text.trim();

    if (host.isEmpty || username.isEmpty || password.isEmpty) {
      setState(() {
        _output = 'Please enter host, username and password.';
      });
      return;
    }

    if (command.isEmpty) {
      setState(() {
        _output = 'Please enter a command.';
      });
      return;
    }

    setState(() {
      _isRunning = true;
      _output = 'Connecting to $host:$_port as $username...\n';
    });

    SSHClient? client;

    try {
      final socket = await SSHSocket.connect(host, _port);

      client = SSHClient(
        socket,
        username: username,
        onPasswordRequest: () => password,
      );

      setState(() {
        _output += 'Connected. Running: $command\n\n';
      });

      // 3. Run command (returns raw bytes)
      final resultBytes = await client.run(command);
      final resultText = utf8.decode(resultBytes);

      setState(() {
        _output += resultText;
      });
    } catch (e) {
      setState(() {
        _output += '\nERROR: $e';
      });
    } finally {

      try {
        client?.close();
        await client?.done;
      } catch (_) {
      }

      setState(() {
        _isRunning = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    final host = _hostController.text.trim();
    final username = _usernameController.text.trim();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Simple SSH Client'),
      ),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 800),
          child: Padding(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              children: [
                Card(
                  elevation: 0,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16),
                    side: BorderSide(color: theme.colorScheme.outlineVariant),
                  ),
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Connection',
                          style: theme.textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        const SizedBox(height: 12),
                        Row(
                          children: [
                            Expanded(
                              child: TextField(
                                controller: _hostController,
                                decoration: const InputDecoration(
                                  labelText: 'Host / IP',
                                  hintText: 'e.g. 192.168.0.10',
                                  prefixIcon: Icon(Icons.dns_outlined),
                                ),
                              ),
                            ),
                            const SizedBox(width: 12),
                            SizedBox(
                              width: 90,
                              child: TextField(
                                enabled: false,
                                decoration: InputDecoration(
                                  labelText: 'Port',
                                  hintText: _port.toString(),
                                  prefixIcon: const Icon(Icons.numbers),
                                ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),
                        Row(
                          children: [
                            Expanded(
                              child: TextField(
                                controller: _usernameController,
                                decoration: const InputDecoration(
                                  labelText: 'Username',
                                  prefixIcon: Icon(Icons.person_outline),
                                ),
                              ),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: TextField(
                                controller: _passwordController,
                                obscureText: true,
                                decoration: const InputDecoration(
                                  labelText: 'Password',
                                  prefixIcon: Icon(Icons.lock_outline),
                                ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),
                        Row(
                          children: [
                            Icon(
                              host.isNotEmpty && username.isNotEmpty
                                  ? Icons.check_circle_outline
                                  : Icons.info_outline,
                              size: 18,
                              color: host.isNotEmpty && username.isNotEmpty
                                  ? theme.colorScheme.primary
                                  : theme.colorScheme.outline,
                            ),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                host.isNotEmpty && username.isNotEmpty
                                    ? 'Server: $username@$host:$_port'
                                    : 'Server: <not set>',
                                style: theme.textTheme.bodyMedium!
                                    .copyWith(fontWeight: FontWeight.w600),
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 16),

                // Command card
                Card(
                  elevation: 0,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(16),
                    side: BorderSide(color: theme.colorScheme.outlineVariant),
                  ),
                  child: Padding(
                    padding: const EdgeInsets.all(16.0),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Command',
                          style: theme.textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        const SizedBox(height: 8),
                        TextField(
                          controller: _commandController,
                          decoration: const InputDecoration(
                            labelText: 'Command',
                            hintText: 'e.g. ls -la /',
                            prefixIcon: Icon(Icons.terminal),
                          ),
                          onSubmitted: (_) => _runCommand(),
                        ),
                        const SizedBox(height: 12),
                        SizedBox(
                          width: double.infinity,
                          child: FilledButton.icon(
                            onPressed: _isRunning ? null : _runCommand,
                            icon: _isRunning
                                ? const SizedBox(
                              height: 16,
                              width: 16,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                              ),
                            )
                                : const Icon(Icons.send),
                            label: Text(
                              _isRunning ? 'Running...' : 'Run on server',
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 16),

                // Output card
                Expanded(
                  child: Card(
                    elevation: 0,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(16),
                      side: BorderSide(
                        color: theme.colorScheme.outlineVariant,
                      ),
                    ),
                    child: Padding(
                      padding: const EdgeInsets.all(12.0),
                      child: SingleChildScrollView(
                        child: SelectableText(
                          _output,
                          style: const TextStyle(
                            fontFamily: 'monospace',
                            fontSize: 13,
                          ),
                        ),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
