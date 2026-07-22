import re
import urllib.request
import json
import os

readme_path = r"C:\Users\ishan\Documents\Projects\Awesome-AI-Renting-Humans\README.md"

def get_stars(owner, repo):
    if not repo:
        # if it's just an org, let's just assign 0 or fetch org's repos. We'll assign 0 for now
        # Actually, let's fix the links in the README if they are orgs.
        if owner.lower() == 'fetchai': repo = 'uAgents'
        elif owner.lower() == 'valory-xyz': repo = 'open-autonomy'
        elif owner.lower() == 'daostack': repo = 'alchemy'
        elif owner.lower() == 'aragon': repo = 'aragon'
        else: return 0

    api_url = f'https://api.github.com/repos/{owner}/{repo}'
    req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return data.get('stargazers_count', 0)
    except Exception as e:
        print(f"Error fetching stars for {owner}/{repo}: {e}")
        return 0

with open(readme_path, 'r', encoding='utf-8') as f:
    content = f.read()

# The section is between "### Dedicated AI Renting Humans & Agent Marketplaces" and "### Additional Strong Open-Source Options"
# But we also have "### Additional Strong Open-Source Options" which has some repos.
# Let's extract all list items containing github links in the entire open source section.

# Find the Open-Source GitHub Projects section
start_marker = "## 💻 Open-Source GitHub Projects"
end_marker = "## How to Contribute"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print("Could not find sections")
    exit(1)

os_section = content[start_idx:end_idx]

# We need to find all list items: "- **[Name](url)** ..."
pattern = re.compile(r'- \*\*\[(.*?)\]\((https://github\.com/([^/]+)/?([^/)]+)?)\)\*\*(.*?)(?=\n- |\n\n|$)', re.DOTALL)

items = []
for match in pattern.finditer(os_section):
    name = match.group(1)
    url = match.group(2)
    owner = match.group(3)
    repo = match.group(4)
    if repo: repo = repo.strip('/')
    rest = match.group(5)
    
    stars = get_stars(owner, repo)
    
    # Construct the badge and link
    repo_path = f"{owner}/{repo}" if repo else owner
    # wait, if we mapped owner to a repo, let's use that for badge if repo was empty originally?
    # the prompt says "beside each opensource name should link to stargazers page of that particular repo"
    
    # let's just use what's in the URL
    if not repo:
        if owner.lower() == 'fetchai': repo = 'uAgents'
        elif owner.lower() == 'valory-xyz': repo = 'open-autonomy'
        elif owner.lower() == 'daostack': repo = 'alchemy'
        elif owner.lower() == 'aragon': repo = 'aragon'
        if repo:
            repo_path = f"{owner}/{repo}"
            url = f"https://github.com/{owner}/{repo}"
    
    badge = f"[![GitHub stars](https://img.shields.io/github/stars/{repo_path}?style=social&color=white)](https://github.com/{repo_path}/stargazers)"
    
    items.append({
        'name': name,
        'url': url,
        'badge': badge,
        'rest': rest,
        'stars': stars,
        'original': match.group(0)
    })

# Sort items by stars descending
items.sort(key=lambda x: x['stars'], reverse=True)

# Replace the original list with the sorted list.
# Wait, there are sub-sections: "### Dedicated AI Renting Humans & Agent Marketplaces" and "### Additional Strong Open-Source Options"
# But we can just combine them or sort them within their sections?
# "sort by that star counts (descending)" - usually implies sorting the whole list or within sections. Let's sort within sections to be safe, or just replace the whole section content. Let's do it section by section.

def process_subsection(sub_content):
    sub_items = []
    for match in pattern.finditer(sub_content):
        name = match.group(1)
        url = match.group(2)
        owner = match.group(3)
        repo = match.group(4)
        if repo: repo = repo.strip('/')
        rest = match.group(5)
        
        stars = get_stars(owner, repo)
        
        if not repo:
            if owner.lower() == 'fetchai': repo = 'uAgents'
            elif owner.lower() == 'valory-xyz': repo = 'open-autonomy'
            elif owner.lower() == 'daostack': repo = 'alchemy'
            elif owner.lower() == 'aragon': repo = 'aragon'
            if repo:
                url = f"https://github.com/{owner}/{repo}"
        
        repo_path = f"{owner}/{repo}" if repo else owner
        badge = f"[![GitHub stars](https://img.shields.io/github/stars/{repo_path}?style=social&color=white)](https://github.com/{repo_path}/stargazers)"
        
        sub_items.append({
            'stars': stars,
            'text': f"- **[{name}]({url})** {badge}{rest}"
        })
    
    sub_items.sort(key=lambda x: x['stars'], reverse=True)
    
    # Replace all matches with the sorted text. Since we want to replace the whole block of items, we'll just reconstruct the block.
    if not sub_items: return sub_content
    
    # We replace the first match to the end of the last match with the joined sorted text
    first_match = next(pattern.finditer(sub_content))
    last_match = list(pattern.finditer(sub_content))[-1]
    
    new_text = "\n\n".join(item['text'].strip() for item in sub_items)
    return sub_content[:first_match.start()] + new_text + sub_content[last_match.end():]

# Split by "### Additional Strong Open-Source Options"
parts = os_section.split("### Additional Strong Open-Source Options")
new_os_section = process_subsection(parts[0])
if len(parts) > 1:
    new_os_section += "### Additional Strong Open-Source Options" + process_subsection(parts[1])

content = content[:start_idx] + new_os_section + content[end_idx:]

with open(readme_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Done")
