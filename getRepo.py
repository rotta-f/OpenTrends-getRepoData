#!/usr/bin/env python3

import json
import getpass
import argparse

import github as gh


class Keys():
    def __init__(self, github_name, name = None):
        self.github_name = github_name
        self.name = name

    def __str__(self):
      if self.name:
        return self.name
      else:
        return self.github_name

    def __eq__(self, other):
        return self.github_name == other.github_name and self.name == other.name

    def __hash__(self):
        return self.github_name.__hash__()

    def __repr__(self):
        return self.__str__()

    def getName(self):
        if self.name:
            return self.name
        return self.github_name

class Key(str):
    def __new__(cls, github_name, name = None):
        obj = str.__new__(cls, github_name if not name else name)
        obj.github_name = github_name
        obj.name = name
        return obj

keys_main = {
    Key("created_at"): None,
    Key("description"): None,
    Key("fork"): None,
    Key("forks_count"): None,
    Key("full_name"): None,
    Key("has_downloads"): None,
    Key("has_pages"): None,
    Key("has_wiki"): None,
    Key("homepage"): None,
    Key("language"): None,
    Key("name"): None,
    Key("open_issues_count"): None,
    Key("pushed_at"): None,
    Key("size"): None,
    Key("subscribers_count"): None,
    Key("updated_at"): None,
    Key("watchers_count"): None,
    Key("stargazers_count", "stars_count"): None
}

parser = argparse.ArgumentParser(description="Search for github data.")
parser.add_argument('-l', help="Login of the user")
parser.add_argument('-p', help="Password of the user")
parser.add_argument('--repo', help="Repository to get the data")
parser.add_argument('--verbose', "-v", action="store_true", help="Verbose mode")
args = parser.parse_args()


login = input("Github Login: ") if not args.l else args.l
password = getpass.getpass() if not args.p else args.p
repository = input("Repository: ") if not args.repo else args.repo
verbose = False if not args.verbose else args.verbose

github = gh.Github(login=login, password=password, verbose=verbose)
github.setRepository(repository)

content_main = github.getRepositoryInfo()

for key in keys_main:
    if key.github_name in content_main:
        keys_main[key] = content_main[key.github_name]

to_complete="To complete"
keys = {
  Key('changelog'): to_complete,
  Key('close_issues_count'): github.getIssuesCount("closed"),
  Key('close_pull_requests_count'): github.getPullsCount("closed"),
  Key('commits_count'): github.getCommitsCount(),
  Key('contributors_count'): github.getContributorsCount(),
  Key('good'): to_complete,
  Key('issues_count'): github.getIssuesCount(),
  Key('license'): to_complete,
  Key('oldest_open_issue'): None if not github.getOldestIssueRequest('open') else github.getOldestIssueRequest('open')["created_at"],
  Key('oldest_open_pull_request'): None if not github.getOldestPullRequest('open') else github.getOldestPullRequest('open')["created_at"],
  Key('open_pull_requests_count'): github.getPullsCount("open"),
  Key('pull_requests_count'): github.getPullsCount(),
  Key('readme'): to_complete
}

keys.update(keys_main)

print(json.dumps(keys, sort_keys=True, indent=2))