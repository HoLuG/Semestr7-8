import 'package:mailer/mailer.dart';
import 'package:mailer/smtp_server.dart';

// ставим: flutter pub add mailer

//https://pub.dev/documentation/mailer/latest/smtp_server_yandex/yandex.html
//https://pub.dev/documentation/mailer/latest/smtp_server_yandex/smtp_server_yandex-library.html
//https://pub.dev/packages/mailer/install

// Как создать пароль приложения для Яндекса (https://yandex.ru/support/id/ru/authorization/app-passwords.html)
// Тут https://id.yandex.ru/security в разделе "Пароли приложений" выбираем "Почта" -> вводим имя пароля, я ввел "Flutter", получаем пароль: fcogbelywgwutrbh
// liybpuwcpthhyfra - второй пароль

main() async {
  // Note that using a username and password for gmail only works if
  // you have two-factor authentication enabled and created an App password.
  // Search for "gmail app password 2fa"
  // The alternative is to use oauth.
  String username = 'arinin.matvey@yandex.ru';
  String password = 'mlabjkztzmrxcwmm'; // <- это пароль для приложения, а не пароль от ящика! Пароль от ящика 12345678990robotland

  final smtpServer = yandex(username, password);
  // Use the SmtpServer class to configure an SMTP server:
  // final smtpServer = SmtpServer('smtp.domain.com');
  // See the named arguments of SmtpServer for further configuration
  // options.

  // Create our message.
  final message = Message()
    ..from = Address(username, 'Matvey Arinin')
    ..recipients.add('matvey4@bk.ru')
    ..ccRecipients.addAll(['mrholley4@gmail.com', ])
    //..bccRecipients.add(Address('posevin@bmstu.ru'))
    ..subject = 'Test Dart Mailer library 1 :: 😀 :: ${DateTime.now()}'
    ..text = 'This is the plain text.\nThis is line 2 of the text part.'
    ..html = "<h1>Test</h1>\n<p>Hey! Here's some HTML content</p>";

  try {
    final sendReport = await send(message, smtpServer);
    print('Message sent: ' + sendReport.toString());
  } on MailerException catch (e) {
    print('Message not sent.');
    for (var p in e.problems) {
      print('Problem: ${p.code}: ${p.msg}');
    }
  }
  // DONE


  // Let's send another message using a slightly different syntax:
  //
  // Addresses without a name part can be set directly.
  // For instance `..recipients.add('destination@example.com')`
  // If you want to display a name part you have to create an
  // Address object: `new Address('destination@example.com', 'Display name part')`
  // Creating and adding an Address object without a name part
  // `new Address('destination@example.com')` is equivalent to
  // adding the mail address as `String`.
  final equivalentMessage = Message()
    ..from = Address(username, 'Аринин Матвей 😀')
    ..recipients.add(Address('matvey4@bk.ru'))
    ..ccRecipients.addAll([Address('mrholley4@gmail.com')])
    //..bccRecipients.add('posevin@gmail.com')
    ..subject = 'Test Dart Mailer library 2 :: 😀 :: ${DateTime.now()}'
    ..text = 'This is the plain text.\nThis is line 2 of the text part.'
    ..html = '<h1>Test</h1>\n<p>Hey! Here is some HTML content</p><img src="https://bmstu.ru/assets/images/logo/logo.png"/>';


  final sendReport2 = await send(equivalentMessage, smtpServer);

  // Sending multiple messages with the same connection
  //
  // Create a smtp client that will persist the connection
  var connection = PersistentConnection(smtpServer);

  // Send the first message
  await connection.send(message);

  // send the equivalent message
  await connection.send(equivalentMessage);

  // close the connection
  await connection.close();
}
