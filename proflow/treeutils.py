import requests
import os
import pathspec
import base64


def get_tree():
    # Replace the placeholders with your actual data
    # API endpoint URL
    url = f'https://api.github.com/repos/{os.environ["GITHUB_ORG"]}/{os.environ["GITHUB_REPO"]}/git/trees/{os.environ["GITHUB_BRANCH"]}?recursive=1'
    ignore_url = f'https://api.github.com/repos/{os.environ["GITHUB_ORG"]}/{os.environ["GITHUB_REPO"]}/contents/.gitignore'

    # Headers containing the authorization token and specifying the API version
    headers = {
        'Authorization': f'Bearer {os.environ["GITHUB_KEY"]}',
        'Accept': 'application/vnd.github.v3+json'
    }

    # Download the .gitignore file
    ignore_response = requests.get(ignore_url, headers=headers)
    ignore_file_content = ''
    if ignore_response.status_code == 200:
        ignore_file_content = ignore_response.json()['content']

    # Decode and split the .gitignore file into separate rules
    ignore_rules = base64.b64decode(ignore_file_content).decode().splitlines()

    # Compile the rules to a pathspec object that can be used to match file paths
    ignore_spec = pathspec.PathSpec.from_lines('gitwildmatch', ignore_rules)

    # Make the GET request
    response = requests.get(url, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        # Extract the tree of paths from the JSON response
        tree = response.json()

        # Print the paths
        items = []
        for item in tree['tree']:
            if not ignore_spec.match_file(item['path']):
                items.append(item['path'])
        
        return items
    
    else:
        print(f'Request failed with status code {response.status_code}')

def print_tree(paths):
    tree = {}
    for path in paths:
        parts = path.split(os.sep)
        current_level = tree
        for part in parts:
            if part not in current_level:
                current_level[part] = {}
            current_level = current_level[part]

    print_tree_recursive(tree)

def print_tree_recursive(tree, indent=''):
    sorted_keys = sorted(tree.keys())
    for key in sorted_keys:
        print_tree_recursive(tree[key], indent + '|   ')

