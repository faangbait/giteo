import pytest
from git import Repo
from uuid import uuid4



@pytest.fixture
def known_repo():
    return Repo("./testrepo")


@pytest.fixture
def known_commit(known_repo):
    return known_repo.commit('079b689ce022acf4736b590951b1be0df5f4ca86')


@pytest.fixture
def known_tag():
    return 1


# @pytest.fixture
# def known_diffindex(known_commit):
#     return get_diffs_for_commit(known_commit)


@pytest.fixture
def known_string_diff_line():
    return "+export enum CACHE_FILES {"


@pytest.fixture
def file():
    return uuid4().hex + ".mp4"


def test_get_repo(known_repo):
    assert known_repo.commit(
        '079b689ce022acf4736b590951b1be0df5f4ca86').message.startswith("Create")


def test_get_commits_for_tag(known_repo, known_commit, known_tag):
    commits = get_commits_for_tag(known_repo, known_tag)
    assert commits[0] == known_commit
    assert commits[len(commits)-1].message.startswith("Testing")


# def test_get_diffs_for_commit(known_commit):
#     diff_index = get_diffs_for_commit(known_commit)
#     assert diff_index[0].a_path == "src/lib/Variables.ts"


def test_is_line_of_code():
    assert is_line_of_code("+ export const test = 'test'")
    assert is_line_of_code("- export const test = 'test'")
    assert not is_line_of_code("@@ -8,9 +8,14 @@ const ServerFuncs = {")


def test_known_diff_fixture(known_diffindex):
    assert known_diffindex[0].a_path == "src/lib/Variables.ts"
    assert known_diffindex[0].b_path == "src/lib/Variables.ts"


def test_split_diff(known_diffindex):
    for diff in known_diffindex:
        assert len(split_the_difference(diff)) > 0
    # still has whitespace
    assert len(split_the_difference(known_diffindex[0])) == 4


def test_render_diff_line(known_string_diff_line, file):
    line, color, bgcolor = render_diff_line(known_string_diff_line, 48)
    assert line == "export enum CACHE_FILES {"
    assert color == "green"

def test_render_scene(known_diffindex, file):
    scene = render_scene(known_diffindex)
    scene.output(file).overwrite_output().run()
    time.sleep(3)
    assert os.path.exists(file)
    os.unlink(file)


def test_render_tag_video(known_repo, known_tag, file):
    video = render_tag_video(known_repo, known_tag)
    video.output(file).overwrite_output().run()
    time.sleep(3)
    assert os.path.exists(file)
    os.unlink(file)
