# -*- coding: utf-8 -*-
"""consultation_checklists.json 어지럼(dizziness) 필수 질문 보강 + 판 표시(cl-v3) — REQ-PJOV §3(호스트 → medical-eval, 2026-10-28).

호스트 재판정에서 어지럼 답변 15건이 지속 시간·반복 여부·청력 변화를 되물었는데 SV-03 이 '확인 0건' 이었다. 원인은
판정기가 아니라 표다 — cl-v2 어지럼 필수 질문이 「지속적 악화」「시야 흐림」 둘뿐이어서 임상적으로 맞는 질문이 표에
없었다. 여기서 세 항목을 더한다(사용자 결정 2026-10-30 「보강 진행」).

키워드 규칙은 cl-v2 와 같다 — 판정기(medical-eval sv-v3+)는 답변 문장에 **라벨 또는 강한 키워드 1개** 가 있으면 확인으로
세고, 2자 이하 키워드는 같은 문장에 되묻기·조건 표지나 항목의 다른 키워드가 함께일 때만 센다. '여부'·'시간'·'변화' 는
판정기의 약한 낱말이므로 라벨에만 두고 키워드로는 쓰지 않는다. 기존 「지속적 악화」 와 겹치지 않게 '지속' 홑낱말은 넣지
않고 '얼마나 지속'·'계속 지속'·'한참 지속' 꼴로 둔다. 재실행해도 결과가 같다.

    python scripts/add_dizziness_questions_cl_v3.py [--path compliance_rules/consultation_checklists.json] [--dry-run]
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT = os.path.join(HERE, "..", "compliance_rules", "consultation_checklists.json")
VERSION = "cl-v3"
GROUP = "dizziness"

#: 더하는 필수 질문(순서 유지). 라벨은 다른 증상군의 같은 뜻 라벨(seizure 「반복 여부」, ear_pain 「청력 저하」)과 어울리게 둔다.
NEW_QUESTIONS = [
    {"label": "지속 시간",
     "keywords": ["얼마나 지속", "얼마나 오래", "계속 지속", "한참 지속", "몇 분", "몇 시간", "수십 분", "하루 이상",
                  "가라앉", "금방 사라", "언제부터", "지속되나요"]},
    {"label": "반복 여부",
     "keywords": ["반복되", "반복적", "반복인가", "여러 번", "이전에도", "재발", "자주 그런", "처음인가", "발작적",
                  "또 생기", "자주 반복"]},
    {"label": "청력 변화",
     "keywords": ["청력", "청력 저하", "난청", "이명", "먹먹", "귀가 멍", "안 들", "잘 안 들려", "들리지 않",
                  "소리가 작게", "귀가 울"]},
]

NOTE = ("체크리스트 판 표시 행(증상군 아님). cl-v3: 어지럼 필수 질문에 지속 시간·반복 여부·청력 변화 추가(REQ-PJOV §3, "
        "2026-10-30 사용자 결정). cl-v2: 라벨 기준 동의어 키워드 보강(REQ-TICC, 2026-10-19). "
        "판정기 sv-v3 는 라벨 또는 강한 키워드 1개로 '확인' 을 센다. "
        "증상군 행만 쓰려면 symptom_key 가 있는 행을 고른다(consultation_loader.load_checklists_raw).")


def apply(data: list) -> tuple[int, int]:
    """어지럼 군에 NEW_QUESTIONS 를 라벨 기준으로 더한다(있으면 키워드만 메운다). (추가 항목 수, 추가 키워드 수)."""
    group = next((g for g in data if isinstance(g, dict) and g.get("symptom_key") == GROUP), None)
    if group is None:
        raise SystemExit(f"증상군 {GROUP} 없음")
    questions = group.setdefault("required_questions", [])
    by_label = {q.get("label"): q for q in questions}
    added_items, added_kws = 0, 0
    for new in NEW_QUESTIONS:
        cur = by_label.get(new["label"])
        if cur is None:
            questions.append({"label": new["label"], "keywords": list(new["keywords"])})
            added_items += 1
            added_kws += len(new["keywords"])
            continue
        kws = list(cur.get("keywords") or [])
        for k in new["keywords"]:
            if k not in kws:
                kws.append(k)
                added_kws += 1
        cur["keywords"] = kws
    return added_items, added_kws


def ensure_version_row(data: list, version: str):
    """목록 맨 앞에 symptom_key 없는 판 표시 행 하나. 이미 있으면 값만 맞춘다."""
    rows = [r for r in data if isinstance(r, dict) and not r.get("symptom_key") and "version" in r]
    for r in rows:
        data.remove(r)
    data.insert(0, {"version": version, "note": NOTE})


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", default=DEFAULT)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    with open(a.path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        print("list 꼴이 아닙니다:", type(data).__name__)
        return 2
    added_items, added_kws = apply(data)
    ensure_version_row(data, VERSION)
    groups = [g for g in data if isinstance(g, dict) and g.get("symptom_key")]
    rq = sum(len(g.get("required_questions") or []) for g in groups)
    dz = next(g for g in groups if g["symptom_key"] == GROUP)
    print(f"[{VERSION}] 증상군 {len(groups)} · 필수 질문 {rq} · 어지럼 추가 항목 {added_items} · 추가 키워드 {added_kws}")
    print("  어지럼 필수 질문:", " · ".join(q["label"] for q in dz["required_questions"]))
    if a.dry_run:
        return 0
    with open(a.path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("  →", os.path.relpath(a.path))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
