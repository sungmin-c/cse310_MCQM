// MCQM 오버레이 스파이크 (M0-a): Android 13에서 통화 앱 위 버블이 동작하는지 확인한다.
//   메인 화면: 권한 요청, 버블 표시/닫기, RSSI 읽기, 설정 패널 열기 (시험용 버튼)
//   버블(overlayMain): docs/SCHEMA.md tick을 WebSocket으로 받아 상태 색·QoE·문구 표시, [조치] → 설정 패널
// 버블은 별도 엔진에서 돌기 때문에 플랫폼 채널(RSSI·패널)은 메인 쪽이 처리하고, 둘은 shareData로 대화한다.
import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_overlay_window/flutter_overlay_window.dart';

import 'tick.dart';

const _device = MethodChannel('mcqm/device');

void main() => runApp(const MaterialApp(home: ControlPage()));

class ControlPage extends StatefulWidget {
  const ControlPage({super.key});
  @override
  State<ControlPage> createState() => _ControlPageState();
}

class _ControlPageState extends State<ControlPage> {
  // adb reverse tcp:8000 tcp:8000 이면 127.0.0.1, 핫스팟 LAN이면 192.168.137.1
  final _url = TextEditingController(text: 'ws://127.0.0.1:8000/ws');
  final _log = <String>[];

  @override
  void initState() {
    super.initState();
    // 버블이 보낸 요청: {"panel": code} 또는 {"need": "url"}
    FlutterOverlayWindow.overlayListener.listen((e) async {
      final m = e is String ? jsonDecode(e) : e;
      if (m is Map && m['panel'] != null) await _openPanel(m['panel']);
      if (m is Map && m['need'] == 'url') {
        await FlutterOverlayWindow.shareData(jsonEncode({'url': _url.text}));
      }
    });
  }

  void _say(String s) =>
      setState(() => _log.insert(0, '${TimeOfDay.now().format(context)} $s'));

  Future<void> _openPanel(String code) async {
    try {
      await _device.invokeMethod('openPanel', {'code': code});
      _say('panel opened: $code');
    } catch (e) {
      _say('panel error: $e');
    }
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('MCQM overlay spike')),
    body: ListView(
      padding: const EdgeInsets.all(12),
      children: [
        TextField(
          controller: _url,
          decoration: const InputDecoration(labelText: 'WebSocket URL'),
        ),
        Wrap(
          spacing: 8,
          children: [
            ElevatedButton(
              onPressed: () async => _say(
                'overlay permission: ${await FlutterOverlayWindow.requestPermission()}',
              ),
              child: const Text('1. 권한'),
            ),
            ElevatedButton(
              onPressed: () async {
                // flutter_overlay_window 1.0.0: 이미 떠 있을 때 다시 show하면 서비스가 스스로 멈춘다 → 건너뜀
                if (!await FlutterOverlayWindow.isActive()) {
                  // 단위 dp. S20 화면 폭 ≈ 411 dp → 그보다 넓으면 옆으로 못 움직인다(10/13 확인).
                  // 드래그는 플러그인(화면 좌표 rawX/rawY 사용)에 맡긴다. Flutter 쪽에서 하면 창 기준 좌표라
                  // 창이 움직이는 동안 떨린다(10/13 확인). 플러그인의 경계 버그는 third_party 수정본에서 고침.
                  // topLeft 정렬이라 x, y는 화면 왼쪽 위 기준 dp.
                  await FlutterOverlayWindow.showOverlay(
                    height: Bubble.expandedHeight,
                    width: Bubble.width,
                    alignment: OverlayAlignment.topLeft,
                    enableDrag: true,
                    positionGravity: PositionGravity.none,
                    // 시작 위치를 안 주면 y = −상태바(px)에 dp 변환이 한 번 더 걸려 화면 위로 사라진다 (10/13 확인)
                    startPosition: const OverlayPosition(
                      Bubble.startX,
                      Bubble.startY,
                    ),
                    overlayTitle: 'MCQM',
                    overlayContent: 'call quality bubble',
                  );
                }
                await Future.delayed(const Duration(milliseconds: 500));
                await FlutterOverlayWindow.shareData(
                  jsonEncode({'url': _url.text}),
                );
                _say('overlay shown');
              },
              child: const Text('2. 버블 표시'),
            ),
            ElevatedButton(
              onPressed: () async {
                await FlutterOverlayWindow.closeOverlay();
                _say('overlay closed');
              },
              child: const Text('버블 닫기'),
            ),
            ElevatedButton(
              onPressed: () async =>
                  _say('RSSI: ${await _device.invokeMethod('rssi')} dBm'),
              child: const Text('3. RSSI'),
            ),
            ElevatedButton(
              onPressed: () => _openPanel('open_wifi_panel'),
              child: const Text('4a. Wi-Fi 패널'),
            ),
            ElevatedButton(
              onPressed: () => _openPanel('open_internet_panel'),
              child: const Text('4b. 인터넷 패널'),
            ),
          ],
        ),
        const Divider(),
        ..._log.map(
          (l) => Text(
            l,
            style: const TextStyle(fontFamily: 'monospace', fontSize: 12),
          ),
        ),
      ],
    ),
  );
}

// ---------------------------------------------------------------- 버블 (별도 엔진)

@pragma('vm:entry-point')
void overlayMain() => runApp(
  MaterialApp(
    debugShowCheckedModeBanner: false,
    // 버블 크기가 고정이라 폰 글꼴 크기 설정을 따르면 넘친다(10/13: 37 px 넘침) → 배율 고정
    builder: (context, child) => MediaQuery(
      data: MediaQuery.of(context).copyWith(textScaler: TextScaler.noScaling),
      child: child!,
    ),
    home: const Bubble(),
  ),
);

class Bubble extends StatefulWidget {
  const Bubble({super.key});
  static const double startX = 30, startY = 120;
  // 단위 dp. S20 화면 폭 ≈ 411 dp. 작게 = 제목 줄(상태·조치·크기·닫기)만, 크게 = 원인·조치 문구까지
  static const int width = 340, compactHeight = 72, expandedHeight = 200;
  @override
  State<Bubble> createState() => _BubbleState();
}

class _BubbleState extends State<Bubble> {
  bool _expanded = true;

  Future<void> _toggleSize() async {
    setState(() => _expanded = !_expanded);
    await FlutterOverlayWindow.resizeOverlay(
      Bubble.width,
      _expanded ? Bubble.expandedHeight : Bubble.compactHeight,
      true,
    );
  }

  Tick? _tick;
  String _status = 'waiting for URL';
  WebSocket? _ws;
  String? _url;
  Timer? _retry;

  @override
  void initState() {
    super.initState();
    FlutterOverlayWindow.overlayListener.listen((e) {
      final m = e is String ? jsonDecode(e) : e;
      if (m is Map && m['url'] is String && m['url'] != _url) {
        _url = m['url'];
        _connect();
      }
    });
    FlutterOverlayWindow.shareData(jsonEncode({'need': 'url'}));
  }

  Future<void> _connect() async {
    _retry?.cancel();
    await _ws?.close();
    setState(() => _status = 'connecting…');
    try {
      final ws = await WebSocket.connect(
        _url!,
      ).timeout(const Duration(seconds: 5));
      _ws = ws;
      setState(() => _status = 'connected');
      ws.listen(
        (data) {
          final t = Tick.tryParse(data as String);
          if (t != null) setState(() => _tick = t);
        },
        onDone: _scheduleRetry,
        onError: (_) => _scheduleRetry(),
      );
    } catch (e) {
      setState(() => _status = 'connect failed');
      _scheduleRetry();
    }
  }

  void _scheduleRetry() {
    if (!mounted) return;
    setState(() => _status = 'disconnected — retry in 3 s');
    _retry = Timer(const Duration(seconds: 3), _connect);
  }

  Widget _iconButton(IconData icon, Future<Object?> Function() onTap) =>
      GestureDetector(
        onTap: onTap,
        behavior: HitTestBehavior.opaque,
        child: SizedBox(
          width: 32,
          height: 32,
          child: Icon(icon, color: Colors.white70, size: 18),
        ),
      );

  @override
  Widget build(BuildContext context) {
    final t = _tick;
    final color = t == null
        ? Colors.grey
        : (t.passed ? Colors.green : Colors.red);
    return Material(
      color: Colors.transparent,
      child: Container(
        margin: const EdgeInsets.all(4),
        padding: const EdgeInsets.all(10),
        decoration: BoxDecoration(
          color: Colors.black87,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: color, width: 3),
        ),
        child: DefaultTextStyle(
          style: const TextStyle(color: Colors.white, fontSize: 13),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Row(
                children: [
                  Icon(Icons.circle, color: color, size: 14),
                  const SizedBox(width: 6),
                  Expanded(
                    child: Text(
                      t == null
                          ? _status
                          : 'QoE ${t.qoe.toStringAsFixed(0)} ${t.passed ? "PASSED" : "FAILED"}',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 15,
                      ),
                    ),
                  ),
                  if (t != null && !t.validated)
                    const Text(
                      '추정값 ',
                      style: TextStyle(fontSize: 11, color: Colors.amber),
                    ),
                  // [조치]는 제목 줄에 둔다 — 아래에 두면 버블 높이를 넘으면 잘려 안 보인다(10/13 확인)
                  if (t?.actionCode != null)
                    GestureDetector(
                      onTap: () => FlutterOverlayWindow.shareData(
                        jsonEncode({'panel': t!.actionCode}),
                      ),
                      child: Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 8,
                          vertical: 4,
                        ),
                        decoration: BoxDecoration(
                          color: Colors.lightBlue,
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: const Text(
                          '조치',
                          style: TextStyle(fontWeight: FontWeight.bold),
                        ),
                      ),
                    ),
                  _iconButton(
                    _expanded ? Icons.close_fullscreen : Icons.open_in_full,
                    _toggleSize,
                  ),
                  _iconButton(Icons.close, FlutterOverlayWindow.closeOverlay),
                ],
              ),
              if (t != null && _expanded)
                Text(t.causeLine, maxLines: 1, overflow: TextOverflow.ellipsis),
              if (t != null && _expanded)
                Text(
                  t.actionLine,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
            ],
          ),
        ),
      ),
    );
  }
}
