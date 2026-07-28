import 'package:flutter/material.dart';

void main() {
  runApp(const WidgetApp());
}

class WidgetApp extends StatelessWidget {
  const WidgetApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Touch Widgets Demo',
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
      ),
      home: const TouchInteractionsPage(),
    );
  }
}

class TouchInteractionsPage extends StatelessWidget {
  const TouchInteractionsPage({super.key});я

  @override
  Widget build(BuildContext context) {
    return const _TouchInteractionsScaffold();
  }
}

class _TouchInteractionsScaffold extends StatefulWidget {
  const _TouchInteractionsScaffold();

  @override
  State<_TouchInteractionsScaffold> createState() =>
      _TouchInteractionsScaffoldState();
}

class _TouchInteractionsScaffoldState extends State<_TouchInteractionsScaffold> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Сенсорные взаимодействия (Flutter)'),
      ),
      body: const _TouchDemosList(),
    );
  }
}

class _TouchDemosList extends StatelessWidget {
  const _TouchDemosList();

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: const [
        _DemoCard(
          title: 'Tap / Double tap / Long press (InkWell)',
          child: _TapLongPressDemo(),
        ),
        SizedBox(height: 12),
        _DemoCard(
          title: 'Swipe-to-dismiss (Dismissible)',
          child: _DismissibleListDemo(),
        ),
        SizedBox(height: 12),
        _DemoCard(
          title: 'Drag & Drop (Draggable / DragTarget)',
          child: _DragDropDemo(),
        ),
        SizedBox(height: 12),
        _DemoCard(
          title: 'Pinch zoom / rotate (GestureDetector)',
          child: _ScaleRotateDemo(),
        ),
        SizedBox(height: 12),
        _DemoCard(
          title: 'Drag scrubber (onHorizontalDragUpdate)',
          child: _ScrubberDemo(),
        ),
      ],
    );
  }
}

class _DemoCard extends StatelessWidget {
  const _DemoCard({
    required this.title,
    required this.child,
  });

  final String title;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      clipBehavior: Clip.antiAlias,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: theme.textTheme.titleMedium),
            const SizedBox(height: 12),
            child,
          ],
        ),
      ),
    );
  }
}

class _TapLongPressDemo extends StatefulWidget {
  const _TapLongPressDemo();

  @override
  State<_TapLongPressDemo> createState() => _TapLongPressDemoState();
}

class _TapLongPressDemoState extends State<_TapLongPressDemo> {
  int taps = 0;
  int doubleTaps = 0;
  int longPresses = 0;

  void _showSnack(String text) {
    final messenger = ScaffoldMessenger.of(context);
    messenger
      ..hideCurrentSnackBar()
      ..showSnackBar(SnackBar(content: Text(text)));
  }

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Material(
          color: cs.surfaceContainerHighest,
          borderRadius: BorderRadius.circular(16),
          child: InkWell(
            borderRadius: BorderRadius.circular(16),
            onTap: () {
              setState(() => taps++);
              _showSnack('Tap: $taps');
            },
            onDoubleTap: () {
              setState(() => doubleTaps++);
              _showSnack('Double tap: $doubleTaps');
            },
            onLongPress: () {
              setState(() => longPresses++);
              _showSnack('Long press: $longPresses');
            },
            child: SizedBox(
              height: 72,
              width: double.infinity,
            ),
          ),
        ),
      ],
    );
  }
}

class _DismissibleListDemo extends StatefulWidget {
  const _DismissibleListDemo();

  @override
  State<_DismissibleListDemo> createState() => _DismissibleListDemoState();
}

class _DismissibleListDemoState extends State<_DismissibleListDemo> {
  final List<String> items = List.generate(5, (i) => 'Элемент #${i + 1}');
  String? lastDeleted;
  int? lastDeletedIndex;

  void _undo() {
    final value = lastDeleted;
    final idx = lastDeletedIndex;
    if (value == null || idx == null) return;
    setState(() {
      items.insert(idx, value);
      lastDeleted = null;
      lastDeletedIndex = null;
    });
  }

  @override
  Widget build(BuildContext context) {
    final messenger = ScaffoldMessenger.of(context);
    return Column(
      children: [
        for (final item in items)
          Dismissible(
            key: ValueKey(item),
            background: Container(
              color: Colors.green.withValues(alpha: 0.2),
              alignment: Alignment.centerLeft,
              padding: const EdgeInsets.only(left: 16),
              child: const Icon(Icons.check),
            ),
            secondaryBackground: Container(
              color: Colors.red.withValues(alpha: 0.2),
              alignment: Alignment.centerRight,
              padding: const EdgeInsets.only(right: 16),
              child: const Icon(Icons.delete),
            ),
            onDismissed: (direction) {
              final index = items.indexOf(item);
              setState(() {
                lastDeleted = item;
                lastDeletedIndex = index;
                items.removeAt(index);
              });
              messenger
                ..hideCurrentSnackBar()
                ..showSnackBar(
                  SnackBar(
                    content: Text('Удалено: $item'),
                    action: SnackBarAction(label: 'Undo', onPressed: _undo),
                  ),
                );
            },
            child: ListTile(
              title: Text(item),
              leading: const Icon(Icons.drag_indicator),
              dense: true,
            ),
          ),
      ],
    );
  }
}

class _DragDropDemo extends StatefulWidget {
  const _DragDropDemo();

  @override
  State<_DragDropDemo> createState() => _DragDropDemoState();
}

class _DragDropDemoState extends State<_DragDropDemo> {
  Color? droppedToA;
  Color? droppedToB;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Row(
          children: [
            Expanded(
              child: _DropZone(
                color: droppedToA,
                onAccept: (c) => setState(() => droppedToA = c),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _DropZone(
                color: droppedToB,
                onAccept: (c) => setState(() => droppedToB = c),
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        Wrap(
          spacing: 12,
          runSpacing: 12,
          children: const [
            _ColorChip(color: Colors.deepPurple),
            _ColorChip(color: Colors.teal),
            _ColorChip(color: Colors.orange),
          ],
        ),
      ],
    );
  }
}

class _ColorChip extends StatelessWidget {
  const _ColorChip({required this.color});

  final Color color;

  @override
  Widget build(BuildContext context) {
    return Draggable<Color>(
      data: color,
      feedback: _ChipBody(color: color, elevated: true),
      childWhenDragging: _ChipBody(color: color.withValues(alpha: 0.3)),
      child: _ChipBody(color: color),
    );
  }
}

class _ChipBody extends StatelessWidget {
  const _ChipBody({required this.color, this.elevated = false});

  final Color color;
  final bool elevated;

  @override
  Widget build(BuildContext context) {
    return Material(
      elevation: elevated ? 6 : 0,
      color: color,
      borderRadius: BorderRadius.circular(999),
      child: const SizedBox(width: 44, height: 44),
    );
  }
}

class _DropZone extends StatelessWidget {
  const _DropZone({
    required this.color,
    required this.onAccept,
  });

  final Color? color;
  final ValueChanged<Color> onAccept;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return DragTarget<Color>(
      onAcceptWithDetails: (details) => onAccept(details.data),
      builder: (context, candidate, rejected) {
        final isOver = candidate.isNotEmpty;
        return AnimatedContainer(
          duration: const Duration(milliseconds: 120),
          height: 90,
          decoration: BoxDecoration(
            color: (color ?? theme.colorScheme.surfaceContainerHighest)
                .withValues(alpha: isOver ? 0.85 : 1),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(
              color: isOver ? theme.colorScheme.primary : Colors.transparent,
              width: 2,
            ),
          ),
        );
      },
    );
  }
}

class _ScaleRotateDemo extends StatefulWidget {
  const _ScaleRotateDemo();

  @override
  State<_ScaleRotateDemo> createState() => _ScaleRotateDemoState();
}

class _ScaleRotateDemoState extends State<_ScaleRotateDemo> {
  double scale = 1.0;
  double rotation = 0.0;

  double _startScale = 1.0;
  double _startRotation = 0.0;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return ClipRRect(
      borderRadius: BorderRadius.circular(16),
      child: ColoredBox(
        color: theme.colorScheme.surfaceContainerHighest,
        child: SizedBox(
          height: 160,
          width: double.infinity,
          child: Center(
            child: GestureDetector(
              onScaleStart: (d) {
                _startScale = scale;
                _startRotation = rotation;
              },
              onScaleUpdate: (d) {
                setState(() {
                  scale = (_startScale * d.scale).clamp(0.6, 3.0);
                  rotation = _startRotation + d.rotation;
                });
              },
              onDoubleTap: () {
                setState(() {
                  scale = 1.0;
                  rotation = 0.0;
                });
              },
              child: Transform(
                alignment: Alignment.center,
                transform: Matrix4.identity()
                  ..scale(scale)
                  ..rotateZ(rotation),
                child: const FlutterLogo(size: 80),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _ScrubberDemo extends StatefulWidget {
  const _ScrubberDemo();

  @override
  State<_ScrubberDemo> createState() => _ScrubberDemoState();
}

class _ScrubberDemoState extends State<_ScrubberDemo> {
  double value = 0.35;

  void _setFromLocalDx(double dx, double width) {
    final v = (dx / width).clamp(0.0, 1.0);
    setState(() => value = v);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return LayoutBuilder(
      builder: (context, c) {
        final width = c.maxWidth;
        return GestureDetector(
          behavior: HitTestBehavior.opaque,
          onTapDown: (d) => _setFromLocalDx(d.localPosition.dx, width),
          onHorizontalDragUpdate: (d) =>
              _setFromLocalDx(d.localPosition.dx, width),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(999),
            child: SizedBox(
              height: 18,
              child: Stack(
                children: [
                  ColoredBox(
                    color: theme.colorScheme.surfaceContainerHighest,
                    child: const SizedBox.expand(),
                  ),
                  FractionallySizedBox(
                    widthFactor: value,
                    child: ColoredBox(
                      color: theme.colorScheme.primary,
                      child: const SizedBox.expand(),
                    ),
                  ),
                  Align(
                    alignment: Alignment(value * 2 - 1, 0),
                    child: Container(
                      width: 22,
                      height: 22,
                      decoration: BoxDecoration(
                        color: theme.colorScheme.onPrimary,
                        borderRadius: BorderRadius.circular(999),
                        border: Border.all(
                          color: theme.colorScheme.primary,
                          width: 2,
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }
}
