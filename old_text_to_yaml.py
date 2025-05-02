from pathlib import Path
import re
import sys
import yaml

def convert_tex_to_yaml(filepath: Path):
    with open(filepath, 'r', encoding="utf8") as file:
        lines = file.readlines()

    def make_lines_iterator():
        for line in lines:
            line = latex_bold_to_markdown(line.strip())
            line = latex_italics_to_markdown(line.strip())
            line = latex_underline_to_markdown(line.strip())
            yield line.strip()
    
    # Process the lines to extract key-value pairs
    content_dict = {}
    lines_iterator = make_lines_iterator()
    section_name = ''
    for line in lines_iterator:
        if line.startswith(r"\section"):
            section_name = line.split("{")[1].split("}")[0]
            content_dict[section_name] = {}
            continue
        
        if line.startswith(r"\cventry"):
            parts = line.split("{")[1:]
            parts = [part.split("}")[0] for part in parts]
            while line.endswith(r"\\"):
                line = next(lines_iterator)
                parts.append(line)
            
            parts = list(filter(None, parts))
            if section_name == "Education" or section_name == "Educación":
                title, content_to_save = parse_education(parts)
                content_dict[section_name][title] = content_to_save
                continue

            if len(parts) >= 4:
                date, title, location, description = parts[:4]
                content_dict[section_name][title] = {
                    "date": date.strip(),
                    "location": location.strip(),
                    "description": description.strip(),
                    "extras": parts[4:] if len(parts) > 4 else [],
                }
            continue
        
        if line and not line.startswith("\\") and not line.startswith("%"):
            if section_name in content_dict:
                content_dict[section_name].setdefault("free_text", []).append(line)
            continue

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


def latex_underline_to_markdown(latex_text: str) -> str:
    """
    Replaces LaTeX underline font commands (\textbf{...}) with Markdown bold font syntax (**...**).

    Args:
        latex_text: The LaTeX text string.

    Returns:
        The Markdown text string with underline fonts converted.
    """
    markdown_text = re.sub(r'\\underline\{(.*?)\}', r'**\1**', latex_text)
    return markdown_text


def latex_italics_to_markdown(latex_text: str) -> str:
    """
    Replaces LaTeX italics font commands (\textbf{...}) with Markdown italics font syntax (**...**).

    Args:
        latex_text: The LaTeX text string.

    Returns:
        The Markdown text string with italics fonts converted.
    """
    markdown_text = re.sub(r'\\textit\{(.*?)\}', r'*\1*', latex_text)
    return markdown_text


def parse_education(parts):
    """
    Parses the education section from the LaTeX entry.

    Args:
        parts: The parts of the LaTeX entry.

    Returns:
        A tuple containing the title and content to save.
    """
    if len(parts) >= 4:
        date, title, sub_location, location = parts[:4]
        content = {
            "date": date.strip(),
            "location": ", ".join([sub_location.strip(), location.strip()]),
            "description": parts[4:] if len(parts) > 4 else [],
        }
    elif len(parts) == 3:
        date, title, location = parts[:3]
        content = {
            "date": date.strip(),
            "location": location.strip(),
            "description": parts[2],
        }
    else:
        print("Error: Unexpected number of parts in education entry.")
        print(parts)
        raise ValueError("Unexpected number of parts in education entry.")
    return title, content


if __name__ == "__main__":
    # Specify the path to the .tex file
    tex_file_path = Path(sys.argv[1])
    
    # Convert the .tex file to .yaml
    convert_tex_to_yaml(tex_file_path)
    print(f"Converted {tex_file_path} to YAML format.")