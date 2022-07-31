import sys
from pathlib import Path
import textwrap
from git import Repo, Commit, DiffIndex, Diff, GitError
import ffmpeg
from typing import List
from PIL import Image, ImageFont, ImageDraw

PRIMARY_FONT = "/usr/share/fonts/liberation-mono/LiberationMono-Regular.ttf"
PRIMARY_CANVAS = "./assets/background-full.png"
REPOSITORY = "."
MINIMUM_COMMIT_MSG_LEN = 20 # Won't pull commits that have short messages like "bugfix"

def get_repo(repo_dir: str= REPOSITORY):
    return Repo(Path(repo_dir))


def get_commits_for_tag(repo: Repo, tag: int, branch: str = "main"):
    commits = list(repo.iter_commits(f"{tag-1}..{tag}"))
    filtered: List[Commit] = []

    for commit in commits:
        if len(commit.message) > MINIMUM_COMMIT_MSG_LEN:
            filtered.append(commit)

    filtered.reverse()
    return filtered


def is_line_of_code(line: str):
    return line.startswith("+") or line.startswith("-") or line.startswith(" ")

def text_wrap_line(line: str):
    return textwrap.wrap(line, width=125)

def bytes_to_string(probably_bytes):
    if isinstance(probably_bytes, bytes):
        return probably_bytes.decode("utf-8")
    return probably_bytes

def split_the_difference(diff: Diff, ignored_lines=[]):
    lines = []
    idx = 0
    for line in diff.diff.splitlines():
        decoded = bytes_to_string(line)
        first_char = decoded[0]
        if is_line_of_code(decoded) and len(decoded.strip("+-")) > 0:
            idx += 1
            if idx not in ignored_lines:
                # lines.append(decoded)
                wrapped = text_wrap_line(decoded[1:])
                for line in wrapped:
                    lines.append(first_char + line)
    return lines

def render_header(diff: Diff):
    header_color_bg = "darkblue"
    header_color_fg = "lightblue"

    if diff.a_mode is None and diff.a_path is None and diff.a_blob is None:
        header_color_bg = "darkgreen"
        header_color_fg = "lightgreen"
    elif diff.b_mode is None and diff.b_path is None and diff.b_blob is None:
        header_color_bg = "darkred"
        header_color_fg = "lightred"

    return header_color_fg, header_color_bg

def save_frame(canvas, commit, img_count):
    canvas.save(f"imgs/{commit.hexsha}/{img_count:09}.png")
    img_count += 1
    return img_count

def draw_frame(commit, diff, headers, footers, new_lines, removed_lines, existing_lines, img_count, ignored_lines=[]):

    with Image.open(PRIMARY_CANVAS) as canvas:
        
        canvas.load();
        fnt = ImageFont.truetype(PRIMARY_FONT, 16)
        draw = ImageDraw.Draw(canvas);
        
        # Manage the headers that will be displayed
        header_filename = diff.b_path or diff.a_pat
        header_color_fg, header_color_bg = render_header(diff)
        draw.text((30,16), header_filename, font=fnt, fill=header_color_fg, background=header_color_bg)
        draw.text((40 + len(header_filename)*10,16), "   ".join(headers), font=fnt, fill="gray")
        draw.text((30,700), footers[0], font=fnt, fill="gray")
        for lidx, line in enumerate(existing_lines):
            if line is not None and lidx not in ignored_lines:
                draw.text((30, 64+(16*(lidx-len(ignored_lines)))), line[1:], font=fnt, fill="white", escape_text=True)
        for lidx, line in enumerate(new_lines):
            if line is not None and lidx not in ignored_lines:
                draw.text((30, 64+(16*(lidx-len(ignored_lines)))), line[1:], font=fnt, fill="green", escape_text=True)
        for lidx, line in enumerate(removed_lines):
            if line is not None and lidx not in ignored_lines:
                draw.text((30, 64+(16*(lidx-len(ignored_lines)))), line[1:], font=fnt, fill="red", escape_text=True)

        return save_frame(canvas, commit, img_count)



def render_scene(commit: Commit):
    diff_index = commit.diff(commit.parents[0], create_patch=True, R=True)
    headers = []
    footers = []
    with Image.open(PRIMARY_CANVAS) as canvas:
        canvas.load();
        img_count = save_frame(canvas, commit, 0)

    for didx, diff in enumerate(diff_index):
        diff: Diff
        footers = [commit.summary]
        existing_lines = []
        new_lines = []
        removed_lines = []
        rem_or_ex_lines = []
        ignored_lines = []

        header_filename = diff.b_path or diff.a_pat

        # Get pre-existing lines and draw them to the first frame
        printable_lines = split_the_difference(diff, ignored_lines)


        for lidx, line in enumerate(printable_lines):
            if line.startswith("+"):
                new_lines.append(line)
                removed_lines.append(None)
                existing_lines.append(None)
                rem_or_ex_lines.append(None)
            elif line.startswith("-"):
                removed_lines.append(line)
                existing_lines.append(None)
                new_lines.append(None)
                rem_or_ex_lines.append(line)
            else:
                existing_lines.append(line)
                removed_lines.append(None)
                new_lines.append(None)
                rem_or_ex_lines.append(line)

        
        for i in range(32):
            img_count = draw_frame(commit, diff, headers, footers, [], [], rem_or_ex_lines, img_count, ignored_lines)
            
        for lidx, line in enumerate(printable_lines):
            if line == "":
                continue
            
            if removed_lines[lidx] is not None:
                if lidx+1 < len(printable_lines):
                    for i in range (4):
                        img_count = draw_frame(commit, diff, headers, footers, new_lines[:lidx+1], removed_lines[:lidx+2], rem_or_ex_lines, img_count, ignored_lines)
                else:
                    for i in range (4):
                        img_count = draw_frame(commit, diff, headers, footers, new_lines[:lidx+1], removed_lines[:lidx+1], rem_or_ex_lines, img_count, ignored_lines)    
                for i in range (4):
                    img_count = draw_frame(commit, diff, headers, footers, new_lines[:lidx+1], removed_lines[:lidx+1], rem_or_ex_lines, img_count, ignored_lines)
                removed_lines[lidx] = None
                rem_or_ex_lines[lidx] = None
                ignored_lines.append(lidx)
                for i in range (4):
                    img_count = draw_frame(commit, diff, headers, footers, new_lines[:lidx+1], removed_lines[:lidx+1], rem_or_ex_lines, img_count, ignored_lines)

            if new_lines[lidx] is not None:
                for i in range (len(line)):
                    next_line = line[:i+1]
                    partial_new = new_lines[:lidx]
                    partial_new.append(next_line)
                    img_count = draw_frame(commit, diff, headers, footers, partial_new, removed_lines[:lidx+1], existing_lines, img_count, ignored_lines)
                    
        for i in range(32):
            img_count = draw_frame(commit, diff, headers, footers, new_lines, removed_lines, existing_lines, img_count, ignored_lines)
        headers.insert(0, header_filename)


    return ffmpeg.input(f"imgs/{commit.hexsha}/*.png", pattern_type='glob', framerate=24)

def render_tag_video(repo: Repo, starting_tag=1, ending_tag=sys.maxsize):
    video = []
    for tag in range(starting_tag, ending_tag):
        try:
            commits = get_commits_for_tag(repo, tag)
        except GitError:
            return ffmpeg.concat(*video)
        for commit in commits:
            Path(f"imgs/{commit.hexsha}/").mkdir(parents=True, exist_ok=True)
            
            existing = Path(f"imgs/{commit.hexsha}/").iterdir();
            while existing:
                try:
                    Path(next(existing)).unlink()
                except StopIteration:
                    break
            video.append(render_scene(commit))

    return ffmpeg.concat(*video)


if __name__ == "__main__":
    all_diffs: List[Diff] = []
    all_commits: List[Commit] = []
    tags = dict()

    repo = get_repo()
    render_tag_video(repo, 1).output("output.mp4").overwrite_output().run()
