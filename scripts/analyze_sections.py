import json
import re

# Load first few papers and find section patterns
with open('../train.jsonl', 'r', encoding='utf-8') as f:
    for i in range(10):  # Check first 10 papers
        line = f.readline()
        if not line:
            break

        obj = json.loads(line)
        text = obj['messages'][1]['content']
        title = obj.get('title', 'Unknown')

        print(f"\n{'='*60}")
        print(f"Paper {i+1}: {title[:50]}...")
        print('='*60)

        # Look for conclusion-related sections with various formats
        patterns = [
            r'\n\s*(\d+\.?\s*)?([Cc]onclusion[s]?(?:\s+and\s+[Ff]uture\s+[Ww]ork)?)\s*\n',
            r'\n\s*(\d+\.?\s*)?([Cc]oncluding\s+[Rr]emarks?)\s*\n',
            r'\n\s*(\d+\.?\s*)?([Ss]ummary)\s*\n',
            r'\n\s*(\d+\.?\s*)?([Dd]iscussion)\s*\n',
            r'\n\s*(\d+\.?\s*)?(CONCLUSION[S]?(?:\s+(?:AND|&)\s+FUTURE\s+WORK)?)\s*\n',
        ]

        found_conclusion = False
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                print(f"Found conclusion-like sections:")
                for match in matches[:3]:  # Show first 3
                    section = match[1] if len(match) > 1 else match[0]
                    print(f"  - {section}")
                found_conclusion = True
                break

        if not found_conclusion:
            # Show any numbered section to understand format
            sections = re.findall(r'\n\s*(\d+\.?\s+[A-Z][a-zA-Z\s]{3,30})\n', text)
            if sections:
                print("Sample numbered sections:")
                for section in sections[:5]:
                    print(f"  - {section.strip()}")


