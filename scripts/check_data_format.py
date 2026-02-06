import json

# Read first line
with open('../train.jsonl', 'r', encoding='utf-8') as f:
    line = f.readline()
    obj = json.loads(line)

print("=" * 60)
print("DATA STRUCTURE ANALYSIS")
print("=" * 60)

print("\n1. Available keys:")
for key in obj.keys():
    value = obj[key]
    if isinstance(value, (list, dict, str)):
        print(f"   - {key}: {type(value).__name__} (length: {len(value)})")
    else:
        print(f"   - {key}: {type(value).__name__} = {value}")

print("\n2. Messages structure:")
if 'messages' in obj:
    msgs = obj['messages']
    print(f"   Total messages: {len(msgs)}")
    for i, msg in enumerate(msgs[:3]):
        role = msg.get('role', 'N/A')
        content = msg.get('content', '')
        print(f"   [{i}] role={role}, content_length={len(content)}")
        if content:
            print(f"       Preview: {content[:100].strip()}...")

print("\n3. Looking for paper text...")
if 'messages' in obj:
    for i, msg in enumerate(obj['messages']):
        content = msg.get('content', '')
        if 'ABSTRACT' in content.upper()[:200]:
            print(f"   Found paper text at messages[{i}]")
            print(f"   Role: {msg.get('role')}")
            print(f"   Length: {len(content)}")
            print(f"   Preview: {content[:200]}")
            break

print("\n" + "=" * 60)

