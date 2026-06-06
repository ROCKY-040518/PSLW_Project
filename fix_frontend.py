import re

# --- HOME.HTML ---
with open('frontend/home.html', 'r', encoding='utf-8') as f:
    home = f.read()

# 1. renderHistoryTable data binding & badge dark mode
old_tr = """                    <td class="py-4 px-4 font-body-sm text-body-sm text-on-surface-variant dark:text-[#cccccc]">Recent</td>
                    <td class="py-4 px-4">
                        <span class="inline-flex items-center rounded-full bg-surface-container-highest px-sm py-0.5 font-label-md text-label-md text-on-surface-variant dark:text-[#cccccc]">-</span>
                    </td>
                    <td class="py-4 px-4 font-body-sm text-body-sm text-on-surface-variant dark:text-[#cccccc]">-</td>"""

new_tr = """                    <td class="py-4 px-4 font-body-sm text-body-sm text-on-surface-variant dark:text-[#cccccc]">${item.date || 'Recent'}</td>
                    <td class="py-4 px-4">
                        <span class="inline-flex items-center rounded-full bg-surface-container-highest dark:bg-gray-800 px-sm py-0.5 font-label-md text-label-md text-on-surface-variant dark:text-gray-300">${item.provider || '-'}</span>
                    </td>
                    <td class="py-4 px-4 font-body-sm text-body-sm text-on-surface-variant dark:text-[#cccccc]">${item.type || '-'}</td>"""
home = home.replace(old_tr, new_tr)

# 2. Usage toggle buttons
home = home.replace(
    '<button class="font-label-md text-label-md text-on-surface dark:text-[#f8f9fa] bg-surface-variant px-3 py-1 rounded">7D</button>',
    '<button class="font-label-md text-label-md text-on-surface dark:text-[#f8f9fa] bg-surface-variant dark:bg-[#333333] px-3 py-1 rounded">7D</button>'
)
home = home.replace(
    '<button class="font-label-md text-label-md text-on-surface-variant dark:text-[#a0a0a0] hover:bg-surface-variant px-3 py-1 rounded transition-colors">30D</button>',
    '<button class="font-label-md text-label-md text-on-surface-variant dark:text-[#a0a0a0] hover:bg-surface-variant dark:hover:bg-[#333333] px-3 py-1 rounded transition-colors">30D</button>'
)

# 3. DOMContentLoaded Upload logic
upload_logic = """
        // URL Parameter Routing for Upload
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('action') === 'upload') {
            switchView('view-dashboard');
            setTimeout(() => {
                const fi = document.getElementById('file-input');
                if (fi) fi.click();
            }, 100);
            window.history.replaceState({}, document.title, window.location.pathname);
        }
"""
if 'action=upload' not in home:
    home = home.replace('loadSummaries();', 'loadSummaries();\n' + upload_logic)

with open('frontend/home.html', 'w', encoding='utf-8') as f:
    f.write(home)

# --- SUMMARY.HTML ---
with open('frontend/summary.html', 'r', encoding='utf-8') as f:
    summary = f.read()

summary = summary.replace('id="btn-upload-audio" onclick="window.location.href=\'home.html\';"', 'id="btn-upload-audio" onclick="window.location.href=\'home.html?action=upload\';"')

with open('frontend/summary.html', 'w', encoding='utf-8') as f:
    f.write(summary)

# --- LOGIN.HTML ---
with open('frontend/login.html', 'r', encoding='utf-8') as f:
    login = f.read()

fouc_script = """<script>
    if (localStorage.getItem('theme') === 'dark' || (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.documentElement.classList.add('dark');
    }
</script>
</head>"""
if "localStorage.getItem('theme')" not in login:
    login = login.replace('</head>', fouc_script)

login = login.replace('<body class="bg-background', '<body class="bg-background dark:bg-[#121212]')
login = login.replace('bg-surface-container-lowest border border-outline-variant', 'bg-surface-container-lowest dark:bg-[#1e1e1e] border border-outline-variant dark:border-gray-800 dark:text-gray-200')
login = login.replace('bg-surface border border-outline-variant', 'bg-surface dark:bg-[#1e1e1e] border border-outline-variant dark:border-gray-800 dark:text-gray-200')

def fix_text(s):
    # Just carefully add dark:text-[#f8f9fa] to text-on-surface
    s = s.replace('text-on-surface ', 'text-on-surface dark:text-[#f8f9fa] ')
    s = s.replace('text-on-surface"', 'text-on-surface dark:text-[#f8f9fa]"')
    s = s.replace('dark:text-[#f8f9fa] dark:text-[#f8f9fa]', 'dark:text-[#f8f9fa]')
    s = s.replace('text-on-surface-variant dark:text-[#f8f9fa]', 'text-on-surface-variant dark:text-[#a0a0a0]')
    return s

login = fix_text(login)

with open('frontend/login.html', 'w', encoding='utf-8') as f:
    f.write(login)

print("Frontend updated")
