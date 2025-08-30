## Related user story/task

- implements `<link to JIRA-ISSUE or JIRA-ISSUE-ID>`
- fixes `<link to GITLAB-ISSUE or GITLAB-ISSUE-ID>`

## Improvements

- first improvement
- second improvement
- third improvement

## Required steps before merging (Done by Requestor)

- check you commit messages if all are following [semantic commits](https://code.siemens.com/gemini/support/gitlab-releases-ci-template#how-to-work-with-semantic-commit-messages-in-this-pipeline) and only use types `chore`, `feat`, `fix`, `docs` then you can directly address merge request otherwise activate squash in your merge request and use a semantic commit message as title for your merge request

## Required steps before merging (Done by Maintainer)

- [ ] review changes
- [ ] check if all stages in CI/CD pipeline run without warnings or errors (check especially builds, sometime fails but does not return an error on script run)
- [ ] check commit messages
  - in case of squash activated check if title and squash commit message follow [semantic commit conventions](https://code.siemens.com/gemini/support/gitlab-releases-ci-template#how-to-work-with-semantic-commit-messages-in-this-pipeline)
  - in case of squash deactivated check if all changes follow [semantic commit conventions](https://code.siemens.com/gemini/support/gitlab-releases-ci-template#how-to-work-with-semantic-commit-messages-in-this-pipeline)

## Further steps after merging (Done by Maintainer)

- [ ] if a new release should be created, check if the corresponding pipeline has run
