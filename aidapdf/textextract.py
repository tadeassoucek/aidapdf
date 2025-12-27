def treat_text(text: str, mode: str, strip_page_nums: bool) -> str:
    if mode == "layout2":
        return text.replace("-\n")
    else:
        return text
