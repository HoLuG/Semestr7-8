import 'dart:convert';
import 'dart:io';

Future<void> main(List<String> args) async {
  final port = args.isNotEmpty ? int.tryParse(args.first) ?? 8090 : 8090;

  final ifaces = await NetworkInterface.list(
    type: InternetAddressType.IPv4,
    includeLinkLocal: true,
  );
  for (final ni in ifaces) {
    for (final addr in ni.addresses) {
      stdout.writeln('Interface ${ni.name}: ${addr.address}');
    }
  }

  final server = await HttpServer.bind(InternetAddress.anyIPv4, port);
  stdout.writeln('WebSocket server running on port $port (all IPv4 interfaces)');

  final sliderStore = TwoSliderStore(filePath: 'sliders.json');
  await sliderStore.init();

  await for (final request in server) {
    if (WebSocketTransformer.isUpgradeRequest(request)) {
      final socket = await WebSocketTransformer.upgrade(request);
      handleWebSocket(socket, sliderStore);
    } else {
      request.response.statusCode = HttpStatus.methodNotAllowed;
      request.response.write('WebSocket endpoint only.');
      await request.response.close();
    }
  }
}

void handleWebSocket(WebSocket socket, TwoSliderStore store) {
  stdout.writeln('Client connected: ${socket.hashCode}');
  socket.listen((dynamic data) async {
    try {
      final msg = parseMessage(data);
      switch (msg['type']) {
        case 'calc':
          final op = msg['op'] as String;
          final num a = (msg['a'] as num);
          final num b = (msg['b'] as num);
          num result;
          switch (op) {
            case '+': result = a + b; break;
            case '-': result = a - b; break;
            case '*': result = a * b; break;
            case '/':
              if (b == 0) throw Exception('Division by zero');
              result = a / b; break;
            default: throw Exception('Unsupported op: $op');
          }
          socket.add(jsonEncode({
            'type': 'calc_result',
            'op': op,
            'a': a,
            'b': b,
            'result': result,
          }));
          break;

        case 'set_slider':
          final which = (msg['which'] as String?)?.toLowerCase();
          if (which != 'a' && which != 'b') {
            throw Exception("which must be 'a' or 'b'");
          }
          final int value = (msg['value'] as num).round().clamp(0, 100);
          await store.set(which!, value);
          final s = await store.get();
          socket.add(jsonEncode({
            'type': 'sliders',
            'a': s['a'],
            'b': s['b'],
            'sum': (s['a'] ?? 0) + (s['b'] ?? 0),
          }));
          break;

        case 'get_sliders':
          final s = await store.get();
          socket.add(jsonEncode({
            'type': 'sliders',
            'a': s['a'],
            'b': s['b'],
            'sum': (s['a'] ?? 0) + (s['b'] ?? 0),
          }));
          break;

        default:
          throw Exception('Unknown type: ${msg['type']}');
      }
    } catch (e) {
      socket.add(jsonEncode({'type': 'error', 'message': e.toString()}));
    }
  }, onDone: () {
    stdout.writeln('Client disconnected: ${socket.hashCode}');
  }, onError: (err) {
    stdout.writeln('WS error: $err');
  });
}

Map<String, dynamic> parseMessage(dynamic data) {
  if (data is String) {
    return json.decode(data) as Map<String, dynamic>;
  } else if (data is List<int>) {
    return json.decode(utf8.decode(data)) as Map<String, dynamic>;
  } else {
    throw Exception('Unsupported message format');
  }
}

class TwoSliderStore {
  final String filePath;
  int aValue = 0;
  int bValue = 0;

  TwoSliderStore({required this.filePath});

  Future<void> init() async {
    final file = File(filePath);
    if (await file.exists()) {
      try {
        final txt = await file.readAsString();
        final m = jsonDecode(txt) as Map<String, dynamic>;
        aValue = (m['a'] as num?)?.round().clamp(0, 100) ?? 0;
        bValue = (m['b'] as num?)?.round().clamp(0, 100) ?? 0;
      } catch (_) {
        aValue = 0; bValue = 0;
        await save();
      }
    } else {
      aValue = 0; bValue = 0;
      await save();
    }
  }

  Future<Map<String, int>> get() async => {'a': aValue, 'b': bValue};

  Future<void> set(String which, int value) async {
    if (which == 'a') aValue = value.clamp(0, 100);
    if (which == 'b') bValue = value.clamp(0, 100);
    await save();
  }

  Future<void> save() async {
    final file = File(filePath);
    await file.writeAsString(jsonEncode({'a': aValue, 'b': bValue}));
  }
}
