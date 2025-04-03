from pathlib import Path
import re
import sys
import yaml

def convert_tex_to_yaml(filepath: Path):
    with open(filepath, 'r', encoding="utf8") as file:
        lines = file.readlines()

    # Process the lines to extract key-value pairs
    content_dict = {}
    lines_iterator = iter(lines)
    for line in lines_iterator:
        line = latex_bold_to_markdown(line.strip())
        if line.startswith(r"\section"):
            section_name = line.split("{")[1].split("}")[0]
            content_dict[section_name] = {}
        
        if line.startswith(r"\cventry"):
            parts = line.split("{")[1:]
            parts = [part.split("}")[0] for part in parts]
            while line.endswith(r"\\"):
                line = latex_bold_to_markdown(next(lines_iterator).strip())
                parts.append(line)
            
            parts = list(filter(None, parts))
            if len(parts) >= 4:
                date, title, location, description = parts[:4]
                content_dict[section_name][title] = {
                    "date": date.strip(),
                    "location": location.strip(),
                    "description": description.strip(),
                    "extras": parts[4:] if len(parts) > 4 else [],
                }

    # Convert to YAML format
    yaml_data = yaml.dump(content_dict,
                          default_flow_style=False,
                          allow_unicode=True,
                          sort_keys=False)

    # Write to a .yaml file
    yaml_filepath = filepath.with_suffix('.yaml')
    with open(yaml_filepath, 'w', encoding="utf8") as yaml_file:
        yaml_file.write(yaml_data)


def latex_bold_to_markdown(latex_text: str) -> str:
    """
    Replaces LaTeX bold font commands (\textbf{...}) with Markdown bold font syntax (**...**).

    Args:
        latex_text: The LaTeX text string.

    Returns:
        The Markdown text string with bold fonts converted.
    """
    markdown_text = re.sub(r'\\textbf\{(.*?)\}', r'**\1**', latex_text)
    return markdown_text


if __name__ == "__main__":
    # Specify the path to the .tex file
    tex_file_path = Path(sys.argv[1])
    
    # Convert the .tex file to .yaml
    convert_tex_to_yaml(tex_file_path)
    print(f"Converted {tex_file_path} to YAML format.")