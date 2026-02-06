from pathlib import Path
import re
import sys
import yaml


def convert_yaml_to_tex(filepath: Path):
    """
    Converts a YAML CV file back to LaTeX format.
    
    Args:
        filepath: Path to the YAML file to convert.
    """
    try:
        with open(filepath, 'r', encoding="utf8") as file:
            content_dict = yaml.safe_load(file)
    except yaml.scanner.ScannerError as e:
        print(f"Error parsing YAML file: {e}")
        print("\nThe YAML file contains syntax errors. Common issues:")
        print("  - Unquoted strings with colons (:) - these need to be in quotes")
        print("  - Unquoted strings with special characters")
        print("\nTo fix: Either manually quote problematic values or regenerate the YAML")
        print("from the original .tex file using the updated old_text_to_yaml.py script.")
        sys.exit(1)
    
    latex_lines = []
    
    for section_name, section_content in content_dict.items():
        # Check if this is a university transcript section
        if is_transcript_section(section_content):
            latex_lines.append(r"\title{University Transcript}")
            latex_lines.append(f"\\section{{{section_name}}}")
            latex_lines.append("")
            # Add transcript table
            for assignment, details in section_content.items():
                if assignment == "free_text":
                    continue
                grade = details.get("grade", "")
                duration = details.get("duration", "")
                if duration:
                    latex_lines.append(f"{assignment} & {grade} & {duration} \\\\")
                else:
                    latex_lines.append(f"{assignment} & {grade} \\\\")
            latex_lines.append("")
            continue
        
        # Regular section
        latex_lines.append(f"\\section{{{section_name}}}")
        
        # Handle list-based sections (like Participation in Conferences)
        if isinstance(section_content, list):
            for entry in section_content:
                latex_entry = format_entry(section_name, None, entry)
                latex_lines.append(latex_entry)
            latex_lines.append("")
            continue
        
        # Handle dict-based sections
        for key, value in section_content.items():
            if key == "free_text":
                # Add free text lines
                for text_line in value:
                    latex_lines.append(markdown_to_latex(text_line))
                continue
            
            # Check if this is a language entry (simple dict with 'level' key)
            if isinstance(value, dict) and "level" in value and len(value) == 1:
                level = value["level"]
                latex_lines.append(f"\\cvitemwithcomment{{{key}}}{{{level}}}{{}}")
                continue
            
            # Check if this is a subsection (list of entries)
            if isinstance(value, list):
                latex_lines.append(f"\\subsection{{{key}}}")
                for entry in value:
                    latex_entry = format_entry(section_name, key, entry)
                    latex_lines.append(latex_entry)
                continue
        
        latex_lines.append("")
    
    # Write to .tex file
    tex_filepath = filepath.with_suffix('.tex')
    with open(tex_filepath, 'w', encoding="utf8") as tex_file:
        tex_file.write('\n'.join(latex_lines))


def is_transcript_section(section_content):
    """
    Checks if a section is a university transcript section.
    
    Args:
        section_content: The content of the section.
    
    Returns:
        True if this is a transcript section, False otherwise.
    """
    if not isinstance(section_content, dict):
        return False
    
    # Check if the first entry has 'grade' key (typical of transcript)
    for key, value in section_content.items():
        if key == "free_text":
            continue
        if isinstance(value, dict) and "grade" in value:
            return True
        break
    return False


def format_entry(section_name, subsection_name, entry):
    """
    Formats a single entry as a LaTeX \\cventry command.
    
    Args:
        section_name: The name of the section.
        subsection_name: The name of the subsection (or None).
        entry: The entry data dictionary.
    
    Returns:
        A formatted LaTeX \\cventry string.
    """
    # Determine entry type based on section and subsection
    if section_name in ["Education", "Educación", "Experience", "Experiencia"]:
        return format_education_entry(entry)
    
    elif section_name in ["Production", "Producción"]:
        if subsection_name in ["Publications", "Publicaciones"]:
            return format_publication_entry(entry)
        elif subsection_name in ["Posters and Oral Presentations", "Posters y Presentaciones Orales", 
                                  "Outreach Experience", "Divulgación Científica"]:
            return format_poster_entry(entry)
        else:
            return format_education_entry(entry)
    
    elif section_name in ["Participation in Conferences and Schools", "Cursos y Congresos"]:
        return format_course_entry(entry)
    
    elif section_name in ["Languages", "Idiomas"]:
        if subsection_name in ["International Exams", "Exámenes Internacionales"]:
            return format_language_exam_entry(entry)
        else:
            return format_education_entry(entry)
    
    else:
        # Default format
        return format_education_entry(entry)


def format_education_entry(entry):
    """
    Formats an education/experience entry.
    Format: \\cventry{date}{name}{}{location}{}{description}
    """
    date = entry.get("date", "")
    name = entry.get("name", "")
    location = entry.get("location", "")
    description = entry.get("description", [])
    extras = entry.get("extras", [])
    
    # Split location if it contains a comma (sub_location, location format)
    location_parts = location.split(", ", 1)
    if len(location_parts) == 2:
        sub_location, main_location = location_parts
        cventry_parts = [date, name, sub_location, main_location]
    else:
        cventry_parts = [date, name, "", location]
    
    # Add empty field
    cventry_parts.append("")
    
    # Add description
    if isinstance(description, list):
        desc_text = format_description(description)
    else:
        desc_text = markdown_to_latex(str(description))
    cventry_parts.append(desc_text)
    
    # Add extras if present
    if extras:
        cventry_parts.extend([markdown_to_latex(str(e)) for e in extras])
    
    # Build cventry command
    formatted_parts = ["{" + markdown_to_latex(part) + "}" for part in cventry_parts]
    return "\\cventry" + "".join(formatted_parts)


def format_publication_entry(entry):
    """
    Formats a publication entry.
    Format: \\cventry{date}{title}{journal}{authors}{}{description}
    """
    date = entry.get("date", "")
    title = entry.get("title", "")
    journal = entry.get("journal", "")
    authors = entry.get("authors", "")
    description = entry.get("description", [])
    
    cventry_parts = [date, title, journal, authors, ""]
    
    # Add description
    if isinstance(description, list):
        desc_text = format_description(description)
    else:
        desc_text = markdown_to_latex(str(description))
    cventry_parts.append(desc_text)
    
    # Build cventry command
    formatted_parts = ["{" + markdown_to_latex(part) + "}" for part in cventry_parts]
    return "\\cventry" + "".join(formatted_parts)


def format_poster_entry(entry):
    """
    Formats a poster/presentation entry.
    Format: \\cventry{date}{title}{event}{authors}{}{description}
    """
    date = entry.get("date", "")
    title = entry.get("title", "")
    event = entry.get("event", "")
    authors = entry.get("authors", "")
    description = entry.get("description", [])
    
    cventry_parts = [date, title, event, authors, ""]
    
    # Add description
    if isinstance(description, list):
        desc_text = format_description(description)
    else:
        desc_text = markdown_to_latex(str(description))
    cventry_parts.append(desc_text)
    
    # Build cventry command
    formatted_parts = ["{" + markdown_to_latex(part) + "}" for part in cventry_parts]
    return "\\cventry" + "".join(formatted_parts)


def format_course_entry(entry):
    """
    Formats a course/conference entry.
    Format: \\cventry{date}{name}{extension}{location}{language}{description}
    """
    date = entry.get("date", "")
    name = entry.get("name", "")
    extension = entry.get("extension", "")
    location = entry.get("location", "")
    language = entry.get("language", "")
    description = entry.get("description", [])
    
    cventry_parts = [date, name, extension, location]
    
    # Add language field if present
    if language:
        cventry_parts.append(f"Language: {language}")
    else:
        cventry_parts.append("")
    
    # Add description
    if isinstance(description, list):
        desc_text = format_description(description)
    else:
        desc_text = markdown_to_latex(str(description))
    cventry_parts.append(desc_text)
    
    # Build cventry command
    formatted_parts = ["{" + markdown_to_latex(part) + "}" for part in cventry_parts]
    return "\\cventry" + "".join(formatted_parts)


def format_language_exam_entry(entry):
    """
    Formats a language exam entry.
    Format: \\cventry{date}{name}{}{}{}{description}
    """
    date = entry.get("date", "")
    name = entry.get("name", "")
    description = entry.get("description", [])
    
    cventry_parts = [date, name, "", "", ""]
    
    # Add description
    if isinstance(description, list):
        desc_text = format_description(description)
    else:
        desc_text = markdown_to_latex(str(description))
    cventry_parts.append(desc_text)
    
    # Build cventry command
    formatted_parts = ["{" + markdown_to_latex(part) + "}" for part in cventry_parts]
    return "\\cventry" + "".join(formatted_parts)


def format_description(description):
    """
    Formats a description list into a single string.
    
    Args:
        description: List of description strings.
    
    Returns:
        Formatted description string.
    """
    if not description:
        return ""
    
    # Join description parts with line continuation
    # Filter out empty strings to avoid issues with split descriptions
    formatted_parts = [markdown_to_latex(str(part).strip()) for part in description if str(part).strip()]
    
    if not formatted_parts:
        return ""
    elif len(formatted_parts) == 1:
        return formatted_parts[0]
    else:
        # Use \\ continuation for multi-line descriptions
        return " \\\\\n".join(formatted_parts)


def markdown_to_latex(text):
    """
    Converts Markdown formatting back to LaTeX.
    
    Args:
        text: Text with Markdown formatting.
    
    Returns:
        Text with LaTeX formatting.
    """
    # Convert markdown links: [text](url) -> \href{url}{text}
    text = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'\\href{\2}{\1}', text)
    
    # Convert bold: **text** -> \textbf{text}
    text = re.sub(r'\*\*([^\*]+)\*\*', r'\\textbf{\1}', text)
    
    # Convert italics: *text* -> \textit{text}
    # Be careful not to match bold markers
    text = re.sub(r'(?<!\*)(\*)(?!\*)([^\*]+)(?<!\*)(\*)(?!\*)', r'\\textit{\2}', text)
    
    # Convert superscript: ^text^ -> $^{text}$
    text = re.sub(r'\^([^\^]+)\^', r'$^{\1}$', text)
    
    return text


if __name__ == "__main__":
    # Specify the path to the .yaml file
    yaml_file_path = Path(sys.argv[1])
    
    # Convert the .yaml file to .tex
    convert_yaml_to_tex(yaml_file_path)
    print(f"Converted {yaml_file_path} to LaTeX format.")
