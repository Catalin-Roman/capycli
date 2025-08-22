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
1. **Prerequisite**: the code we want to be pushed to upstream is merged into the `fork_main` branch
2. **Prerequisite**: the `upstream_main` branch is up-to-date with `upstream/main`
    1. Option 1: trigger a Pipeline from the "Pull from upstream" Schedule
    2. Option 2: use git commands
3. Create a branch from `upstream_main` named `create-pull-request`
    1. *Note*: if you want to use a different name the you have to also set the `PULL_REQUEST_BRANCH` pipeline variable to match it
4. Cherry-pick the commit representing the changes to be pushed to upstream into the `create-pull-request` branch
    1. *Note*: the conflicts (if any) and the testing should be done on this branch
5. Run a Pipeline on the `create-pull-request` branch to automagically generate a Pull Request in the upstream
    1. The `create-pull-request` branch is first pushed to the intermediate Github repo
        1. *Note*: a valid Github token must be set as value for the `GITHUB_CONTENT_TOKEN` variable (see [Variables](#2-variables))
    2. The Pull Request is created from the intermediate Github repo to the upstream
        1. *Note*: a valid Github token must be set as value for the `GITHUB_PULL_REQUEST_TOKEN` variable (see [Variables](#2-variables))
    3. *Note*: the Pull Request is generated as *Draft*
    4. *Note*: The Pull Request is created with some default values for the title and body (see [Variables](#2-variables))
6. Check the Pull Request and if all *Checks* are successfull then make it *Ready for review*

## 2. Variables

| Name | Default | Details |
|------|---------|---------|
| PULL_REQUEST_BRANCH | create-pull-request | The name of the branch containing the code we want to be pushed to upstream |
| PULL_REQUEST_TITLE | Pull Request from SI GSW R&D | The default title of the Pull Request |
| PULL_REQUEST_BODY | This Pull Request was created by SI GSW R&D. | The default description of the Pull Request |
| GITHUB_CONTENT_TOKEN | No default value | The token to be used for pushing the `create-pull-request` branch to the intermediate Github repo|
| GITHUB_PULL_REQUEST_TOKEN | No default value | The token to be used for creating the Pull Request to upstream|

## 3. Relevant branches

## 4. isort and flake8 in VSCode

We need to ensure that the code we want to push to upstream has been analyzied by flake8 and isort

TODO

# 3.
Link to upstream (on GitHub): [CaPyCLI](https://github.com/sw360/capycli)
