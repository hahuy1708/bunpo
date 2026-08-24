"""
    ollama pull qwen2.5:14b-instruct-q4_K_M

    python add_explanations.py --input data.json --model qwen2.5:14b-instruct-q4_K_M --batch-size 3

    # nếu muốn ghi ra file khác thay vì ghi đè file gốc:
    python add_explanations.py --input data.json --output data_full.json --model qwen2.5:14b-instruct-q4_K_M
"""

import argparse
import json
import re
import shutil
import sys
import time
import urllib.request
from pathlib import Path

# ---------------------------------------------------------------------------
# FIX CỨNG theo đúng cấu trúc dataset đã xác nhận: 195 câu, thiếu 1..95
# ---------------------------------------------------------------------------
NEEDS_EXPLANATION_INDICES = set(range(1, 96))     # index 1..95
HAS_EXPLANATION_INDICES = set(range(96, 196))     # index 96..195

FEW_SHOT = [
    {
        "index": 96,
        "full_sentence": "アメリカ政府の方針に沿い一方的に議事が進められた。",
        "choices": {"1": "に沿い", "2": "議事", "3": "一方的に", "4": "方針"},
        "explanation": "訳: Nghị sự đã được tiến hành một cách đơn phương, đúng theo phương châm của chính phủ Mỹ. 文法: N+に沿い（dựa theo, đi theo）",
    },
    {
        "index": 97,
        "full_sentence": "この町の雰囲気は昼に比べて夜がまったく違う。",
        "choices": {"1": "雰囲気", "2": "夜は", "3": "町の", "4": "昼に比べて"},
        "explanation": "訳: Bầu không khí của thị trấn này, so với ban ngày thì ban đêm hoàn toàn khác biệt. 文法: Aに比べてB（so với A thì B）",
    },
    {
        "index": 98,
        "full_sentence": "この問題について先生に聞いたところ先生もわからないそうだ。",
        "choices": {"1": "わからない", "2": "先生も", "3": "聞いたところ", "4": "先生に"},
        "explanation": "訳: Nghe nói khi hỏi thầy về vấn đề này thì thầy cũng không biết. 文法: V-た+ところ（thử làm thì）",
    },
    {
        "index": 99,
        "full_sentence": "ほんの小さなうそをきっかけにしてクラス中が大騒ぎになってしまった。",
        "choices": {"1": "きっかけにして", "2": "大騒ぎに", "3": "クラス中が", "4": "うそを"},
        "explanation": "訳: Chỉ từ một lời nói dối nhỏ mà cả lớp đã trở nên náo loạn. 文法: N+をきっかけにして（lấy làm nguyên nhân）",
    },
    {
        "index": 100,
        "full_sentence": "日本は商品価格のみならず交通費や家賃も高い。",
        "choices": {"1": "交通費や", "2": "商品価格", "3": "家賃も", "4": "のみならず"},
        "explanation": "訳: Ở Nhật Bản, không chỉ giá hàng hóa mà phí giao thông và tiền nhà cũng đắt. 文法: AのみならずBも（không chỉ A mà B cũng）",
    },
]

SYSTEM_PROMPT_TEMPLATE = """Bạn là chuyên gia ngữ pháp tiếng Nhật JLPT N2, song ngữ Nhật - Việt.
Với mỗi câu (đã có thứ tự ĐÚNG sẵn - full_sentence) và 4 lựa chọn gốc (choices) tạo nên câu đó,
nhiệm vụ của bạn KHÔNG phải là giải đố, mà là XÁC ĐỊNH cụm ngữ pháp N2 nằm trong các choices
và GIẢI THÍCH tại sao câu đúng nghĩa như vậy.

QUAN TRỌNG: Cụm ngữ pháp chính CẦN được tìm trong các "choices" được cho, không tự bịa ra mẫu khác
không xuất hiện trong câu. Nếu không chắc chắn 100% về tên mẫu ngữ pháp, hãy mô tả chức năng của nó
một cách trung thực thay vì đoán bừa một tên mẫu nghe có vẻ đúng.

Dưới đây là danh sách các mẫu ngữ pháp N2 ĐÃ ĐƯỢC XÁC NHẬN, ưu tiên dùng lại đúng các mẫu này
nếu câu chứa mẫu tương ứng (không bắt buộc, chỉ là tài liệu tham khảo):
{reference_list}

Format output cho MỖI câu (không markdown, không đánh số thêm):
<index>|||訳: <bản dịch tiếng Việt tự nhiên>. 文法: <mẫu ngữ pháp, dạng N/V+mẫu>（<nghĩa mẫu, tiếng Việt, ngắn gọn>）

Nếu câu có 2 mẫu ngữ pháp, liệt kê cả 2 phân tách bằng dấu ";" trong phần 文法.
Trả lời DUY NHẤT các dòng theo format trên, không kèm bất kỳ văn bản nào khác."""


def build_reference_list(items, cap=150):
    patterns = set()
    for it in items:
        if it.get("index") not in HAS_EXPLANATION_INDICES:
            continue
        exp = it.get("explanation") or ""
        m = re.search(r"文法[:：]\s*(.+)$", exp)
        if not m:
            continue
        for part in re.split(r"[；;]", m.group(1)):
            part = part.strip().rstrip("。.")
            if part:
                patterns.add(part)
    patterns = sorted(patterns)[:cap]
    return "\n".join(f"- {p}" for p in patterns)


def normalize_pattern_token(pattern_text):
    core = re.split(r"（|\(", pattern_text)[0]
    core = re.sub(r"^(N|V|Adj|V-る|V-た|V-ない|V-u|A|B)[\+\-]*", "", core.strip())
    return core.strip()


def build_user_prompt(batch_items):
    examples_text = "\n".join(
        f'[INDEX {ex["index"]}] full_sentence: "{ex["full_sentence"]}"\n'
        f'choices: {json.dumps(ex["choices"], ensure_ascii=False)}'
        for ex in FEW_SHOT
    )
    example_output = "\n".join(f'{ex["index"]}|||{ex["explanation"]}' for ex in FEW_SHOT)
    items_text = "\n".join(
        f'[INDEX {it["index"]}] full_sentence: "{it["full_sentence"]}"\n'
        f'choices: {json.dumps(it["choices"], ensure_ascii=False)}'
        for it in batch_items
    )
    return f"""Ví dụ mẫu:
{examples_text}

Ví dụ output đúng:
{example_output}

Bây giờ hãy tạo explanation cho {len(batch_items)} câu sau, trả về đúng {len(batch_items)} dòng:

{items_text}
"""


def extract_indexed_lines(text):
    """Parse các dòng '<index>|||<explanation>' thành dict theo index."""
    text = re.sub(r"^```\w*\s*|\s*```$", "", text.strip(), flags=re.MULTILINE)
    result = {}
    duplicate_indices = set()
    for line in text.splitlines():
        line = line.strip()
        if not line or "|||" not in line:
            continue
        left, explanation = line.split("|||", 1)
        match = re.fullmatch(r"\s*(\d+)\s*", left)
        if not match:
            continue
        index = int(match.group(1))
        explanation = explanation.strip()
        if not explanation:
            continue
        if index in result:
            duplicate_indices.add(index)
        else:
            result[index] = explanation
    if duplicate_indices:
        raise ValueError(f"Output lặp index: {sorted(duplicate_indices)}")
    return result


def call_ollama(system_prompt, user_prompt, model, host):
    payload = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "options": {"temperature": 0.2},
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{host}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=600) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["message"]["content"]


def save_progress(items, output_path, flagged, review_path):
    tmp_path = output_path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    Path(tmp_path).replace(output_path)  # ghi atomic, tránh file hỏng nếu bị ngắt giữa chừng

    tmp_review = review_path + ".tmp"
    with open(tmp_review, "w", encoding="utf-8") as f:
        json.dump(flagged, f, ensure_ascii=False, indent=2)
    Path(tmp_review).replace(review_path)


def detect_and_reset_duplicates(items):
    seen = {}
    duplicate_indices = set()
    for item in items:
        index = item.get("index")
        explanation = (item.get("explanation") or "").strip()
        if index not in NEEDS_EXPLANATION_INDICES or not explanation:
            continue
        if explanation in seen:
            duplicate_indices.update((seen[explanation], index))
        else:
            seen[explanation] = index
    for item in items:
        if item.get("index") in duplicate_indices:
            item["explanation"] = ""
    if duplicate_indices:
        print(f"CẢNH BÁO: đã xóa explanation trùng ở index {sorted(duplicate_indices)} để tạo lại.")
    return duplicate_indices


def process(items, model, host, batch_size, output_path, review_path, max_retries=3):
    reference_list = build_reference_list(items)
    known_tokens = {normalize_pattern_token(p.lstrip("- ")) for p in reference_list.split("\n") if p}
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(reference_list=reference_list or "(chưa có dữ liệu tham chiếu)")

    # Universe cố định = index 1-95. Trong đó, bỏ qua câu ĐÃ CÓ explanation
    # (từ lần chạy trước bị dừng giữa chừng) để resume, không phải "đoán".
    todo_idx = [
        i for i, it in enumerate(items)
        if it.get("index") in NEEDS_EXPLANATION_INDICES and not it.get("explanation")
    ]
    already_done = len(NEEDS_EXPLANATION_INDICES) - len(todo_idx)

    print(f"Tổng số câu trong file: {len(items)}")
    print(f"Universe cần xử lý (fix cứng index 1-95): {len(NEEDS_EXPLANATION_INDICES)}")
    if already_done:
        print(f"Đã hoàn thành sẵn từ lần chạy trước: {already_done} câu -> bỏ qua (resume)")
    print(f"Còn lại cần gọi model lần này: {len(todo_idx)}")
    print(f"Mẫu tham chiếu trích từ index 96-195: {len(known_tokens)}\n")

    flagged_by_index = {}
    if Path(review_path).exists():
        try:
            with open(review_path, "r", encoding="utf-8") as f:
                for item in json.load(f):
                    if item.get("index") in NEEDS_EXPLANATION_INDICES:
                        flagged_by_index[item["index"]] = item
        except (OSError, json.JSONDecodeError):
            print(f"CẢNH BÁO: không đọc được review cũ: {review_path}")

    for start in range(0, len(todo_idx), batch_size):
        batch_idx = todo_idx[start:start + batch_size]
        remaining = list(batch_idx)

        for attempt in range(1, max_retries + 1):
            if not remaining:
                break
            try:
                batch_items = [items[i] for i in remaining]
                user_prompt = build_user_prompt(batch_items)
                raw = call_ollama(system_prompt, user_prompt, model, host)
                explanations = extract_indexed_lines(raw)
                expected = {items[idx]["index"] for idx in remaining}
                unexpected = set(explanations) - expected
                if unexpected:
                    raise ValueError(f"Output chứa index không được yêu cầu: {sorted(unexpected)}")
                newly_done = []
                for idx in remaining:
                    item_index = items[idx]["index"]
                    if item_index not in explanations:
                        continue
                    exp = explanations[item_index]
                    items[idx]["explanation"] = exp
                    newly_done.append(idx)

                    m = re.search(r"文法[:：]\s*(.+)$", exp)
                    is_known = False
                    if m:
                        for part in re.split(r"[；;]", m.group(1)):
                            token = normalize_pattern_token(part)
                            if token and any(token in k or k in token for k in known_tokens):
                                is_known = True
                                break
                    if not is_known:
                        flagged_by_index[item_index] = {
                            "index": item_index,
                            "full_sentence": items[idx]["full_sentence"],
                            "explanation": exp,
                            "reason": "Mẫu ngữ pháp không khớp danh sách tham chiếu -> nên tự kiểm tra lại",
                        }
                    else:
                        flagged_by_index.pop(item_index, None)

                remaining = [idx for idx in remaining if idx not in newly_done]
                if newly_done:
                    save_progress(items, output_path, list(flagged_by_index.values()), review_path)
                    print(f"  ✓ Batch {start // batch_size + 1} (lần {attempt}): xong index "
                          f"{[items[idx]['index'] for idx in newly_done]} (đã lưu đĩa)")
                if remaining:
                    print(f"  … còn thiếu index {[items[idx]['index'] for idx in remaining]}, thử lại..." )
            except Exception as e:
                print(f"  ✗ Batch {start // batch_size + 1} lỗi lần {attempt}: {e}")
            if remaining and attempt < max_retries:
                time.sleep(2 * attempt)
        if remaining:
            print(f"  ✗ Bỏ qua index {[items[idx]['index'] for idx in remaining]} sau {max_retries} lần thử.")
        time.sleep(0.3)

    return items, list(flagged_by_index.values())


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", required=True, help="File JSON gốc (195 câu)")
    parser.add_argument("--output", default=None,
                         help="Mặc định: GHI ĐÈ thẳng vào --input. Chỉ định khác nếu muốn giữ file gốc nguyên vẹn.")
    parser.add_argument("--model", default="qwen2.5:14b-instruct-q4_K_M")
    parser.add_argument("--ollama-host", default="http://localhost:11434")
    parser.add_argument("--batch-size", type=int, default=3)
    parser.add_argument("--force-indices", default=None,
                        help="Danh sách index cần tạo lại, ví dụ: --force-indices 10,12")
    args = parser.parse_args()

    output_path = args.output or args.input
    in_place = (output_path == args.input)

    backup_path = args.input + ".bak"
    if in_place and not Path(backup_path).exists():
        shutil.copy2(args.input, backup_path)
        print(f"Đã tạo backup an toàn: {backup_path} (chỉ tạo 1 lần)")

    with open(args.input, "r", encoding="utf-8") as f:
        items = json.load(f)

    if args.force_indices:
        force_indices = {int(value.strip()) for value in args.force_indices.split(",") if value.strip()}
        for item in items:
            if item.get("index") in force_indices:
                item["explanation"] = ""
        print(f"Đã ép tạo lại explanation cho index: {sorted(force_indices)}")

    review_path = output_path + ".needs_review.json"

    detect_and_reset_duplicates(items)

    items, flagged = process(
        items, model=args.model, host=args.ollama_host, batch_size=args.batch_size,
        output_path=output_path, review_path=review_path,
    )

    duplicate_indices = detect_and_reset_duplicates(items)
    if duplicate_indices:
        save_progress(items, output_path, flagged, review_path)

    still_missing = [it.get("index") for it in items
                      if it.get("index") in NEEDS_EXPLANATION_INDICES and not it.get("explanation")]
    print(f"\nHoàn tất -> {output_path}" + (" (ghi đè file gốc)" if in_place else ""))
    if still_missing:
        print(f"Còn thiếu explanation ở index: {still_missing} -> chạy lại đúng lệnh này để resume.")
    else:
        print("Đã điền đủ explanation cho toàn bộ index 1-95 ✓")
    print(f"Cần tự kiểm tra tay ({len(flagged)} câu): {review_path}")


if __name__ == "__main__":
    main()