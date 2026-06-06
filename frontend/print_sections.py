import re

with open('home.html', 'r', encoding='utf-8') as f:
    content = f.read()

print("--- API Settings Card ---")
m = re.search(r'<section id="view-api-settings".*?</section>', content, re.DOTALL)
if m: print(m.group(0)[:800])

print("\n--- History Pagination & Input ---")
m = re.search(r'<section id="view-history".*?</section>', content, re.DOTALL)
if m:
    h_content = m.group(0)
    print("Input:", re.search(r'<input[^>]+type="text"[^>]*>', h_content).group(0))
    print("Pagination:", re.search(r'<div[^>]*>[\s\n]*<span[^>]*>Showing[^<]*</span>.*?</nav>[\s\n]*</div>', h_content, re.DOTALL).group(0))

print("\n--- Usage Toggle ---")
m = re.search(r'<section id="view-usage".*?</section>', content, re.DOTALL)
if m:
    u_content = m.group(0)
    print("Toggle:", re.search(r'<div class="flex items-center gap-xs bg-surface-container-low p-xs rounded-lg">.*?</button>\s*</div>', u_content, re.DOTALL).group(0))
