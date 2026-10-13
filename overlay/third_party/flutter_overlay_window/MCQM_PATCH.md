# MCQM 수정본 (flutter_overlay_window 1.0.0, MIT)

pub.dev 1.0.0 원본을 복사해 한 곳만 고쳤다 (2026-10-13, Sungmin).
- `OverlayService.applySoftBoundaryConstraints`: LEFT/TOP 중력에서 드래그 경계를 '창 폭/높이 근처'로 잘못 제한해
  버블이 오른쪽·아래로 못 가는 벽이 생기던 문제 → 화면 크기 기준으로 제한하도록 수정.
- `example/`는 뺐다. 나머지는 원본 그대로. 업스트림이 고치면 pub.dev 버전으로 되돌린다.
