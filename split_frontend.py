import re

def process_html(filename, js_filename):
    with open(f'frontend/{filename}', 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Find the script tags. We know the first one is usually for dark mode logic.
    script_matches = list(re.finditer(r'<script>(.*?)</script>', html, re.DOTALL))
    if len(script_matches) >= 2:
        # The last script tag is typically the business logic
        target_script = script_matches[-1]
        js_code = target_script.group(1).strip()
        
        # Remove BASE_URL definition from js_code as it's in config.js
        # We need to match the deployment setting comments and the const BASE_URL line
        js_code = re.sub(r'// \[DEPLOYMENT SETTING\].*?const BASE_URL = [^\n]+;\n?', '', js_code, flags=re.DOTALL | re.IGNORECASE)
        js_code = re.sub(r'const BASE_URL = [^\n]+;\n?', '', js_code, flags=re.DOTALL | re.IGNORECASE)
        
        with open(f'frontend/js/{js_filename}', 'w', encoding='utf-8') as f:
            f.write(js_code)
            
        new_script_tags = f'<script src="js/config.js"></script>\\n<script src="js/api.js"></script>\\n<script src="js/{js_filename}"></script>'
        new_html = html[:target_script.start()] + new_script_tags + html[target_script.end():]
        
        with open(f'frontend/{filename}', 'w', encoding='utf-8') as f:
            f.write(new_html)

process_html('login.html', 'login.js')
process_html('home.html', 'dashboard.js')
process_html('summary.html', 'summary_detail.js')

with open('frontend/js/config.js', 'w', encoding='utf-8') as f:
    f.write('''// [DEPLOYMENT SETTING]
// 로컬 개발 시: 'http://localhost:8000'
// 외부 접속 시: 'http://서버공인IP_또는_DDNS주소:8000' (예: 'http://my-project.iptime.org:8000')
const BASE_URL = ''; // Nginx 환경을 고려해 비워둠
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    // 로컬 환경 대체
    // BASE_URL = 'http://localhost:8000';
}
''')

with open('frontend/js/api.js', 'w', encoding='utf-8') as f:
    f.write('''// API 통신을 담당하는 공통 모듈
// 추후 fetch 로직들을 이쪽으로 추상화할 수 있습니다.
''')

print("Frontend split complete.")
