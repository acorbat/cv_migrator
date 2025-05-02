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
            line = latex_superscript_to_markdown(line.strip())
            yield line.strip()
    
    # Process the lines to extract key-value pairs
    content_dict = {}
    lines_iterator = make_lines_iterator()
    section_name = ''
    for line in lines_iterator:
        if line.startswith(r"\title"):
            title = line.split("{")[1].split("}")[0]
            if title == "Curriculum Vitae":
                continue
            elif title == "University Transcript" or title == "Resumen de Certificado Analítico":
                for line in lines_iterator:
                    if line.startswith(r"\section"):
                        section_name = line.split("{")[1].split("}")[0]
                        content_dict[section_name] = {}
                    
                    if line.startswith("\\") or line.startswith("Assignment") or line.startswith("Asignatura") or line == "" or line.startswith("%"):
                        continue
                    
                    parts = line.rstrip("\\ \\hline").split("&")
                    assignment = parts[0].strip()
                    grade = parts[1].strip()
                    content_dict[section_name][assignment.strip()] = {"grade": grade.strip()}
                    if len(parts) == 3:
                        content_dict[section_name][assignment.strip()].update({"duration" : parts[2].strip()})
                continue

        if line.startswith(r"\section"):
            section_name = line.split("{")[1].split("}")[0]
            subsection_name = ''
            content_dict[section_name] = {}
            continue
        
        if line.startswith(r"\subsection"):
            subsection_name = line.split("{")[1].split("}")[0]
            content_dict[section_name][subsection_name] = {}
            continue

        if line.startswith(r"\cventry"):
            parts = line.split("{")[1:]
            parts = [part.split("}")[0] for part in parts]
            while line.endswith(r"\\"):
                parts[-1] = parts[-1].rstrip(r"\\")
                line = next(lines_iterator)
                parts.append(line)
            parts[-1] = parts[-1].rstrip(r"\}")
            
            parts = list(filter(None, parts))

            if section_name == "Education" or section_name == "Educación":
                title, content_to_save = parse_education(parts)
                
            elif section_name == "Experience" or section_name == "Experiencia":
                if subsection_name and subsection_name == "Teaching and Mentoring Experience" or subsection_name == "Docencia y Formación":
                    title, content_to_save = parse_education(parts)
                else:
                    title, content_to_save = parse_education(parts)
                
            elif section_name == "Production" or section_name == "Producción":
                if subsection_name and subsection_name == "Publications" or subsection_name == "Publicaciones":
                    title, content_to_save = parse_publication(parts)
                elif subsection_name and subsection_name == "Posters and Oral Presentations" or subsection_name == "Posters y Presentaciones Orales":
                    title, content_to_save = parse_poster(parts)
                elif subsection_name and subsection_name == "Outreach Experience" or subsection_name == "Divulgación Científica":
                    title, content_to_save = parse_poster(parts)
                else:
                    title, content_to_save = parse_education(parts)

            elif section_name == "Participation in Conferences and Schools" or section_name == "Cursos y Congresos":
                title, content_to_save = parse_course(parts)
            
            elif section_name == "Languages" or section_name == "Idiomas":
                if subsection_name and subsection_name == "International Exams" or subsection_name == "Exámenes Internacionales":
                    title, content_to_save = parse_language_exam(parts)
                else:
                    title, content_to_save = parse_education(parts)
                
            elif len(parts) >= 4:
                date, title, location, description = parts[:4]
                content_to_save = {
                    "date": date.strip(),
                    "location": location.strip(),
                    "description": description.strip(),
                    "extras": parts[4:] if len(parts) > 4 else [],
                }
            
            if subsection_name:
                content_dict[section_name][subsection_name][title] = content_to_save
            else:
                content_dict[section_name][title] = content_to_save
            continue
        
        if line and not line.startswith("\\") and not line.startswith("%"):
            if section_name == "Languages" or section_name == "Idiomas":
                if line.startswith(r"\cvitemwithcomment"):
                    parts = line.split("{")[1:]
                    parts = [part.split("}")[0] for part in parts]
                    parts = list(filter(None, parts))
                    if len(parts) >= 2:
                        raise ValueError("Unexpected number of parts in languages entry.")
                    content_dict[section_name][parts[0]] = {
                        "level": parts[1].strip()
                    }
            elif section_name in content_dict:
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
    Replaces LaTeX italics font commands (\textbf{...}) with Markdown italics font syntax (*...*).

    Args:
        latex_text: The LaTeX text string.

    Returns:
        The Markdown text string with italics fonts converted.
    """
    markdown_text = re.sub(r'\\textit\{(.*?)\}', r'*\1*', latex_text)
    return markdown_text


def latex_superscript_to_markdown(latex_text: str) -> str:
    """
    Replaces LaTeX superscript font commands (\textbf{...}) with Markdown superscript font syntax (^...^).

    Args:
        latex_text: The LaTeX text string.

    Returns:
        The Markdown text string with superscript fonts converted.
    """
    markdown_text = re.sub(r'\$\^\{(.*?)\}\$', r'^\1^', latex_text)
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


def parse_publication(parts):
    """
    Parses the publications subsection from the LaTeX entry.

    Args:
        parts: The parts of the LaTeX entry.

    Returns:
        A tuple containing the title and content to save.
    """
    if len(parts) >= 4:
        date, title, journal, authors = parts[:4]
        content = {
            "date": date.strip(),
            "journal": journal.strip(),
            "authors": authors.strip(),
            "description": parts[4:] if len(parts) > 4 else [],
        }
    else:
        print("Error: Unexpected number of parts in education entry.")
        print(parts)
        raise ValueError("Unexpected number of parts in education entry.")
    return title, content


def parse_poster(parts):
    """
    Parses the posters subsection from the LaTeX entry.

    Args:
        parts: The parts of the LaTeX entry.

    Returns:
        A tuple containing the title and content to save.
    """
    if len(parts) >= 4:
        date, title, event, authors = parts[:4]
        content = {
            "date": date.strip(),
            "event": event.strip(),
            "authors": authors.strip(),
            "description": parts[4:] if len(parts) > 4 else [],
        }
    else:
        print("Error: Unexpected number of parts in education entry.")
        print(parts)
        raise ValueError("Unexpected number of parts in education entry.")
    return title, content


def parse_course(parts):
    """
    Parses the courses subsection from the LaTeX entry.

    Args:
        parts: The parts of the LaTeX entry.

    Returns:
        A tuple containing the title and content to save.
    """
    if len(parts) >= 5:
        date, title, extension, location, language = parts[:5]
        content = {
            "date": date.strip(),
            "extension": extension.strip(),
            "location": location.strip(),
            "language": language.lstrip("Language: ").lstrip("Idioma: ").strip(),
            "description": parts[5:] if len(parts) > 5 else [],
        }
    elif len(parts) == 4:
        date, title, extension, location = parts[:5]
        content = {
            "date": date.strip(),
            "extension": extension.strip(),
            "location": location.strip(),
            "description": parts[5:] if len(parts) > 5 else [],
        }
    else:
        print("Error: Unexpected number of parts in education entry.")
        print(parts)
        raise ValueError("Unexpected number of parts in education entry.")
    return title, content


def parse_language_exam(parts):
    """
    Parses the languages subsection from the LaTeX entry.

    Args:
        parts: The parts of the LaTeX entry.

    Returns:
        A tuple containing the title and content to save.
    """
    if len(parts) >= 2:
        date, exam = parts[:2]
        content = {
            "date": date.strip(),
            "description": parts[2:] if len(parts) > 2 else [],
        }
    else:
        print("Error: Unexpected number of parts in languages entry.")
        print(parts)
        raise ValueError("Unexpected number of parts in languages entry.")
    return exam, content


if __name__ == "__main__":
    # Specify the path to the .tex file
    tex_file_path = Path(sys.argv[1])
    
    # Convert the .tex file to .yaml
    convert_tex_to_yaml(tex_file_path)
    print(f"Converted {tex_file_path} to YAML format.")