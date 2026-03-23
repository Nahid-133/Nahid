import os
import re
import sys
import shutil

def remove_comments_from_python(code: str) -> str:
    """
    Removes full-line and inline comments from Python code by tracking quote states.

    NOTE: This line-by-line approach is complex and still fragile against Python's
    more advanced string features (like backslash escapes within strings).
    A truly robust solution requires the built-in 'ast' module.
    """
    cleaned_lines = []

    for line in code.split("\n"):
        stripped = line.strip()

        if stripped.startswith("#"):
            continue


        in_single_quotes = False
        in_double_quotes = False
        comment_start_index = -1

        for i, char in enumerate(line):
            if char in ('"', "'") and i > 0 and line[i-1] == '\\':
                continue

            if char == "'":
                if not in_double_quotes:
                    in_single_quotes = not in_single_quotes
            elif char == '"':
                if not in_single_quotes:
                    in_double_quotes = not in_double_quotes

            elif char == '#' and not in_single_quotes and not in_double_quotes:
                comment_start_index = i
                break

        if comment_start_index != -1:
            new_line = line[:comment_start_index]
        else:
            new_line = line

        new_line = new_line.rstrip()

        cleaned_lines.append(new_line)

    return "\n".join(cleaned_lines)

def process_folder(root_folder: str):
    """
    Processes the folder, removing comments from .py files and deleting __pycache__ folders.
    """
    abs_root_folder = os.path.abspath(root_folder)

    if not os.path.exists(abs_root_folder):
        print(f"🛑 Error: Folder not found at {abs_root_folder}", file=sys.stderr)
        return

    if not os.path.isdir(abs_root_folder):
        print(f"🛑 Error: Path is not a directory: {abs_root_folder}", file=sys.stderr)
        return

    print(f"Starting cleanup in: {abs_root_folder}")

    for root, dirs, files in os.walk(abs_root_folder, topdown=True):

        dirs_to_delete = []

        for d in list(dirs):
            if d == '__pycache__':
                dir_path = os.path.join(root, d)
                print(f"🧹 Removing directory: {dir_path}")
                try:
                    shutil.rmtree(dir_path)
                    dirs_to_delete.append(d)
                except OSError as e:
                    print(f"🛑 Error deleting directory {dir_path}: {e}", file=sys.stderr)

            if d.startswith(('.', 'venv', 'env')):
                 dirs_to_delete.append(d)

        dirs[:] = [d for d in dirs if d not in dirs_to_delete]

        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)

                print(f"Cleaning comments in: {file_path}")

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        original = f.read()

                    cleaned = remove_comments_from_python(original)

                    if cleaned != original:
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(cleaned)
                    else:
                        print(f"Skipped (no change): {file_path}")

                except PermissionError:
                    print(f"🛑 Error: Permission denied for file: {file_path}", file=sys.stderr)
                except FileNotFoundError:
                    print(f"🛑 Error: File not found (concurrent access?): {file_path}", file=sys.stderr)
                except OSError as e:
                    print(f"🛑 Error: OS issue with file {file_path}: {e}", file=sys.stderr)
                except Exception as e:
                    print(f"🛑 Error: An unexpected error occurred with {file_path}: {e}", file=sys.stderr)

    print("✔ Done! Cleanup and comment removal completed.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        folder_to_process = sys.argv[1]
    else:
        folder_to_process = os.getcwd()
        print(f"⚠️ No folder provided. Defaulting to current directory: {folder_to_process}")

    confirmation = input(f"WARNING: This script will modify ALL Python files and delete ALL __pycache__ folders in '{folder_to_process}'. Continue? (y/N): ").lower()

    if confirmation == 'y':
        process_folder(folder_to_process)
    else:
        print("Operation cancelled by user.")