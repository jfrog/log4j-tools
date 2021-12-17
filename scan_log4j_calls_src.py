import os
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, Set

import easyargs
from colorama import Fore, Style
from javalang import parse as parser
from javalang.parser import JavaSyntaxError
from javalang.tree import (
    ClassDeclaration,
    FieldDeclaration,
    FormalParameter,
    Import,
    Literal,
    MethodInvocation,
    ReferenceType,
    VariableDeclaration,
)
from tqdm import tqdm


@dataclass(frozen=True)
class CalleeDesc:
    class_name: str
    method_name: str


def traverse(t, visitor):
    if not hasattr(t, "children"):
        return
    for child in t.children:
        if not child:
            continue
        if isinstance(child, list):
            for item in child:
                traverse(item, visitor)
        else:
            traverse(child, visitor)
    visitor(t)


def print_file_name(filename):
    tqdm.write(Fore.RED + filename + Style.RESET_ALL)


class Scanner:
    def __init__(self, filename) -> None:

        self.filename = filename
        with open(filename) as fl:
            text = fl.read()
        self.AST = parser.parse(text)
        self.text_by_lines = text.split("\n")
        self.env: Dict[str, str] = {}
        self.call_nodes: Dict[CalleeDesc, Set[MethodInvocation]] = defaultdict(set)
        self.imports: Set[str] = set()
        self.wildcard_imports: Set[str] = set()
        self.extend_nodes: Dict[str, Set[ClassDeclaration]] = defaultdict(set)
        traverse(self.AST, self.visitor)
        self.inverted_import_names = {
            import_name.split(".")[-1]: import_name for import_name in self.imports
        }

    def lookup_type(self, name):
        if name in self.env:
            return self.env[name]
        return None

    @staticmethod
    def literal_arguments_only(call_node):
        for arg in call_node.arguments:
            if not isinstance(arg, Literal):
                return False
        return True

    def push_type_resolution(self, name, assigned_type):
        self.env[name] = assigned_type

    def visitor(self, node):
        if isinstance(node, Import):
            if node.wildcard:
                self.wildcard_imports.add(node.path)
            else:
                self.imports.add(node.path)

        elif isinstance(node, ClassDeclaration):
            if isinstance(node.extends, ReferenceType):
                self.push_type_resolution(node.name, node.extends.name)
                self.extend_nodes[node.extends.name].add(node)

        elif isinstance(node, (VariableDeclaration, FieldDeclaration)):
            for declarator in node.declarators:
                self.push_type_resolution(declarator.name, node.type.name)

        elif isinstance(node, MethodInvocation):
            relevant_type = self.lookup_type(node.qualifier)
            if relevant_type:
                self.call_nodes[CalleeDesc(relevant_type, node.member)].add(node)

        elif isinstance(node, FormalParameter):
            self.push_type_resolution(node.name, node.type.name)

    def class_name_matches(self, class_name, regex):
        if "." in class_name:
            return regex.match(class_name)
        if class_name in self.inverted_import_names:
            return regex.match(self.inverted_import_names[class_name])
        return any(
            regex.match(f"{wildcard_import}.{class_name}")
            for wildcard_import in self.wildcard_imports
        )

    def find_calls(self, class_regex_compiled, method_regex_compiled):
        for callee, call_nodes in self.call_nodes.items():
            if self.class_name_matches(
                callee.class_name, class_regex_compiled
            ) and method_regex_compiled.match(callee.method_name):

                non_constant_calls = [
                    node for node in call_nodes if not self.literal_arguments_only(node)
                ]
                if non_constant_calls:
                    yield non_constant_calls

    def find_extends(self, class_compiled_regex):
        for class_name, class_nodes in self.extend_nodes.items():
            if self.class_name_matches(class_name, class_compiled_regex):
                yield class_nodes

    def print_node_code_lines(self, nodes):
        for node in nodes:
            tqdm.write(
                Fore.GREEN
                + f"{node.position.line:5d}  "
                + Style.RESET_ALL
                + f"{self.text_by_lines[node.position.line - 1]}"
            )


def quick_match(filename, match_regex_compiled):
    txt = open(filename).read()
    return match_regex_compiled.search(txt)


def find_use_in_file(filename, root_folder, class_regex, method_regex):
    class_regex_compiled = re.compile(class_regex)
    method_regex_compiled = re.compile(method_regex)
    if not quick_match(filename, class_regex_compiled):
        return
    relative_filename = os.path.relpath(filename, root_folder)
    first = True
    extends = False
    scanner = Scanner(filename)
    for nodelist in scanner.find_calls(class_regex_compiled, method_regex_compiled):
        if first:
            print_file_name(relative_filename)
            first = False
        scanner.print_node_code_lines(nodelist)
    for nodelist in scanner.find_extends(class_regex_compiled):
        if first:
            print_file_name(relative_filename)
            first = False
        extends = True
        scanner.print_node_code_lines(nodelist)
    if extends:
        tqdm.write(
            f"{Fore.RED}!!! Warning: vulnerable class extended !!!{Style.RESET_ALL}"
        )


def traverse_folder(root_dir):
    for directory, dirs, files in os.walk(root_dir):
        for filename in files:
            if filename.endswith(".java"):
                yield os.path.join(directory, filename)


@easyargs
def scan(
    root_dir,
    class_regex=r"org.apache.logging.log4j.Logger",
    method_regex="(info|warn|error|log|debug|trace|fatal|catching|throwing|traceEntry|printf|logMessage)",
):
    parsing_failed_files = []
    for filename in tqdm(list(traverse_folder(root_dir))):
        try:
            find_use_in_file(filename, root_dir, class_regex, method_regex)
        except (IOError, JavaSyntaxError):
            parsing_failed_files.append(filename)
    if parsing_failed_files:
        with open("err.log", "w") as f:
            f.write("Parsing failed:\n" + "\n".join(parsing_failed_files))


if __name__ == "__main__":
    scan()
