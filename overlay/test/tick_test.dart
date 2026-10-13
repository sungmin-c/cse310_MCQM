// 계약 테스트: docs/schema/sample.jsonl 모든 줄을 버블 파서가 받아들이는지 (SCHEMA.md 계약 테스트 표의 Flutter 쪽)
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:mcqm_overlay/tick.dart';

void main() {
  final lines = File('../docs/schema/sample.jsonl')
      .readAsLinesSync()
      .where((l) => l.trim().isNotEmpty)
      .toList();

  test('sample.jsonl 전부 파싱', () {
    expect(lines, isNotEmpty);
    for (final l in lines) {
      expect(Tick.tryParse(l), isNotNull, reason: l);
    }
  });

  test('v1: failed면 Wi-Fi 패널, passed면 조치 없음', () {
    final ticks = lines.map(Tick.tryParse).whereType<Tick>().toList();
    for (final t in ticks) {
      expect(t.actionCode, t.passed ? isNull : 'open_wifi_panel');
    }
  });

  test('v1.1 초안 필드 우선', () {
    final t = Tick.tryParse('{"qoe": 41, "verdict": "failed", "validated": false, "advice": "old",'
        ' "diagnosis": {"cause": "bandwidth", "confidence": 0.8},'
        ' "action": {"code": "open_internet_panel", "text": "new"}}')!;
    expect(t.actionCode, 'open_internet_panel');
    expect(t.actionLine, '조치: new');
    expect(t.causeLine, '원인: 대역폭 부족 (신뢰도 80%)');
  });

  test('깨진 메시지는 null', () {
    expect(Tick.tryParse('not json'), isNull);
    expect(Tick.tryParse('{"verdict": "passed"}'), isNull);
  });
}
