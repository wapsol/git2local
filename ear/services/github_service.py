"""GitHub service for fetching and aggregating GitHub activity."""

import json
import subprocess
import sys
from typing import List, Dict, Set, Optional
from collections import defaultdict


class GitHubService:
    """Service for GitHub API operations."""

    def __init__(self):
        """Initialize GitHub service."""
        pass

    def run_gh_command(self, query: str) -> dict:
        """Execute a GitHub GraphQL query using gh CLI.

        Args:
            query: GraphQL query string

        Returns:
            Parsed JSON response

        Raises:
            RuntimeError: If gh command fails
        """
        cmd = ['gh', 'api', 'graphql', '-f', f'query={query}']
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"GitHub API error: {e.stderr}")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"JSON parsing error: {e}")

    def fetch_recent_activity(self, orgs: List[str], since_date: str) -> Dict:
        """Fetch issues and PRs updated since the given date.

        Args:
            orgs: List of GitHub organizations
            since_date: ISO date string (YYYY-MM-DD)

        Returns:
            Dictionary with 'issues' and 'prs' keys
        """
        org_query = ' '.join(f'org:{org}' for org in orgs)

        # Fetch issues
        issues_query = f'''
        {{
          search(query: "{org_query} is:issue updated:>={since_date}", type: ISSUE, first: 100) {{
            issueCount
            edges {{
              node {{
                ... on Issue {{
                  number
                  title
                  url
                  createdAt
                  updatedAt
                  state
                  body
                  repository {{
                    nameWithOwner
                  }}
                  author {{
                    login
                  }}
                  comments(first: 50) {{
                    totalCount
                    nodes {{
                      author {{
                        login
                      }}
                      createdAt
                      updatedAt
                      url
                      body
                    }}
                  }}
                }}
              }}
            }}
          }}
        }}
        '''

        # Fetch PRs
        prs_query = f'''
        {{
          search(query: "{org_query} is:pr updated:>={since_date}", type: ISSUE, first: 100) {{
            issueCount
            edges {{
              node {{
                ... on PullRequest {{
                  number
                  title
                  url
                  createdAt
                  updatedAt
                  mergedAt
                  closedAt
                  state
                  body
                  repository {{
                    nameWithOwner
                  }}
                  author {{
                    login
                  }}
                  comments(first: 50) {{
                    totalCount
                    nodes {{
                      author {{
                        login
                      }}
                      createdAt
                      updatedAt
                      url
                      body
                    }}
                  }}
                  reviews(first: 50) {{
                    totalCount
                    nodes {{
                      author {{
                        login
                      }}
                      createdAt
                      state
                    }}
                  }}
                }}
              }}
            }}
          }}
        }}
        '''

        print("Fetching issues...", file=sys.stderr)
        issues_data = self.run_gh_command(issues_query)

        print("Fetching PRs...", file=sys.stderr)
        prs_data = self.run_gh_command(prs_query)

        return {
            'issues': issues_data,
            'prs': prs_data
        }

    def aggregate_by_developer(
        self,
        data: Dict,
        filter_devs: Optional[Set[str]] = None
    ) -> Dict:
        """Aggregate all activity by developer.

        Args:
            data: Dictionary with 'issues' and 'prs' keys from fetch_recent_activity
            filter_devs: Optional set of developer usernames to filter

        Returns:
            Dictionary mapping developer username to activity data
        """
        developer_activity = defaultdict(lambda: {
            'issues_created': [],
            'issues_commented': [],
            'prs_created': [],
            'prs_reviewed': [],
            'prs_commented': [],
            'repos': set(),
            'by_repo': defaultdict(lambda: {
                'issues_created': [],
                'issues_commented': [],
                'prs_created': [],
                'prs_reviewed': [],
                'prs_commented': []
            }),
            'total_comments': 0,
            'total_issues': 0,
            'total_prs': 0,
            'total_reviews': 0
        })

        # Process issues
        for edge in data['issues']['data']['search']['edges']:
            issue = edge['node']
            author = issue['author']['login'] if issue['author'] else 'ghost'

            if not filter_devs or author in filter_devs:
                repo_name = issue['repository']['nameWithOwner']
                developer_activity[author]['issues_created'].append(issue)
                developer_activity[author]['repos'].add(repo_name)
                developer_activity[author]['by_repo'][repo_name]['issues_created'].append(issue)
                developer_activity[author]['total_issues'] += 1

            # Process issue comments
            for comment in issue['comments']['nodes']:
                commenter = comment['author']['login'] if comment['author'] else 'ghost'
                if not filter_devs or commenter in filter_devs:
                    repo_name = issue['repository']['nameWithOwner']
                    comment_data = {'issue': issue, 'comment': comment}
                    developer_activity[commenter]['issues_commented'].append(comment_data)
                    developer_activity[commenter]['repos'].add(repo_name)
                    developer_activity[commenter]['by_repo'][repo_name]['issues_commented'].append(comment_data)
                    developer_activity[commenter]['total_comments'] += 1

        # Process PRs
        for edge in data['prs']['data']['search']['edges']:
            pr = edge['node']
            author = pr['author']['login'] if pr['author'] else 'ghost'

            if not filter_devs or author in filter_devs:
                repo_name = pr['repository']['nameWithOwner']
                developer_activity[author]['prs_created'].append(pr)
                developer_activity[author]['repos'].add(repo_name)
                developer_activity[author]['by_repo'][repo_name]['prs_created'].append(pr)
                developer_activity[author]['total_prs'] += 1

            # Process PR comments
            for comment in pr['comments']['nodes']:
                commenter = comment['author']['login'] if comment['author'] else 'ghost'
                if not filter_devs or commenter in filter_devs:
                    repo_name = pr['repository']['nameWithOwner']
                    comment_data = {'pr': pr, 'comment': comment}
                    developer_activity[commenter]['prs_commented'].append(comment_data)
                    developer_activity[commenter]['repos'].add(repo_name)
                    developer_activity[commenter]['by_repo'][repo_name]['prs_commented'].append(comment_data)
                    developer_activity[commenter]['total_comments'] += 1

            # Process PR reviews
            for review in pr['reviews']['nodes']:
                reviewer = review['author']['login'] if review['author'] else 'ghost'
                if not filter_devs or reviewer in filter_devs:
                    repo_name = pr['repository']['nameWithOwner']
                    review_data = {'pr': pr, 'review': review}
                    developer_activity[reviewer]['prs_reviewed'].append(review_data)
                    developer_activity[reviewer]['repos'].add(repo_name)
                    developer_activity[reviewer]['by_repo'][repo_name]['prs_reviewed'].append(review_data)
                    developer_activity[reviewer]['total_reviews'] += 1

        # Convert sets to lists and defaultdicts to dicts
        for dev in developer_activity:
            developer_activity[dev]['repos'] = sorted(list(developer_activity[dev]['repos']))
            developer_activity[dev]['by_repo'] = dict(developer_activity[dev]['by_repo'])

        # Filter out developers not in the filter list
        if filter_devs:
            developer_activity = {k: v for k, v in developer_activity.items() if k in filter_devs}

        return dict(developer_activity)
