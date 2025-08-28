# Maintaining this Fork in sync with upstream

[[_TOC_]]

# 1. Pull changes from upstream

## 1. How it works

1. There is a pipeline scheduled once per week
2. The weekly pipeline does the following:
    1. Merge the `upstream/main` into `upstream_main`
        1. The goal is to keep an exact copy of the upstream main branch
        2. Note: without tags from upstream - would clober existing tags
        3. Note: we don't expect any conflicts at this stage
    2. Create a branch named `pull-from-upstream` from the `fork_main` branch
    3. Merge `upstream_main` into `pull-from-upstream`
        1. If there are conflicts then they should be fixed locally on this branch
    4. Push the `pull-from-upstream` branch to `origin/pull-from-upstream`
        1. The push happens regardless of conflicts
        2. We use `--force` to override if the previous pull was not merged
    5. Create a Merge Request from `pull-from-upstream` to `fork_main`
    6. If the Merge Request looks good, then Merge !

## 2. Required variables
The synchronization of this fork with the upstream project requires the following variables:

| Name | Details | Default value |
|------|---------|---------------|
| GIT_AUTOMATION_NAME | Used to configure Git user.name | git-automation-name|
| GIT_AUTOMATION_EMAIL | Used to configure Git user.email | git-automation-email |
| GIT_AUTOMATION_TOKEN |  - Used as the token for Git commands (e.g. git push) and Gitlab API (e.g. create Merge Request) <br/> - It's a Personal Access Token, see [Troubleshooting](https://docs.gitlab.com/18.1/user/profile/account/two_factor_authentication_troubleshooting/#error-http-basic-access-denied-if-a-password-was-provided-for-git-authentication-) <br/> - Required scopes: api, read_repository, write_repository| |

## 3. Relevant branches

The following branches are relevant:

| Name | Details |
|------|---------|
| `fork_main` | The default branch of the fork repo (this repo) |
| `upstream_main` | Contains only the upstream code (no upstream tags, no changes done by us) |
| `pull-from-upstream` | Created from `fork_main`, it contains the changes from `upstream_main`; used as source for the Merge Request (and for fixing conflicts) |


# 2. Push changes to upstream

## 1. How it works

1. **Prerequisite**: Everything is synced: the `fork_main` branch is synced with the `upstream_main` branch which is synced with `upstream/main`
2. **Prerequisite**: You need to have a GitHub account and a GitHub token
3. Checkout a new branch from `fork_main` (e.g. `new-si-gsw-feature`) and start implementing the new feature
4. When you think the new feature is done, create the Pull Request (see [Create the Pull Request](#5-create-the-pull-request))
    1. The script checks if you already have a CaPyCLI fork in your GitHub account. If you don't, it will create one for you.
    2. The `new-si-gsw-feature` branch will be pushed to your fork
    3. The Pull Request will be created
5. After the Pull Request is acceptedby the upstream Maintainers, pull the changes into `fork_main` (see [Pull changes from upstream](#1-pull-changes-from-upstream))

- What happens if the Maintainers of the upstream require more from you (for example: more unit test coverage) ?
    - Implement the required changes on the `new-si-gsw-feature` branch and push them to your GitHub repo. The changes will be reflected in the previously created Pull Request

- What happens is the Maintainers of the upstream don't accept your Pull Request?
    - You can merge your `new-si-gsw-feature` into `fork_main`

## 2. Variables

TODO

| Name | Default | Details |
|------|---------|---------|
| PULL_REQUEST_BRANCH | create-pull-request | The name of the branch containing the code we want to be pushed to upstream |
| PULL_REQUEST_TITLE | Pull Request from SI GSW R&D | The default title of the Pull Request |
| PULL_REQUEST_BODY | This Pull Request was created by SI GSW R&D. | The default description of the Pull Request |
| GITHUB_CONTENT_TOKEN | No default value | The token to be used for pushing the `create-pull-request` branch to the intermediate Github repo <br/> Required Scopes: Contents (Read and write), Workflows (Read and write) only if the intermediate Github repo is empty |
| GITHUB_PULL_REQUEST_TOKEN | No default value | The token to be used for creating the Pull Request to upstream <br/> Required Scopes: Pull requests (Read and write) |

## 3. Relevant branches

TODO

## 4. isort and flake8 in VSCode

We need to ensure that the code we want to push to upstream has been analyzied by flake8 and isort.

- Install the flake8 and isort VSCode extensions (publisher: Microsoft) and enable them
- If you're using multi-root workspaces, you can configure each folder individually by addind the `"flake8.enabled": true` line to the `.vscode/settings.json` file

*Note*: the isort settings are in the `.isort.cfg` and flake8 settings are in `tox.ini`
*Note*: the exact calls to isort and flake8 are in `.github/workflows/static-checks.yml`

## 5. Create the Pull Request

### 5.1 From the command line

TODO Execute `python -m utils.create_pull_request` from the root dir of this repo (see [Parameters](#54-parameters))

### 5.2 From VSCode

TODO

### 5.3 From a Gitlab Pipeline

TODO Push your branch to origin then configure and execute a Pipeline.

### 5.4 Parameters

TODO

| Name | Type | Default | Details |
|------|------|---------|---------|
|||||


# 3.
Link to upstream (on GitHub): [CaPyCLI](https://github.com/sw360/capycli)
