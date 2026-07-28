import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:mailer/mailer.dart';
import 'package:mailer/smtp_server.dart';

void main() {
  runApp(const MyApp());
}

class Recipient {
  final String name;
  final String email;

  Recipient(this.name, this.email);
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'SMTP Demo',
      theme: ThemeData(useMaterial3: true),
      home: const EmailFormPage(),
    );
  }
}

class EmailFormPage extends StatefulWidget {
  const EmailFormPage({super.key});

  @override
  State<EmailFormPage> createState() => _EmailFormPageState();
}

class _EmailFormPageState extends State<EmailFormPage> {
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  final _bodyController = TextEditingController();
  final _signatureController = TextEditingController();

  final List<Recipient> _recipients = [];

  bool _isSending = false;

  final Duration _delayBetweenEmails = const Duration(seconds: 5);

  final String username = 'arinin.matvey@yandex.ru';
  final String password = 'mlabjkztzmrxcwmm';

  @override
  void initState() {
    super.initState();

    _recipients.addAll([
      Recipient('Данила Павлович', 'danila@posevin.com'),
      Recipient('Данила Павлович', 'posevin@bmstu.ru'),
      Recipient('Друг', 'mrholley4@gmail.com'),
    ]);
  }

  @override
  void dispose() {
    _nameController.dispose();
    _emailController.dispose();
    _bodyController.dispose();
    _signatureController.dispose();
    super.dispose();
  }

  void _addRecipient() {
    final name = _nameController.text.trim();
    final email = _emailController.text.trim();

    if (name.isEmpty || email.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Имя и email не должны быть пустыми')),
      );
      return;
    }

    final exists =
    _recipients.any((r) => r.email.toLowerCase() == email.toLowerCase());

    if (exists) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Этот email уже есть в списке')),
      );
      return;
    }

    setState(() {
      _recipients.add(Recipient(name, email));
      _nameController.clear();
      _emailController.clear();
    });
  }

  Future<void> _sendEmails() async {
    if (_recipients.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Список адресатов пуст')),
      );
      return;
    }

    final bodyText = _bodyController.text.trim();
    final signatureText = _signatureController.text.trim();

    if (bodyText.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Введите текст письма')),
      );
      return;
    }

    setState(() => _isSending = true);

    final smtpServer = yandex(username, password);

    try {
      final connection = PersistentConnection(smtpServer);

      const colors = [
        'red',
        'green',
        'blue',
        '#ff6600',
        '#9900cc',
        '#009688',
      ];

      for (final recipient in _recipients) {
        final subject = 'Привет, ${recipient.name}!';

        final words =
        bodyText.split(RegExp(r'\s+')).where((w) => w.isNotEmpty);
        final colored = <String>[];

        var i = 0;
        for (final w in words) {
          final safeWord = htmlEscape.convert(w);
          colored.add(
            '<span style="color: ${colors[i % colors.length]}">$safeWord</span>',
          );
          i++;
        }

        final logo = FileAttachment(File('assets/logo2.jpg'))
          ..location = Location.inline
          ..cid = '<logoImage>';

        final htmlBody = '''
<html>
  <body>
    <p>${colored.join(' ')}</p>
    <br><br>
    ${signatureText.isNotEmpty ? "<p>${htmlEscape.convert(signatureText)}</p>" : ""}
    <img src="cid:logoImage" alt="Logo">
  </body>
</html>
''';

        final message = Message()
          ..from = Address(username, 'Matvey Arinin')
          ..recipients.add(recipient.email)
          ..subject = subject
          ..text = bodyText
          ..html = htmlBody
          ..attachments.add(logo);

        try {
          final sendReport = await connection.send(message);
          print('Message sent to ${recipient.email}: $sendReport');
        } on MailerException catch (e) {
          print('Message NOT sent to ${recipient.email}.');
          for (var p in e.problems) {
            print('Problem: ${p.code}: ${p.msg}');
          }
        }

        await Future.delayed(_delayBetweenEmails);
      }

      await connection.close();

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Отправка завершена')),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isSending = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('SMTP рассылка'),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            TextField(
              controller: _nameController,
              decoration: const InputDecoration(
                labelText: 'Имя',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 8),
            TextField(
              controller: _emailController,
              decoration: const InputDecoration(
                labelText: 'Email',
                border: OutlineInputBorder(),
              ),
              keyboardType: TextInputType.emailAddress,
            ),
            const SizedBox(height: 8),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: _isSending ? null : _addRecipient,
                icon: const Icon(Icons.person_add),
                label: const Text('Добавить адресата'),
              ),
            ),
            const SizedBox(height: 16),

            Expanded(
              child: _recipients.isEmpty
                  ? const Center(child: Text('Пока нет адресатов'))
                  : SingleChildScrollView(
                child: DataTable(
                  columns: const [
                    DataColumn(label: Text('Имя')),
                    DataColumn(label: Text('Email')),
                    DataColumn(label: Text('')),
                  ],
                  rows: _recipients
                      .asMap()
                      .entries
                      .map(
                        (entry) => DataRow(
                      cells: [
                        DataCell(Text(entry.value.name)),
                        DataCell(Text(entry.value.email)),
                        DataCell(
                          IconButton(
                            icon: const Icon(Icons.delete),
                            tooltip: 'Удалить',
                            onPressed: _isSending
                                ? null
                                : () {
                              setState(() {
                                _recipients
                                    .removeAt(entry.key);
                              });
                            },
                          ),
                        ),
                      ],
                    ),
                  )
                      .toList(),
                ),
              ),
            ),

            const SizedBox(height: 8),

            TextField(
              controller: _bodyController,
              maxLines: 4,
              decoration: const InputDecoration(
                labelText: 'Текст письма',
                alignLabelWithHint: true,
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 8),
            
            TextField(
              controller: _signatureController,
              maxLines: 2,
              decoration: const InputDecoration(
                labelText: 'Подпись',
                alignLabelWithHint: true,
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 8),

            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: _isSending ? null : _sendEmails,
                icon: _isSending
                    ? const SizedBox(
                  width: 16,
                  height: 16,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
                    : const Icon(Icons.send),
                label:
                Text(_isSending ? 'Отправляем...' : 'Отправить всем'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
