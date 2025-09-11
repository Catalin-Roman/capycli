# Maintaining this Fork in sync with upstream

[[_TOC_]]

# 1. Pull changes from upstream

## 1. How it works

1. There is a pipeline scheduled once per week
2. The weekly pipeline does the following:
    1. Rebase `upstream_main` on `upstream/main`
        1. The goal is to keep an exact copy of the upstream `main` branch
        2. Note: without tags from upstream - would clober existing tags
        3. Note: we don't expect any conflicts at this stage
    2. Create a branch named `pull-from-upstream` from the `fork_main` branch
    3. Rebase `pull-from-upstream` on `upstream_main`
        1. If there are conflicts then they should be fixed locally on this branch
    4. Push the `pull-from-upstream` branch to `origin/pull-from-upstream`
        1. The push happens regardless of conflicts
        2. We use `--force` to override if the previous pull was not merged
    5. Create a Merge Request from `pull-from-upstream` to `fork_main`
    6. If the Merge Request looks good, then Merge !




## 2. Variables

| Name | Details | Default value |
|------|---------|---------------|
| GIT_AUTOMATION_NAME | Used to configure Git user.name | ${GITLAB_USER_NAME}|
| GIT_AUTOMATION_EMAIL | Used to configure Git user.email | ${GITLAB_USER_EMAIL} |
| GITHUB_COM_TOKEN | - Configured for the `upstream` remote <br/> - Used for pulling from Github (to avoid rate limits) ||
| GL_TOKEN | - Configured for the `origin` remote <br/> - Used for Git commands (e.g. git push) and Gitlab API (e.g. create Merge Request) <br/> - See [Troubleshooting](https://docs.gitlab.com/18.1/user/profile/account/two_factor_authentication_troubleshooting/#error-http-basic-access-denied-if-a-password-was-provided-for-git-authentication-) <br/> - Required scopes: api, read_repository, write_repository| |

## 3. Relevant branches

The following branches are relevant:

| Name | Details |
|------|---------|
| `fork_main` | The default branch of the fork repo (this repo) |
| `upstream_main` | Contains only the upstream code (no upstream tags, no changes done by us) |
| `pull-from-upstream` | Created from `fork_main`, it contains the changes from `upstream_main`; used as source for the Merge Request (and for fixing conflicts) |


# 2. Push changes to upstream

## 1. How it works

1. **Prerequisite**: Everything is synced:
    - the `fork_main` branch is synced with the `upstream_main` branch
    - the `upstream_main` branch is synced with `upstream/main` (see [Pull changes from upstream](#1-pull-changes-from-upstream))
2. **Prerequisite**: You need to have a GitHub account and GitHub token(s) (see [Tokens](#2-tokens))
3. Checkout a new branch from `fork_main` (e.g. `new-si-gsw-feature`) and start implementing the new feature
4. When you think the new feature is done, create the Pull Request (see [Create the Pull Request](#3-create-the-pull-request))
    1. The script checks if you already have a CaPyCLI fork in your GitHub account. If you don't, it will create one for you.
        1. *Note*: if you already have a fork, please make sure that *"This branch is up to date with sw360/capycli:main."* is displayed on it's `main` branch - meaning that your fork is in sync with the upstream
    2. The `new-si-gsw-feature` branch will be pushed to your fork
    3. The Pull Request will be created (as Draft)
5. After the Pull Request is accepted by the upstream Maintainers, pull the changes into `fork_main` (see [Pull changes from upstream](#1-pull-changes-from-upstream))

- What happens if the Maintainers of the upstream require more from you (for example: more unit test coverage) ?
    - Implement the required changes on the `new-si-gsw-feature` branch and push them to your GitHub repo. The changes will be reflected in the previously created Pull Request

- What happens is the Maintainers of the upstream don't accept your Pull Request?
    - You can merge your `new-si-gsw-feature` into `fork_main`

## 2. Tokens

In order to create the Pull Request, you need to:
- modify content (e.g. create a fork) of your GitHub repo
    - required permission: "Administration" repository permissions (write) and "Contents" repository permissions (write) (see: [official docs](https://docs.github.com/en/rest/repos/forks?apiVersion=2022-11-28#create-a-fork))
    - additionally, if the fork will be created by the script, the Workflows (write) is required
- create the Pull Request to upstream
    - required permission: "Pull requests" repository permissions (write) (see: [official docs](https://docs.github.com/en/rest/pulls/pulls?apiVersion=2022-11-28#create-a-pull-request))

If you have just one token with all required permissions, just pass it to both CLI arguments (see [Parameters](#34-parameters)).


## 3. Create the Pull Request

### 3.1 From the command line

Execute this command from the root dir of this repo with the corresponding parameters (see [Parameters](#34-parameters))

```python -m utils.create_pull_request```

### 3.2 From VSCode

The following VSCode launch configuration can be used to create the Pull Request
(for the complete list of parametes, see [Parameters](#34-parameters))

*Note*: it might be nice to first create the Pull Request to a GitHub repo you own - just as courtesy to the upstream maintainers. To achieve that, set the `--github-upstream-username` to your GitHub name.

```
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Create Pull Request",
            "type": "debugpy",
            "request": "launch",
            "module": "utils.create_pull_request",
            "console": "integratedTerminal",
            "justMyCode": false,
            "env": {},
            "args": [
                "--github-username", "<your_github_username>",
                "--github-pull-request-token", "<github_pull_request_token>",
                "--github-content-token", "<github_content_token>",
                "--github-upstream-username", "sw360",
                "--github-upstream-repo", "capycli",
                "--pull-request-branch", "<the_head_branch_of_the_pull_request>",
            ]
        }
    ]
}
```

### 3.3 From a Gitlab Pipeline

Push your branch to origin then configure and execute a Pipeline.

### 3.4 Parameters

The following table contains the list of parameters supported by the script.

| CLI Argument | Pipeline Variable | Required | Default Value | Description |
|--------------|-------------------|----------|---------------|-------------|
| `--github-username` | `GITHUB_USERNAME` | Yes | No default value | Your username on GitHub |
| `--github-pull-request-token` | `GITHUB_PULL_REQUEST_TOKEN` | Yes | No default value | GitHub token for creating the Pull Request (see [Tokens](#2-tokens)) |
| `--github-content-token` | `GITHUB_CONTENT_TOKEN` | Yes | No default value | GitHub token for accessing the repository content (see [Tokens](#2-tokens)) |
| `--pull-request-branch` | `PULL_REQUEST_BRANCH` | No | `new-si-gsw-feature` | The name of the branch to create the Pull Request from (a.k.a. the head of the Pull Request) |
| `--pull-request-title` | `PULL_REQUEST_TITLE` | No | `Pull Request from SI GSW R&D` | The title of the Pull Request |
| `--pull-request-body` | `PULL_REQUEST_BODY` | No | `This is a pull request from the SI GSW R&D team.` | The body of the Pull Request |
| `--my-github-remote` | `MY_GITHUB_REMOTE` | No | `my_github_remote` | The name of the GitHub remote to use for pushing changes |
| `--github-upstream-username` | `GITHUB_UPSTREAM_USERNAME` | No | `sw360` | The username of the upstream CaPyCLI repository |
| `--github-upstream-repo` | `GITHUB_UPSTREAM_REPO` | No | `capycli` | The name of the upstream CaPyCLI repository |
| `--reset-files` | `RESET_FILES` | No | `.gitignore`, `Readme.md`, `pyproject.toml`, `poetry.lock` | Space-separated list of files to be reset to the upstream version |
| `--remove-files` | `REMOVE_FILES` | No | `.gitlab-ci.yml`, `.gitlab/merge_request_templates/Merge Request.md`, `.pre-commit-config.yaml`, `CHANGELOG_camelot.md`, `Readme_Fork_Maintenance.md`, `release_info` | Space-separated list of files to remove from the repository |
| `--fork-upstream-main` | `FORK_UPSTREAM_MAIN` | No | `upstream_main` | The name of the branch inside our fork which tracks (is a 1:1 copy of) the upstream `main` branch |

## 4. Unit tests

If you need to modify the script which creates the Pull Request, please also update the unit tests to cover your additions.

To execute only our unit tests (with coverage) you can use this command:
```
poetry run python -m pytest --cov utils.create_pull_request --cov-report html tests/test_create_pull_request.py
```

Link to unit tests: [here](./tests/test_create_pull_request.py)

## 5. isort and flake8 in VSCode

We need to ensure that the code we want to push to upstream has been analyzied by flake8 and isort.

- Install the flake8 and isort VSCode extensions (publisher: Microsoft) and enable them
- If you're using multi-root workspaces, you can configure each folder individually by addind the `"flake8.enabled": true` line to the `.vscode/settings.json` file

*Note*: the isort settings are in the `.isort.cfg` and flake8 settings are in `tox.ini`
*Note*: the exact calls to isort and flake8 are in `.github/workflows/static-checks.yml`

# 3. Versioning

The main decision drivers that led to switching from our SemVer scheme to the CalVer versioning
convention were:
- we must ensure that we are using the CaPyCLI version that is built by our fork (this project)
- the upstream CaPyCLI is published to PyPI ([link](https://pypi.org/project/capycli/)) and PyPI is the primary source of packages
- we can't change the name of the package we are building (e.g. from *capycli* to *capycli-camelot*) because this
implies manual changes when creating Pull Request to upstream
- keeping the same version for a package with the same name but different content is not an option
- there is a time frame between the moment when we create the Pull Request and the moment it's accepted by
the upstream maintainers (it's a manual job); even if it's accepted, the maintainers might not create a
Release from it and thus no tag will be availale to us

Based on the above, we will use the CalVer versioning with the "*year.counter*" flavour.

# 4. Links
Link to upstream (on GitHub): [CaPyCLI](https://github.com/sw360/capycli)

Link to GitHub API (2022-11-28): [REST API](https://docs.github.com/en/rest?apiVersion=2022-11-28)
