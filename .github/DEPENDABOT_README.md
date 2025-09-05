# Dependabot Configuration

This repository uses Dependabot for automated dependency updates. Dependabot will automatically create pull requests to keep your dependencies up to date.

## What Dependabot Does

- **Weekly Updates**: Checks for dependency updates every Monday at 9:00 UTC
- **Automated PRs**: Creates pull requests for outdated dependencies
- **Grouped Updates**: Groups related packages together (e.g., all React packages in one PR)
- **Auto-Approval**: Automatically approves and merges patch and minor version updates
- **Testing**: Runs linting and building on all dependency update PRs

## Configuration Files

### `.github/dependabot.yml`
Main configuration file that defines:
- Which package ecosystems to monitor (npm/pnpm, pip)
- Update schedules and frequency
- Grouping rules for related packages
- PR limits and reviewer assignments
- Ignored dependencies and version constraints

### `.github/workflows/dependabot.yml`
GitHub Actions workflow that:
- Runs tests on Dependabot PRs
- Auto-approves safe updates (patch/minor versions)
- Enables auto-merge for approved PRs

## Package Groups

Dependencies are grouped logically to reduce PR noise:

- **React**: React core packages (`react`, `react-dom`, types)
- **Next.js**: Next.js and related packages
- **Radix UI**: All Radix UI component packages
- **AI SDK**: AI SDK and related packages
- **Testing**: Playwright and testing utilities
- **Dev Tools**: Development tools (Drizzle, Biome, ESLint, TypeScript)

## Update Schedule

- **Frequency**: Weekly (Mondays)
- **Time**: 9:00 UTC
- **PR Limit**: 10 open PRs maximum
- **Auto-merge**: Patch and minor updates only

## Ignored Updates

The following updates are ignored to prevent breaking changes:
- Major version updates for React, React DOM, and Next.js
- Next.js canary versions (unstable)

## Customization

### Adding Reviewers/Assignees
Update the `reviewers` and `assignees` fields in `.github/dependabot.yml`:
```yaml
reviewers:
  - "your-github-username"
assignees:
  - "your-github-username"
```

### Modifying Update Schedule
Change the schedule in `.github/dependabot.yml`:
```yaml
schedule:
  interval: "daily"  # or "weekly", "monthly"
  day: "monday"      # for weekly updates
  time: "09:00"
  timezone: "UTC"
```

### Adding New Package Groups
Add new groups in the `groups` section:
```yaml
groups:
  your-group:
    patterns:
      - "package-pattern-*"
```

### Ignoring Specific Dependencies
Add to the `ignore` section:
```yaml
ignore:
  - dependency-name: "specific-package"
    versions: ["1.2.3"]
```

## Monitoring Dependabot

- Check the **Dependabot** tab in your GitHub repository
- Review open PRs created by Dependabot
- Monitor the Actions tab for automated testing results
- Check dependency alerts for security vulnerabilities

## Security Updates

Dependabot also creates PRs for security vulnerabilities with high priority. These are not subject to the same grouping and scheduling rules as regular updates.

## Troubleshooting

### PRs Not Auto-Merging
- Check if the PR has conflicts
- Ensure tests are passing
- Verify the update is patch/minor (major updates require manual review)

### Missing Updates
- Check Dependabot's repository settings
- Verify the package ecosystem is configured
- Ensure the schedule hasn't been modified

### Too Many PRs
- Increase the `open-pull-requests-limit`
- Adjust grouping rules to combine more packages
- Change the update frequency
