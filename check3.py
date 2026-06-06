content=open('frontend/home.html', encoding='utf-8').read()
idx = content.find("7D")
print(content[max(0,idx-200):idx+200])
