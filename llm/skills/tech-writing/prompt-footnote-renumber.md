# Prompt：脚注重新编号

## 用途
将文章脚注按正文首次出现顺序重新编号，清理孤儿脚注，排序脚注定义区。

## 操作步骤（Python 脚本）

```python
import re

with open('article.md', 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')

# Step 1: 按正文首次出现顺序收集引用编号
seen = []
seen_set = set()
for line in lines:
    if re.match(r'^\[\^\d+\]:', line.strip()):
        continue  # 跳过定义行
    for r in re.findall(r'\[\^(\d+)\]', line):
        if r not in seen_set:
            seen.append(r)
            seen_set.add(r)

old_to_new = {old: str(i) for i, old in enumerate(seen, 1)}

# Step 2: 检测孤儿脚注（定义存在但正文未引用）
def_nums = set()
for line in lines:
    m = re.match(r'^\[\^(\d+)\]:', line.strip())
    if m:
        def_nums.add(m.group(1))

orphan_defs = def_nums - seen_set
print(f"孤儿定义（将被删除）: {sorted(orphan_defs, key=int)}")
missing_defs = seen_set - def_nums
print(f"缺失定义: {sorted(missing_defs, key=int)}")

# Step 3: 删除孤儿脚注定义
for n in orphan_defs:
    content = re.sub(r'\n\[\^' + n + r'\]:[^\n]+', '', content)

# Step 4: 用 placeholder 防止双重替换
for old, new in old_to_new.items():
    content = content.replace(f'[^{old}]', f'[^RNUM{new}]')
    content = content.replace(f'[^{old}]:', f'[^RNUM{new}]:')

# Step 5: 替换 placeholder 为最终编号
for new in old_to_new.values():
    content = content.replace(f'[^RNUM{new}]', f'[^{new}]')

# Step 6: 脚注定义区按编号排序
fn_start = None
lines2 = content.split('\n')
for i, line in enumerate(lines2):
    if re.match(r'^\[\^\d+\]:', line.strip()):
        fn_start = i
        break

body = lines2[:fn_start]
fn_lines = lines2[fn_start:]

footnotes = []
current = []
for line in fn_lines:
    if re.match(r'^\[\^\d+\]:', line.strip()) and current:
        footnotes.append('\n'.join(current))
        current = [line]
    else:
        current.append(line)
if current:
    footnotes.append('\n'.join(current))

footnotes.sort(key=lambda f: int(re.match(r'\[\^(\d+)\]', f.strip()).group(1)))

content = '\n'.join(body) + '\n' + '\n'.join(footnotes)

with open('article.md', 'w', encoding='utf-8') as f:
    f.write(content)

print("完成。请验证：")
print(f"  正文引用数: {len(seen)}")
print(f"  脚注定义数: {len(footnotes)}")
```

## 注意事项
- 运行前备份原文件
- 删除孤儿定义前先确认是否是有意保留的内容
- 脚注定义区必须在文章正文之后（Markdown 标准）
