import re


def build_input_code_prompt_xml(code: dict[str, str]) -> str:
    p = ""
    p += "\n"
    for name, content in code.items():
        p += f'<INPUT_CODE name="{name}">\n'
        p += f"{content}\n"
        p += f'</INPUT_CODE name="{name}">\n'
    p += "\n"
    return p


def build_input_code_prompt_md(code: dict[str, str]) -> str:
    p = ""
    p += "\n"
    for name, content in code.items():
        p += f"```{name}\n"
        p += f"{content}\n"
        p += "```\n"
    p += "\n"
    return p


def extract_code_xml_from_llm_output(llm_output: str) -> dict[str, str]:
    code = {}

    tags_matches: list[re.Match] = []
    tags_matches += re.finditer(r"<OUTPUT_CODE name=\".+\">", llm_output)
    tags_matches += re.finditer(r"</OUTPUT_CODE(\s+name=\"(?:\S+)\")?>", llm_output)

    tags = list(map(lambda x: x.group(0), tags_matches))
    tag_locs = list(map(lambda x: x.start(0), tags_matches))
    tag_lengths = [len(tag) for tag in tags]

    if len(tags) % 2 != 0:
        raise ValueError("Invalid number of tags")

    sorted_tags, sorted_tag_locs, sorted_tag_lengths = zip(
        *sorted(zip(tags, tag_locs, tag_lengths), key=lambda x: x[1])
    )

    for i in range(0, len(sorted_tags), 2):
        start = sorted_tag_locs[i] + sorted_tag_lengths[i]
        end = sorted_tag_locs[i + 1]
        name = re.findall(r"name=\"(.+)\"", sorted_tags[i])[0]
        code[name] = llm_output[start:end]

    return code


def extract_code_markdown_from_llm_outout(llm_output: str) -> dict[str, str]:
    code = {}

    tags_matches: list[re.Match] = []
    tags_matches += re.finditer(r"```(?:\S+)\n", llm_output)
    tags_matches += re.finditer(r"```\n", llm_output)

    tags = list(map(lambda x: x.group(0), tags_matches))
    tag_locs = list(map(lambda x: x.start(0), tags_matches))
    tag_lengths = [len(tag) for tag in tags]

    if len(tags) % 2 != 0:
        raise ValueError("Invalid number of tags")

    sorted_tags, sorted_tag_locs, sorted_tag_lengths = zip(
        *sorted(zip(tags, tag_locs, tag_lengths), key=lambda x: x[1])
    )

    for i in range(0, len(sorted_tags), 2):
        start = sorted_tag_locs[i] + sorted_tag_lengths[i]
        end = sorted_tag_locs[i + 1]
        name = re.findall(r"```(\S+)\n", sorted_tags[i])[0]
        code[name] = llm_output[start:end]

    return code


def extract_code_from_markdown_simple(markdown: str) -> str:
    start = markdown.find("```")
    if start == -1:
        raise ValueError("No code block found")
    end = markdown.find("```", start + 3)
    if end == -1:
        raise ValueError("No closing code block found")
    return markdown[start:end].removeprefix("```").strip()


def approx_num_tokens(text: str, char_per_token_guess: int = 3) -> int:
    return len(text) // char_per_token_guess + 1
