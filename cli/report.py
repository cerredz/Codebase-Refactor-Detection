import os
import json

if __name__ == "__main__":
    path = os.path.dirname(os.path.dirname(__file__))
    with open(os.path.join(path, "results.json"), "r") as file:
        results = json.load(file)
    
    print(f"\n🔍 REFACTOR ANALYSIS REPORT ({len(results)} similar regions found)\n{'='*60}")
    for i, result in enumerate(results, 1):
        print(f"\n📁 REGION {i}: {os.path.basename(result['file1'])} ↔ {os.path.basename(result['file2'])}")
        print(f"   📂 {result['file1']}")
        print(f"   📂 {result['file2']}")
        print(f"\n   🔸 FILE 1 CODE:\n{result['regions']['file1']}")
        print(f"   🔸 FILE 2 CODE:\n{result['regions']['file2']}")
        print("─" * 60)