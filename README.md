```
local ➜  git2local git:(main) ./git2local --help
usage: git2local [-h] [--orgs ORGS]
                 [--period {lastweek,week,7d,14d,month,lastmonth,quarter,year}]
                 [--devs DEVS] [--non-interactive] [--days DAYS]

Generate GitHub Engineering Activity Reports (EAR) for GitHub organizations

options:
  -h, --help            show this help message and exit
  --orgs ORGS           Comma-separated list of GitHub organizations
                        (default: interactive prompt or
                        euroblaze,wapsol). Example: euroblaze,wapsol
  --period {lastweek,week,7d,14d,month,lastmonth,quarter,year}
                        Time period for the report (default:
                        interactive prompt or lastweek). See examples
                        above for period options.
  --devs DEVS           Comma-separated list of GitHub usernames to
                        filter (default: all developers). Example:
                        VTV24710,euroblaze,daikk115
  --non-interactive     Run without interactive prompts, using
                        defaults or specified flags
  --days DAYS           (Deprecated: use --period instead) Number of
                        days to look back

Examples:
  git2local                                              # Interactive mode (prompts for orgs and period)
  git2local --orgs=euroblaze,wapsol --period=week        # This week's activity
  git2local --orgs=euroblaze --period=month              # This month for euroblaze
  git2local --devs=VTV24710 --period=quarter             # Filter specific developer
  git2local --non-interactive                            # Use all defaults without prompts
  git2local --orgs=myorg --period=7d --devs=user1,user2  # Combine all filters

Time Periods:
  lastweek   - Last Week (default)
  week       - This Week (Monday to today)
  7d         - Past 7 Days
  14d        - Past 14 Days
  month      - This Month
  lastmonth  - Last Month
  quarter    - This Quarter
  year       - This Year

Output:
  Reports are saved to: reports/EAR_YYYY-MM-DD.html
```
