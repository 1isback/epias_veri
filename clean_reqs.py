import re

def clean_requirements(input_path, output_path):
    try:
        with open(input_path, 'r', encoding='utf-16le') as f:
            text = f.read()
    except UnicodeDecodeError:
        with open(input_path, 'r', encoding='utf-8') as f:
            text = f.read()

    lines = text.splitlines()
    clean_lines = []
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        # Remove trailing conda parts e.g., @ file://...
        line = re.sub(r'\s+@\s+.*', '', line)
        # Remove trailing =build_string for conda packages
        line = re.sub(r'=[^=]+$', '', line) if line.count('=') > 1 and '==' not in line else line
        
        clean_lines.append(line)
        
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(clean_lines))

if __name__ == '__main__':
    clean_requirements('backend/requirements.txt', 'backend/requirements_clean.txt')
