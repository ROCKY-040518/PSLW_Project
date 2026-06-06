import re

def fix_html(content):
    # API Settings Main Card
    content = content.replace(
        'class="bg-surface border border-outline-variant rounded-xl p-xl shadow-sm"',
        'class="bg-surface dark:bg-[#1e1e1e] border border-outline-variant dark:border-gray-800 rounded-xl p-xl shadow-sm"'
    )
    
    # Input/Select elements
    def fix_input_select(m):
        cls = m.group(1)
        # remove old ones
        cls = re.sub(r'dark:(bg|border|text)-[^\s"]+\s*', '', cls)
        cls += ' dark:bg-[#1e1e1e] dark:border-gray-800 dark:text-gray-200'
        return f'class="{cls}"'

    content = re.sub(r'<input[^>]+class="([^"]+)"', lambda m: m.group(0).replace(f'class="{m.group(1)}"', fix_input_select(m)), content)
    content = re.sub(r'<select[^>]+class="([^"]+)"', lambda m: m.group(0).replace(f'class="{m.group(1)}"', fix_input_select(m)), content)
    
    # Drop zone and cards using bg-surface-container-lowest
    def fix_lowest(m):
        cls = m.group(1)
        cls = re.sub(r'dark:(bg|border|text)-[^\s"]+\s*', '', cls)
        cls += ' dark:bg-[#1e1e1e] dark:border-gray-800 dark:text-gray-200'
        return f'class="{cls}"'
    
    content = re.sub(r'class="([^"]*bg-surface-container-lowest[^"]*)"', lambda m: m.group(0).replace(f'class="{m.group(1)}"', fix_lowest(m)), content)

    # History Table Pagination Wrapper (often border-surface-container or similar)
    content = content.replace(
        'class="px-lg py-md flex items-center justify-between border-t border-surface-container"',
        'class="px-lg py-md flex items-center justify-between border-t border-surface-container dark:border-gray-800 dark:bg-[#1e1e1e]"'
    )
    # the container holding the table
    content = content.replace(
        'class="bg-surface border border-outline-variant rounded-xl overflow-hidden shadow-sm"',
        'class="bg-surface dark:bg-[#1e1e1e] border border-outline-variant dark:border-gray-800 rounded-xl overflow-hidden shadow-sm"'
    )
    
    # Usage Toggle Wrapper
    content = content.replace(
        'class="flex items-center gap-xs bg-surface-container-low p-xs rounded-lg"',
        'class="flex items-center gap-xs bg-surface-container-low dark:bg-[#252525] p-xs rounded-lg"'
    )
    
    # Text colors inside pagination or usage that were missing
    content = content.replace('text-on-surface"', 'text-on-surface dark:text-[#f8f9fa]"')
    # clean dupes
    content = content.replace('dark:text-[#f8f9fa] dark:text-[#f8f9fa]', 'dark:text-[#f8f9fa]')
    
    # History Table cell JS
    tr_js = "tr.className = 'hover:bg-surface-bright dark:hover:bg-[#252525] border-b border-surface-container dark:border-gray-700 transition-colors group';"
    tr_js_new = "tr.className = 'hover:bg-surface-bright dark:hover:bg-[#252525] border-b border-surface-container dark:border-gray-800 transition-colors group';"
    content = content.replace(tr_js, tr_js_new)
    
    return content

with open('home.html', 'r', encoding='utf-8') as f:
    home_html = f.read()

home_html = fix_html(home_html)

with open('home.html', 'w', encoding='utf-8') as f:
    f.write(home_html)

# Extract Nav from home.html
nav_match = re.search(r'(<nav.*?</nav>)', home_html, re.DOTALL)
if nav_match:
    nav_html = nav_match.group(1)

    # Modify Nav for summary.html
    # Change switchView(...) or href="#" to href="home.html"
    nav_html = re.sub(r"onclick=\"switchView\('view-[a-z]+'\);\s*return false;\"", "", nav_html)
    nav_html = re.sub(r'href="#"', 'href="home.html"', nav_html)

    with open('summary.html', 'r', encoding='utf-8') as f:
        summary_html = f.read()

    # Replace Nav in summary.html
    summary_html = re.sub(r'<nav.*?</nav>', nav_html.replace('\\', '\\\\'), summary_html, flags=re.DOTALL)
    
    with open('summary.html', 'w', encoding='utf-8') as f:
        f.write(summary_html)

print("Fixes applied successfully!")
