// docs/SCHEMA.md tick 메시지 → 버블 표시값. v1.1 초안 필드(diagnosis, action)가 없으면 v1 필드로 대체한다.
import 'dart:convert';

class Tick {
  final double qoe;
  final bool passed;
  final bool validated;
  final String? cause; // v1.1 diagnosis.cause
  final double? confidence; // v1.1 diagnosis.confidence
  final String? actionCode; // v1.1 action.code (없으면 failed일 때 Wi-Fi 패널)
  final String? actionText; // v1.1 action.text, 없으면 v1 advice

  Tick(
    this.qoe,
    this.passed,
    this.validated,
    this.cause,
    this.confidence,
    this.actionCode,
    this.actionText,
  );

  static Tick? tryParse(String raw) {
    try {
      final m = jsonDecode(raw) as Map<String, dynamic>;
      final passed = m['verdict'] == 'passed';
      final diag = m['diagnosis'] as Map<String, dynamic>?;
      final action = m['action'] as Map<String, dynamic>?;
      return Tick(
        (m['qoe'] as num).toDouble(),
        passed,
        m['validated'] == true,
        diag?['cause'] as String?,
        (diag?['confidence'] as num?)?.toDouble(),
        action?['code'] as String? ?? (passed ? null : 'open_wifi_panel'),
        action?['text'] as String? ?? m['advice'] as String?,
      );
    } catch (_) {
      return null;
    }
  }

  static const _causeKo = {
    'bandwidth': '대역폭 부족',
    'delay_jitter': '지연·떨림',
    'loss': '패킷 손실',
    'weak_wifi': '약한 Wi-Fi',
    'none': '정상',
  };

  String get causeLine {
    if (cause == null) return passed ? '원인: 정상' : '원인: 분석 중';
    final c = confidence == null
        ? ''
        : ' (신뢰도 ${(confidence! * 100).round()}%)';
    return '원인: ${_causeKo[cause] ?? cause}$c';
  }

  String get actionLine => actionText == null ? '' : '조치: $actionText';
}
