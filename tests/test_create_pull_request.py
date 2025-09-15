import pytest
from pytest import fixture, LogCaptureFixture
import requests
import sys
import logging
from unittest.mock import MagicMock, patch
from argparse import Namespace
from git.exc import InvalidGitRepositoryError, GitCommandError, NoSuchPathError
from utils.create_pull_request.git_helper import GitHelper
from utils.create_pull_request.github_helper import GitHubHelper, GitHubRepo
from utils.create_pull_request.github_helper import logger as ghh_logger
from utils.create_pull_request import __main__

DUMMY_COMMIT_SHA = 'abc123'
DUMMY_BRANCH_NAME = 'dummy-branch'

IRRELEVANT = 'irrelevant'


class TestGitHelper:
    @fixture
    def args(self) -> Namespace:
        return Namespace(
            reset_files=['file1.py', 'file2.py'],
            remove_files=['file3.py', 'file4.py'],
            my_github_remote='myremote',
            pull_request_branch='feature-branch',
            fork_upstream_main='main',
            github_upstream_username='upstreamuser',
            github_upstream_repo='upstreamrepo',
            github_username='testuser',
            github_content_token='contenttoken',
        )

    @fixture
    def mocked_repo(self) -> MagicMock:
        repo = MagicMock()
        repo.git = MagicMock()
        repo.heads = MagicMock()
        repo.working_dir = '/dummy/repo'
        repo.remotes.origin.fetch.return_value = MagicMock(name='origin', url='https://github.com/user/repo.git')
        repo.is_dirty.return_value = True
        repo.commit.return_value.hexsha = DUMMY_COMMIT_SHA
        return repo

    @patch('utils.create_pull_request.git_helper.Repo')
    def test_init_success(self, mocked_class_repo: MagicMock, args: Namespace, mocked_repo: MagicMock) -> None:
        mocked_class_repo.return_value = mocked_repo

        git_helper = GitHelper(args, IRRELEVANT)

        assert git_helper.repo == mocked_repo
        assert git_helper.reset_files == args.reset_files
        assert git_helper.files_to_remove == args.remove_files
        assert git_helper.my_github_remote == args.my_github_remote
        assert git_helper.pull_request_branch == args.pull_request_branch
        assert git_helper.fork_upstream_main == args.fork_upstream_main
        assert git_helper.github_upstream_username == args.github_upstream_username
        assert git_helper.github_upstream_repo == args.github_upstream_repo
        assert git_helper.remote_short_name == f"{args.github_username}/{args.github_upstream_repo}"

    @patch('utils.create_pull_request.git_helper.Repo', side_effect=InvalidGitRepositoryError)
    def test_init_invalid_repo(self, args: Namespace) -> None:
        git_helper = GitHelper(args, IRRELEVANT)
        assert not hasattr(git_helper, 'repo')

    @patch('utils.create_pull_request.git_helper.Repo', side_effect=NoSuchPathError)
    def test_init_invalid_repo_nosuchpatherror(self, args: Namespace) -> None:
        git_helper = GitHelper(args, IRRELEVANT)
        assert not hasattr(git_helper, 'repo')

    @patch('utils.create_pull_request.git_helper.Repo')
    def test_get_latest_commit(self, mocked_class_repo: MagicMock, args: Namespace, mocked_repo: MagicMock) -> None:
        mocked_class_repo.return_value = mocked_repo
        git_helper = GitHelper(args, IRRELEVANT)

        commit_hash = git_helper.get_latest_commit(DUMMY_BRANCH_NAME)

        assert commit_hash == DUMMY_COMMIT_SHA
        mocked_repo.commit.assert_called_with(DUMMY_BRANCH_NAME)

    @patch('utils.create_pull_request.git_helper.Repo')
    def test_reset_files_to_commit_success(self, mocked_class_repo: MagicMock, args: Namespace,
                                           mocked_repo: MagicMock) -> None:
        mocked_class_repo.return_value = mocked_repo
        mocked_repo.is_dirty.return_value = True
        git_helper = GitHelper(args, IRRELEVANT)

        result = git_helper.reset_files_to_commit(DUMMY_COMMIT_SHA)

        assert result is True
        mocked_repo.git.checkout.assert_any_call(DUMMY_COMMIT_SHA, '--', args.reset_files)
        mocked_repo.git.add.assert_called_with(args.reset_files)
        mocked_repo.git.commit.assert_called()
        mocked_repo.git.rebase.assert_called_with(args.fork_upstream_main)

    @patch('utils.create_pull_request.git_helper.Repo')
    def test_reset_files_to_commit_no_changes(self, mocked_class_repo: MagicMock, args: Namespace,
                                              mocked_repo: MagicMock) -> None:
        mocked_class_repo.return_value = mocked_repo
        mocked_repo.is_dirty.return_value = False
        git_helper = GitHelper(args, IRRELEVANT)

        result = git_helper.reset_files_to_commit(DUMMY_COMMIT_SHA)

        assert result is True
        mocked_repo.git.commit.assert_not_called()

    @patch('utils.create_pull_request.git_helper.Repo')
    def test_reset_files_to_commit_git_error(self, mocked_class_repo: MagicMock, args: Namespace,
                                             mocked_repo: MagicMock) -> None:
        mocked_class_repo.return_value = mocked_repo
        mocked_repo.git.checkout.side_effect = GitCommandError('cmd', 1)
        git_helper = GitHelper(args, IRRELEVANT)

        result = git_helper.reset_files_to_commit(DUMMY_COMMIT_SHA)

        assert result is False

    @patch('utils.create_pull_request.git_helper.Repo')
    def test_reset_files_to_commit_branch_checkout_git_error(self, mocked_class_repo: MagicMock,
                                                             args: Namespace,
                                                             mocked_repo: MagicMock) -> None:
        mocked_repo.heads.__getitem__.return_value.checkout.side_effect = GitCommandError('cmd', 1)
        mocked_class_repo.return_value = mocked_repo
        git_helper = GitHelper(args, IRRELEVANT)

        result = git_helper.reset_files_to_commit(DUMMY_COMMIT_SHA)

        assert result is False

    @patch('utils.create_pull_request.git_helper.Repo')
    def test_reset_files_to_commit_git_add_git_error(self, mocked_class_repo: MagicMock,
                                                     args: Namespace,
                                                     mocked_repo: MagicMock) -> None:
        mocked_repo.git.add.side_effect = GitCommandError('cmd', 1)
        mocked_class_repo.return_value = mocked_repo
        git_helper = GitHelper(args, IRRELEVANT)

        result = git_helper.reset_files_to_commit(DUMMY_COMMIT_SHA)

        assert result is False

    @patch('utils.create_pull_request.git_helper.Repo')
    def test_reset_files_to_commit_git_commit_git_error(self, mocked_class_repo: MagicMock,
                                                        args: Namespace,
                                                        mocked_repo: MagicMock) -> None:
        mocked_repo.git.commit.side_effect = GitCommandError('cmd', 1)
        mocked_class_repo.return_value = mocked_repo
        git_helper = GitHelper(args, IRRELEVANT)

        result = git_helper.reset_files_to_commit(DUMMY_COMMIT_SHA)

        assert result is False

    @patch('utils.create_pull_request.git_helper.Repo')
    def test_reset_files_to_commit_git_rebase_git_error(self, mocked_class_repo: MagicMock,
                                                        args: Namespace,
                                                        mocked_repo: MagicMock) -> None:
        mocked_repo.git.rebase.side_effect = GitCommandError('cmd', 1)
        mocked_class_repo.return_value = mocked_repo
        git_helper = GitHelper(args, IRRELEVANT)

        result = git_helper.reset_files_to_commit(DUMMY_COMMIT_SHA)

        assert result is False

    @patch('utils.create_pull_request.git_helper.Repo')
    @patch('utils.create_pull_request.git_helper.Path')
    def test_remove_files_success(self, mock_path: MagicMock, mocked_class_repo: MagicMock,
                                  args: Namespace,
                                  mocked_repo: MagicMock) -> None:
        mocked_class_repo.return_value = mocked_repo
        mock_path.return_value.exists.return_value = True
        mocked_repo.is_dirty.return_value = True
        git_helper = GitHelper(args, IRRELEVANT)

        result = git_helper.remove_files()

        assert result is True
        mocked_repo.git.rm.assert_any_call('file3.py')
        mocked_repo.git.rm.assert_any_call('file4.py')
        mocked_repo.git.commit.assert_called()
        mocked_repo.git.rebase.assert_called_with(args.fork_upstream_main)

    @patch('utils.create_pull_request.git_helper.Repo')
    @patch('utils.create_pull_request.git_helper.Path')
    def test_remove_files_no_changes(self, mock_path: MagicMock,
                                     mocked_class_repo: MagicMock,
                                     args: Namespace,
                                     mocked_repo: MagicMock) -> None:
        mocked_class_repo.return_value = mocked_repo
        mock_path.return_value.exists.return_value = True
        mocked_repo.is_dirty.return_value = False
        git_helper = GitHelper(args, IRRELEVANT)

        result = git_helper.remove_files()

        assert result is True
        mocked_repo.git.commit.assert_not_called()

    @patch('utils.create_pull_request.git_helper.Repo')
    def test_remove_files_branch_checkout_git_error(self, mocked_class_repo: MagicMock,
                                                    args: Namespace,
                                                    mocked_repo: MagicMock) -> None:
        mocked_repo.heads.__getitem__.return_value.checkout.side_effect = GitCommandError('cmd', 1)
        mocked_class_repo.return_value = mocked_repo
        git_helper = GitHelper(args, IRRELEVANT)

        result = git_helper.remove_files()

        assert result is False

    @patch('utils.create_pull_request.git_helper.Repo')
    def test_remove_files_git_commit_git_error(self, mocked_class_repo: MagicMock,
                                               args: Namespace,
                                               mocked_repo: MagicMock) -> None:
        mocked_repo.git.commit.side_effect = GitCommandError('cmd', 1)
        mocked_class_repo.return_value = mocked_repo
        git_helper = GitHelper(args, IRRELEVANT)

        result = git_helper.remove_files()

        assert result is False

    @patch('utils.create_pull_request.git_helper.Repo')
    @patch('utils.create_pull_request.git_helper.Path')
    def test_remove_files_git_rm_git_error(self, mock_path: MagicMock,
                                           mocked_class_repo: MagicMock,
                                           args: Namespace,
                                           mocked_repo: MagicMock) -> None:
        mocked_class_repo.return_value = mocked_repo
        mock_path.return_value.exists.return_value = True
        mocked_repo.git.rm.side_effect = GitCommandError('cmd', 1)
        git_helper = GitHelper(args, IRRELEVANT)

        result = git_helper.remove_files()

        assert result is False

    @patch('utils.create_pull_request.git_helper.Repo')
    def test_remove_files_git_rebase_git_error(self, mocked_class_repo: MagicMock,
                                               args: Namespace,
                                               mocked_repo: MagicMock) -> None:
        mocked_repo.git.rebase.side_effect = GitCommandError('cmd', 1)
        mocked_class_repo.return_value = mocked_repo
        git_helper = GitHelper(args, IRRELEVANT)

        result = git_helper.remove_files()

        assert result is False

    @patch('utils.create_pull_request.git_helper.Repo')
    def test_push_branch_to_remote_success(self, mocked_class_repo: MagicMock,
                                           args: Namespace,
                                           mocked_repo: MagicMock) -> None:
        mock_remote = MagicMock()
        mock_remote.name = args.my_github_remote
        mock_remote.push.return_value = [MagicMock(flags=0, ERROR=1, summary='push ok')]

        mocked_repo.create_remote.return_value = mock_remote
        mocked_repo.heads = {args.pull_request_branch: MagicMock()}
        mocked_repo.delete_remote.return_value = mock_remote.name

        mocked_class_repo.return_value = mocked_repo

        git_helper = GitHelper(args, IRRELEVANT)

        result = git_helper.push_branch_to_remote()

        assert result is True
        mocked_repo.create_remote.assert_called_with(args.my_github_remote,
                                                     url=(f"https://{args.github_username}:{args.github_content_token}"
                                                          f"@github.com/{git_helper.remote_short_name}.git"))
        mock_remote.push.assert_called()

    @patch('utils.create_pull_request.git_helper.Repo')
    def test_push_branch_to_remote_failed(self, mocked_class_repo: MagicMock,
                                          args: Namespace,
                                          mocked_repo: MagicMock) -> None:
        mock_remote = MagicMock()
        mock_remote.name = args.my_github_remote
        mock_remote.push.return_value = [MagicMock(flags=1, ERROR=1, summary='push failed')]

        mocked_repo.create_remote.return_value = mock_remote
        mocked_repo.heads = {args.pull_request_branch: MagicMock()}
        mocked_repo.delete_remote.return_value = mock_remote.name

        mocked_class_repo.return_value = mocked_repo

        git_helper = GitHelper(args, IRRELEVANT)

        result = git_helper.push_branch_to_remote()

        assert result is False
        mocked_repo.create_remote.assert_called_with(args.my_github_remote,
                                                     url=(f"https://{args.github_username}:{args.github_content_token}"
                                                          f"@github.com/{git_helper.remote_short_name}.git"))
        mock_remote.push.assert_called()

    @patch('utils.create_pull_request.git_helper.Repo')
    def test_push_branch_to_remote_failed_completely(self, mocked_class_repo: MagicMock,
                                                     args: Namespace,
                                                     mocked_repo: MagicMock) -> None:
        mock_remote = MagicMock()
        mock_remote.name = args.my_github_remote
        mock_remote.push.return_value = []

        mocked_repo.create_remote.return_value = mock_remote
        mocked_repo.heads = {args.pull_request_branch: MagicMock()}
        mocked_repo.delete_remote.return_value = mock_remote.name

        mocked_class_repo.return_value = mocked_repo

        git_helper = GitHelper(args, IRRELEVANT)

        result = git_helper.push_branch_to_remote()

        assert result is False
        mocked_repo.create_remote.assert_called_with(args.my_github_remote,
                                                     url=(f"https://{args.github_username}:{args.github_content_token}"
                                                          f"@github.com/{git_helper.remote_short_name}.git"))
        mock_remote.push.assert_called()

    @patch('utils.create_pull_request.git_helper.Repo')
    def test_push_branch_to_remote_git_error(self, mocked_class_repo: MagicMock,
                                             args: Namespace,
                                             mocked_repo: MagicMock) -> None:
        mock_remote = MagicMock()
        mock_remote.name = args.my_github_remote
        mock_remote.push.side_effect = GitCommandError('cmd', 1)

        mocked_repo.create_remote.return_value = mock_remote
        mocked_repo.heads = {args.pull_request_branch: MagicMock()}
        mocked_repo.delete_remote.return_value = mock_remote.name

        mocked_class_repo.return_value = mocked_repo

        git_helper = GitHelper(args, IRRELEVANT)

        result = git_helper.push_branch_to_remote()

        assert result is False
        mocked_repo.create_remote.assert_called_with(args.my_github_remote,
                                                     url=(f"https://{args.github_username}:{args.github_content_token}"
                                                          f"@github.com/{git_helper.remote_short_name}.git"))
        mock_remote.push.assert_called()

    @patch('utils.create_pull_request.git_helper.Repo')
    def test_push_branch_to_remote_exception(self, mocked_class_repo: MagicMock,
                                             args: Namespace,
                                             mocked_repo: MagicMock) -> None:
        mock_remote = MagicMock()
        mock_remote.name = args.my_github_remote
        mock_remote.push.side_effect = Exception("Unexpected error")

        mocked_repo.create_remote.return_value = mock_remote
        mocked_repo.heads = {args.pull_request_branch: MagicMock()}
        mocked_repo.delete_remote.return_value = mock_remote.name

        mocked_class_repo.return_value = mocked_repo

        git_helper = GitHelper(args, IRRELEVANT)

        result = git_helper.push_branch_to_remote()

        assert result is False
        mocked_repo.create_remote.assert_called_with(args.my_github_remote,
                                                     url=(f"https://{args.github_username}:{args.github_content_token}"
                                                          f"@github.com/{git_helper.remote_short_name}.git"))
        mock_remote.push.assert_called()

    @patch('utils.create_pull_request.git_helper.Repo')
    def test_push_branch_to_remote_remote_exists(self, mocked_class_repo: MagicMock,
                                                 args: Namespace,
                                                 mocked_repo: MagicMock) -> None:
        mock_remote = MagicMock()
        mock_remote.name = args.my_github_remote

        mocked_repo.remotes.origin.fetch.return_value = mock_remote
        mocked_repo.heads = {args.pull_request_branch: MagicMock()}

        mocked_class_repo.return_value = mocked_repo

        git_helper = GitHelper(args, IRRELEVANT)

        result = git_helper.push_branch_to_remote()

        assert result is False

    @patch('utils.create_pull_request.git_helper.Repo')
    def test_push_branch_to_remote_branch_missing(self, mocked_class_repo: MagicMock,
                                                  args: Namespace,
                                                  mocked_repo: MagicMock) -> None:
        mocked_repo.heads = {}

        mocked_class_repo.return_value = mocked_repo

        git_helper = GitHelper(args, IRRELEVANT)

        result = git_helper.push_branch_to_remote()

        assert result is False

    @patch('utils.create_pull_request.git_helper.Repo')
    def test_push_branch_to_remote_create_remote_error(self, mocked_class_repo: MagicMock,
                                                       args: Namespace,
                                                       mocked_repo: MagicMock) -> None:
        mocked_repo.create_remote.side_effect = GitCommandError('cmd', 1)
        mocked_class_repo.return_value = mocked_repo

        git_helper = GitHelper(args, IRRELEVANT)

        result = git_helper.push_branch_to_remote()

        assert result is False

    @patch('utils.create_pull_request.git_helper.Repo')
    def test_push_branch_to_remote_branch_checkout_git_error(self, mocked_class_repo: MagicMock,
                                                             args: Namespace,
                                                             mocked_repo: MagicMock) -> None:
        mocked_pull_request_branch = MagicMock()
        mocked_repo.heads = {args.pull_request_branch: mocked_pull_request_branch}
        mocked_pull_request_branch.checkout.side_effect = GitCommandError('cmd', 1)
        mocked_class_repo.return_value = mocked_repo
        git_helper = GitHelper(args, IRRELEVANT)

        result = git_helper.push_branch_to_remote()

        assert result is False

    @patch("utils.create_pull_request.git_helper.Repo")
    def test_branch_exists_true(self, mocked_class_repo: MagicMock, args: Namespace, mocked_repo: MagicMock) -> None:
        # Simulate remote refs containing the branch
        ref = MagicMock()
        ref.name = "myremote/feature-branch"
        mocked_repo.remote.return_value.refs = [ref]
        mocked_class_repo.return_value = mocked_repo

        git_helper = GitHelper(args, IRRELEVANT)
        git_helper.repo = mocked_repo

        assert git_helper.branch_exists("feature-branch", "myremote") is True

    @patch("utils.create_pull_request.git_helper.Repo")
    def test_branch_exists_false_branch_not_found(self, mocked_class_repo: MagicMock, args: Namespace,
                                                  mocked_repo: MagicMock) -> None:
        # Simulate remote refs not containing the branch
        ref = MagicMock()
        ref.name = "myremote/other-branch"
        mocked_repo.remote.return_value.refs = [ref]
        mocked_class_repo.return_value = mocked_repo

        git_helper = GitHelper(args, IRRELEVANT)
        git_helper.repo = mocked_repo

        assert git_helper.branch_exists("feature-branch", "myremote") is False

    @patch("utils.create_pull_request.git_helper.Repo")
    def test_branch_exists_empty_refs(self, mocked_class_repo: MagicMock, args: Namespace,
                                      mocked_repo: MagicMock) -> None:
        # Simulate remote refs being empty
        mocked_repo.remote.return_value.refs = []
        mocked_class_repo.return_value = mocked_repo

        git_helper = GitHelper(args, IRRELEVANT)
        git_helper.repo = mocked_repo

        assert git_helper.branch_exists("feature-branch", "myremote") is False

    @patch("utils.create_pull_request.git_helper.Repo")
    def test_branch_exists_value_error(self, mocked_class_repo: MagicMock, args: Namespace,
                                       mocked_repo: MagicMock) -> None:
        # Simulate ValueError when accessing remote
        mocked_repo.remote.side_effect = ValueError("Remote not found")
        mocked_class_repo.return_value = mocked_repo

        git_helper = GitHelper(args, IRRELEVANT)
        git_helper.repo = mocked_repo

        assert git_helper.branch_exists("feature-branch", "myremote") is False

class TestGitHubHelper:
    @fixture
    def args(self) -> Namespace:
        return Namespace(
            github_content_token="content_token",
            github_pull_request_token="pr_token",
            pull_request_branch="feature-branch",
            pull_request_title="Test PR",
            pull_request_body="This is a test PR.",
            github_username="testuser",
            github_upstream_repo="testrepo",
            github_upstream_username="upstreamuser"
        )

    @fixture
    def github_helper(self, args: Namespace) -> GitHubHelper:
        return GitHubHelper(args)

    def test_githubrepo_initialization(self) -> None:
        repo = GitHubRepo("user", "repo")
        assert repo.username == "user"
        assert repo.repo_name == "repo"
        assert repo.default_branch == "main"
        assert repo.short_name == "user/repo"
        assert repo.url_for_api == "https://api.github.com/repos/user/repo"

    @patch("utils.create_pull_request.github_helper.requests.get")
    def test_check_fork_exists_true(self, patched_requests_get: MagicMock, github_helper: GitHubHelper) -> None:
        mocked_response = MagicMock()
        mocked_response.ok = True
        mocked_response.json.return_value = {
            "fork": True,
            "parent": {"full_name": github_helper.upstream.short_name}
        }
        patched_requests_get.return_value = mocked_response

        assert github_helper.check_fork_exists() is True

    @patch("utils.create_pull_request.github_helper.requests.get")
    def test_check_fork_exists_false_invalid_json(self, patched_requests_get: MagicMock,
                                                  github_helper: GitHubHelper) -> None:
        mocked_response = MagicMock()
        mocked_response.ok = True
        mocked_response.json.side_effect = requests.JSONDecodeError("Expecting value", "", 0)
        patched_requests_get.return_value = mocked_response

        assert github_helper.check_fork_exists() is False

    @patch("utils.create_pull_request.github_helper.requests.get")
    def test_check_fork_exists_false_not_fork(self, patched_requests_get: MagicMock,
                                              github_helper: GitHubHelper) -> None:
        mocked_response = MagicMock()
        mocked_response.ok = True
        mocked_response.json.return_value = {"fork": False}

        patched_requests_get.return_value = mocked_response

        assert github_helper.check_fork_exists() is False

    @patch("utils.create_pull_request.github_helper.requests.get")
    def test_check_fork_exists_false_wrong_parent(self, patched_requests_get: MagicMock,
                                                  github_helper: GitHubHelper) -> None:
        mocked_response = MagicMock()
        mocked_response.ok = True
        mocked_response.json.return_value = {
            "fork": True,
            "parent": {"full_name": "other/repo"}
        }

        patched_requests_get.return_value = mocked_response

        assert github_helper.check_fork_exists() is False

    @patch("utils.create_pull_request.github_helper.requests.get")
    def test_check_fork_exists_false_request_failed(self, patched_requests_get: MagicMock,
                                                    github_helper: GitHubHelper) -> None:
        mocked_response = MagicMock()
        mocked_response.ok = False
        mocked_response.status_code = 404

        patched_requests_get.return_value = mocked_response

        assert github_helper.check_fork_exists() is False

    @patch("utils.create_pull_request.github_helper.requests.post")
    def test_create_fork_success(self, patched_requests_post: MagicMock, github_helper: GitHubHelper) -> None:
        mocked_response = MagicMock()
        mocked_response.ok = True

        patched_requests_post.return_value = mocked_response

        assert github_helper.create_fork() is True

    @patch("utils.create_pull_request.github_helper.requests.post")
    def test_create_fork_failure(self, patched_requests_post: MagicMock, github_helper: GitHubHelper) -> None:
        mocked_response = MagicMock()
        mocked_response.ok = False
        mocked_response.status_code = 403

        patched_requests_post.return_value = mocked_response

        assert github_helper.create_fork() is False

    @patch("utils.create_pull_request.github_helper.requests.post")
    def test_create_pull_request_success(self, patched_requests_post: MagicMock, github_helper: GitHubHelper,
                                         caplog: LogCaptureFixture) -> None:
        mocked_response = MagicMock()
        mocked_response.ok = True
        mocked_response.json.return_value = {"html_url": "http://github.com/pull/1"}

        patched_requests_post.return_value = mocked_response

        with caplog.at_level(logging.INFO, "ghh_logger"):
            ghh_logger.propagate = True
            github_helper.create_pull_request()
            ghh_logger.propagate = False

        assert "Successfully created Pull Request" in caplog.text

    @patch("utils.create_pull_request.github_helper.requests.post")
    def test_create_pull_request_failure(self, patched_requests_post: MagicMock, github_helper: GitHubHelper,
                                         caplog: LogCaptureFixture) -> None:
        mocked_response = MagicMock()
        mocked_response.ok = False
        mocked_response.status_code = 400

        patched_requests_post.return_value = mocked_response

        with caplog.at_level(logging.ERROR, "ghh_logger"):
            ghh_logger.propagate = True
            github_helper.create_pull_request()
            ghh_logger.propagate = False

        assert "Unable to create Pull Request" in caplog.text

    @patch("utils.create_pull_request.github_helper.requests.get")
    def test_get_existing_pull_requests_success(self, patched_requests_get: MagicMock,
                                                github_helper: GitHubHelper) -> None:
        mocked_response = MagicMock()
        mocked_response.ok = True
        mocked_response.json.return_value = [{"id": 1}, {"id": 2}]

        patched_requests_get.return_value = mocked_response

        prs = github_helper.get_existing_pull_requests()

        assert isinstance(prs, list)
        assert len(prs) == 2

    @patch("utils.create_pull_request.github_helper.requests.get")
    def test_get_existing_pull_requests_failure(self, patched_requests_get: MagicMock,
                                                github_helper: GitHubHelper) -> None:
        mocked_response = MagicMock()
        mocked_response.ok = False
        mocked_response.status_code = 500

        patched_requests_get.return_value = mocked_response

        prs = github_helper.get_existing_pull_requests()

        assert prs == []

    @patch.object(GitHubHelper, "get_existing_pull_requests")
    def test_pull_request_exists_true(self, mock_get_prs: MagicMock, github_helper: GitHubHelper) -> None:
        mock_get_prs.return_value = [
            {
                "state": "open",
                "head": {"ref": github_helper.pull_request_branch},
                "base": {"ref": "main"},
                "html_url": "http://github.com/pull/1"
            }
        ]
        assert github_helper.pull_request_exists() is True

    @patch.object(GitHubHelper, "get_existing_pull_requests")
    def test_pull_request_exists_false(self, mock_get_prs: MagicMock, github_helper: GitHubHelper) -> None:
        mock_get_prs.return_value = [
            {
                "state": "closed",
                "head": {"ref": github_helper.pull_request_branch},
                "base": {"ref": "main"}
            }
        ]
        assert github_helper.pull_request_exists() is False


class TestMainFunction:
    def test_parse_cli_arguments_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        test_args = [
            "prog",
            "--github-username", "testuser",
            "--github-pull-request-token", "prtoken",
            "--github-content-token", "contenttoken"
        ]
        monkeypatch.setattr(sys, "argv", test_args)
        args = __main__.parse_cli_arguments()
        assert args.github_username == "testuser"
        assert args.github_pull_request_token == "prtoken"
        assert args.github_content_token == "contenttoken"
        assert args.pull_request_branch == "new-si-gsw-feature"
        assert args.pull_request_title == "Pull Request from SI GSW R&D"
        assert args.pull_request_body == "This is a pull request from the SI GSW R&D team."
        assert args.my_github_remote == "my_github_remote"
        assert args.github_upstream_username == "sw360"
        assert args.github_upstream_repo == "capycli"
        assert args.reset_files == ['.gitignore', 'Readme.md', 'pyproject.toml', 'poetry.lock', 'Dockerfile']
        assert args.remove_files == [
            '.gitlab-ci.yml',
            '.gitlab/merge_request_templates/Merge Request.md',
            '.pre-commit-config.yaml',
            'CHANGELOG_camelot.md',
            'Readme_Fork_Maintenance.md',
            'release_info',
            'renovate.json',
            'tests/test_create_pull_request.py', 'utils/create_pull_request/*'
        ]
        assert args.fork_upstream_main == "upstream_main"

    def test_parse_cli_arguments_custom(self, monkeypatch: pytest.MonkeyPatch) -> None:
        test_args = [
            "prog",
            "--github-username", "customuser",
            "--github-pull-request-token", "customprtoken",
            "--github-content-token", "customcontenttoken",
            "--pull-request-branch", "feature-branch",
            "--pull-request-title", "Custom Title",
            "--pull-request-body", "Custom Body",
            "--my-github-remote", "custom_remote",
            "--github-upstream-username", "customupstream",
            "--github-upstream-repo", "customrepo",
            "--reset-files", "file1", "file2",
            "--remove-files", "file3", "file4",
            "--fork-upstream-main", "custom_upstream_main"
        ]
        monkeypatch.setattr(sys, "argv", test_args)
        args = __main__.parse_cli_arguments()
        assert args.github_username == "customuser"
        assert args.github_pull_request_token == "customprtoken"
        assert args.github_content_token == "customcontenttoken"
        assert args.pull_request_branch == "feature-branch"
        assert args.pull_request_title == "Custom Title"
        assert args.pull_request_body == "Custom Body"
        assert args.my_github_remote == "custom_remote"
        assert args.github_upstream_username == "customupstream"
        assert args.github_upstream_repo == "customrepo"
        assert args.reset_files == ["file1", "file2"]
        assert args.remove_files == ["file3", "file4"]
        assert args.fork_upstream_main == "custom_upstream_main"

    def test_main_workflow(self, monkeypatch: pytest.MonkeyPatch) -> None:
        test_args = [
            "prog",
            "--github-username", "testuser",
            "--github-pull-request-token", "prtoken",
            "--github-content-token", "contenttoken"
        ]
        monkeypatch.setattr(sys, "argv", test_args)
        args = __main__.parse_cli_arguments()

        with patch('utils.create_pull_request.__main__.ghh.GitHubHelper') as MockGitHubHelper, \
             patch('utils.create_pull_request.__main__.gh.GitHelper') as MockGitHelper, \
             patch('utils.create_pull_request.__main__.os.getcwd', return_value='/dummy/repo'):

            mocked_object_github_helper = MockGitHubHelper.return_value
            mocked_object_git_helper = MockGitHelper.return_value

            mocked_object_github_helper.check_fork_exists.return_value = True
            mocked_object_github_helper.pull_request_exists.return_value = False
            mocked_object_github_helper.create_pull_request.return_value = None

            mocked_object_git_helper.get_latest_commit.return_value = DUMMY_COMMIT_SHA
            mocked_object_git_helper.reset_files_to_commit.return_value = True
            mocked_object_git_helper.remove_files.return_value = True
            mocked_object_git_helper.push_branch_to_remote.return_value = True

            __main__.main()

            MockGitHubHelper.assert_called_once()
            MockGitHelper.assert_called_once()

            mocked_object_git_helper.get_latest_commit.assert_called_once_with(args.fork_upstream_main)
            mocked_object_git_helper.reset_files_to_commit.assert_called_once_with(DUMMY_COMMIT_SHA)
            mocked_object_git_helper.remove_files.assert_called_once()

            mocked_object_github_helper.check_fork_exists.assert_called_once()
            mocked_object_git_helper.push_branch_to_remote.assert_called_once()
            mocked_object_github_helper.pull_request_exists.assert_called_once()
            mocked_object_github_helper.create_pull_request.assert_called_once()
