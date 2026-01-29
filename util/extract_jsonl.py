import json
import random
from typing import List, Dict, Optional

def sample_jsonl(input_path: str,
                 output_path: Optional[str] = None,
                 sample_size: int = 100,
                 seed: int = 42,
                 allow_replacement: bool = False) -> List[Dict]:
    """
    从 `input_path` (jsonl) 随机抽取样本并返回样本对象列表。
    若指定 `output_path`，将把抽取结果写为 jsonl。
    allow_replacement 控制是否允许重复抽取同一条目。
    """
    random.seed(seed)
    items = []
    with open(input_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except Exception:
                continue

    if not items:
        return []

    if allow_replacement:
        chosen = [random.choice(items) for _ in range(sample_size)]
    else:
        if sample_size >= len(items):
            chosen = items.copy()
        else:
            chosen = random.sample(items, sample_size)

    extracted = []
    for obj in chosen:
        # 安全取值，跳过缺失 messages 或 messages 长度不足的条目
        msgs = obj.get("messages") or []
        if not isinstance(msgs, list) or len(msgs) < 2:
            continue
        text = None
        try:
            text = msgs[1].get("content")
        except Exception:
            text = None
        if not text:
            continue

        new_obj = {
                "id": obj.get("id"),
                "title": obj.get("title"),
                "text": text,
                "rates": obj.get("rates"),
                "decision": obj.get("decision"),
            }
        extracted.append(new_obj)

    if output_path:
        with open(output_path, "w", encoding="utf-8") as out:
            for o in extracted:
                out.write(json.dumps(o, ensure_ascii=False) + "\n")

    return extracted


if __name__ == "__main__":
    samples = sample_jsonl("../train.jsonl", output_path="train_extracted_sample.jsonl", sample_size=421, seed=123, allow_replacement=False)
    print(f"抽取到 {len(samples)} 条样本，已写入 `train_extracted_sample.jsonl`。")
    samples = sample_jsonl("../test.jsonl", output_path="test_extracted_sample.jsonl", sample_size=79, seed=123, allow_replacement=False)
    print(f"抽取到 {len(samples)} 条样本，已写入 `test_extracted_sample.jsonl`。")
