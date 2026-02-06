#!/usr/bin/env python3
"""
コードリーディングの調査進捗を表示する。

表示項目:
- ドキュメント数と総行数
- 深度・確信度の分布
- コンポーネントカバレッジ
- 最近のセッション
"""

from pathlib import Path
import re


PROJECT_ROOT = Path(__file__).parent.parent
DOCS_SRC = PROJECT_ROOT / "docs" / "src"
STATE_DIR = PROJECT_ROOT / ".state"


def count_docs() -> dict:
    """ドキュメントの統計を集計する。"""
    stats = {
        "total_files": 0,
        "total_lines": 0,
        "depth": {"SHALLOW": 0, "MEDIUM": 0, "DEEP": 0, "TODO": 0},
        "confidence": {"VERIFIED": 0, "INFERRED": 0, "TODO": 0},
        "components": [],
    }

    for md_file in sorted(DOCS_SRC.rglob("*.md")):
        if md_file.name == "SUMMARY.md":
            continue
        stats["total_files"] += 1

        try:
            content = md_file.read_text(encoding="utf-8")
            stats["total_lines"] += len(content.splitlines())

            # 深度マーカーを検出
            for depth in ["SHALLOW", "MEDIUM", "DEEP", "TODO"]:
                if f"[{depth}]" in content:
                    stats["depth"][depth] += 1
                    break

            # 確信度マーカーを検出
            for conf in ["VERIFIED", "INFERRED", "TODO"]:
                if f"[{conf}]" in content:
                    stats["confidence"][conf] += 1
                    break

        except (OSError, UnicodeDecodeError):
            pass

    # コンポーネント一覧
    comp_dir = DOCS_SRC / "components"
    if comp_dir.exists():
        for d in sorted(comp_dir.iterdir()):
            if d.is_dir():
                has_summary = (d / "summary.md").exists()
                file_count = len(list(d.rglob("*.md")))
                stats["components"].append({
                    "name": d.name,
                    "has_summary": has_summary,
                    "file_count": file_count,
                })

    return stats


def get_recent_sessions(n: int = 5) -> list[dict]:
    """最近のセッション記録を取得する。"""
    sessions = []
    session_dir = STATE_DIR / "sessions"
    if not session_dir.exists():
        return sessions

    for f in sorted(session_dir.glob("*.md"), reverse=True)[:n]:
        try:
            content = f.read_text(encoding="utf-8")
            title_match = re.search(r"^# (.+)", content, re.MULTILINE)
            title = title_match.group(1) if title_match else f.stem
            sessions.append({"file": f.name, "title": title})
        except (OSError, UnicodeDecodeError):
            sessions.append({"file": f.name, "title": f.stem})

    return sessions


def get_exploration_status() -> str:
    """exploration-log.md からフェーズ進捗を取得する。"""
    log_file = STATE_DIR / "exploration-log.md"
    if not log_file.exists():
        return "（exploration-log.md が見つかりません）"

    try:
        content = log_file.read_text(encoding="utf-8")
        # フェーズ進捗の部分を抽出
        lines = []
        in_phase = False
        for line in content.splitlines():
            if "フェーズ進捗" in line or "Phase" in line.lower():
                in_phase = True
                continue
            if in_phase:
                if line.startswith("- "):
                    lines.append(line)
                elif line.startswith("---") or (line.startswith("#") and lines):
                    break
        return "\n".join(lines) if lines else "（フェーズ情報なし）"
    except (OSError, UnicodeDecodeError):
        return "（読み取りエラー）"


def main():
    stats = count_docs()

    print("=" * 50)
    print("  コードリーディング進捗レポート")
    print("=" * 50)

    # 基本統計
    print(f"\n📄 ドキュメント: {stats['total_files']} ファイル / {stats['total_lines']} 行")

    # 深度分布
    print("\n📊 深度分布:")
    for depth, count in stats["depth"].items():
        bar = "█" * count
        if count > 0:
            print(f"  {depth:8s}: {bar} ({count})")

    # 確信度分布
    print("\n🔍 確信度分布:")
    for conf, count in stats["confidence"].items():
        bar = "█" * count
        if count > 0:
            print(f"  {conf:10s}: {bar} ({count})")

    # コンポーネント
    if stats["components"]:
        print("\n📦 コンポーネント:")
        for comp in stats["components"]:
            status = "✓" if comp["has_summary"] else "○"
            print(f"  {status} {comp['name']} ({comp['file_count']} files)")

    # フェーズ進捗
    print("\n🚀 フェーズ進捗:")
    print(get_exploration_status())

    # 最近のセッション
    sessions = get_recent_sessions()
    if sessions:
        print("\n📝 最近のセッション:")
        for s in sessions:
            print(f"  - {s['file']}: {s['title']}")

    print()


if __name__ == "__main__":
    main()
