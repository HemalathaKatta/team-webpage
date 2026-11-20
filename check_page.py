#!/usr/bin/env python3
"""
Checks the team web page before Jenkins tags and deploys it.

1. index.html must exist
2. Every opening tag must have its matching closing tag
3. Every member listed in team.txt must have a <section id="name">
   with a heading (<h2>) and some text (<p>)

Exit code 0 = page is fine, 1 = problem found (the Jenkins build fails).
"""
import sys
from html.parser import HTMLParser

PAGE = "index.html"
TEAM_FILE = "features.txt"
# Tags that never have a closing tag
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input",
             "link", "meta", "source", "track", "wbr"}


class PageChecker(HTMLParser):
    def __init__(self):
        super().__init__()
        self.open_tags = []      # (tag, line) of tags not closed yet
        self.errors = []
        self.sections = {}       # section id -> {"h2": text, "p": text}
        self.current_section = None
        self.current_text_tag = None

    def handle_starttag(self, tag, attrs):
        if tag in VOID_TAGS:
            return
        self.open_tags.append((tag, self.getpos()[0]))
        if tag == "section":
            section_id = dict(attrs).get("id", "")
            self.current_section = section_id
            self.sections[section_id] = {"h2": "", "p": ""}
        elif tag in ("h2", "p") and self.current_section is not None:
            self.current_text_tag = tag

    def handle_endtag(self, tag):
        if tag in VOID_TAGS:
            return
        line = self.getpos()[0]
        if not self.open_tags:
            self.errors.append(f"line {line}: </{tag}> has no matching opening tag")
            return
        last_tag, last_line = self.open_tags[-1]
        if last_tag != tag:
            self.errors.append(f"line {line}: found </{tag}> but <{last_tag}> "
                               f"from line {last_line} is still open")
            # try to recover so one mistake is not reported many times
            if any(t == tag for t, _ in self.open_tags):
                while self.open_tags and self.open_tags[-1][0] != tag:
                    self.open_tags.pop()
                self.open_tags.pop()
            return
        self.open_tags.pop()
        if tag == "section":
            self.current_section = None
        if tag == self.current_text_tag:
            self.current_text_tag = None

    def handle_data(self, data):
        if self.current_section is not None and self.current_text_tag:
            self.sections[self.current_section][self.current_text_tag] += data.strip()


def main():
    try:
        with open(PAGE, encoding="utf-8") as f:
            html = f.read()
    except FileNotFoundError:
        print(f"ERROR: {PAGE} not found")
        sys.exit(1)

    with open(TEAM_FILE, encoding="utf-8") as f:
        team = [name.strip().lower() for name in f if name.strip()]

    checker = PageChecker()
    checker.feed(html)
    checker.close()
    errors = list(checker.errors)
    for tag, line in checker.open_tags:
        errors.append(f"line {line}: <{tag}> is never closed")

    print(f"Features to check: {', '.join(team)}")
    for name in team:
        section = checker.sections.get(name)
        if section is None:
            errors.append(f'section for "{name}" is missing (<section id="{name}">)')
        elif not section["h2"]:
            errors.append(f'section "{name}" has no heading (<h2>)')
        elif not section["p"]:
            errors.append(f'section "{name}" has no text (<p>)')
        else:
            print(f"  OK  {name}: {section['h2']} - {section['p']}")

    if errors:
        print("\nPAGE CHECK FAILED:")
        for error in errors:
            print("  ERROR: " + error)
        sys.exit(1)
    print("\nPAGE CHECK PASSED: all sections present and all tags closed")


if __name__ == "__main__":
    main()
