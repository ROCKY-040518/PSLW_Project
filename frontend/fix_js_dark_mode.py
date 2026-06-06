import re

def process_file(content):
    # Fix the history table rendering JS
    
    # tr class
    tr_target = "tr.className = 'hover:bg-surface-bright transition-colors group';"
    tr_repl = "tr.className = 'hover:bg-surface-bright dark:hover:bg-[#252525] border-b border-surface-container dark:border-gray-700 transition-colors group';"
    content = content.replace(tr_target, tr_repl)

    # empty state message
    empty_target = '<td colspan="6" class="py-12 text-center text-on-surface-variant dark:text-[#a0a0a0]">No history available.</td>'
    empty_repl = '<td colspan="6" class="py-12 text-center text-on-surface-variant dark:text-[#cccccc]">No history available.</td>'
    content = content.replace(empty_target, empty_repl)
    
    # td elements inside innerHTML
    # Replace `<td class="... ">` to include dark mode text colors if missing
    def td_repl(m):
        cls = m.group(1)
        if 'dark:text' not in cls:
            cls += ' dark:text-[#cccccc]'
        return f'<td class="{cls}">'

    # We need to find the block containing the template literals
    # We can just apply the regex safely globally for <td class="..."> inside home.html
    # since it won't hurt to add text color to tds
    content = re.sub(r'<td class="([^"]+)">', td_repl, content)

    # Some texts might be using text-on-surface or text-on-surface-variant without dark mode inside the innerHTML
    # But wait, my previous script `add_dark_classes` actually processed all 'text-on-surface' strings.
    
    return content

with open('home.html', 'r', encoding='utf-8') as f:
    home_html = f.read()

home_html = process_file(home_html)

with open('home.html', 'w', encoding='utf-8') as f:
    f.write(home_html)

print("JS dark mode fixes applied!")
