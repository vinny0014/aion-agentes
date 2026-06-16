#!/usr/bin/env bash
set -u

REPO_URL="${AION_REPO_URL:-https://github.com/vinny0014/aion-agentes.git}"
BRANCH="${AION_BRANCH:-aion/dev-flow-dashboard}"

echo "AION development flow diagnostic"
echo "Repository: ${REPO_URL}"
echo "Target branch: ${BRANCH}"
echo

echo "Git version: $(git --version)"
echo "Current branch: $(git branch --show-current 2>/dev/null || echo 'unknown')"
echo

echo "Configured remotes:"
git remote -v || true
echo

if ! git remote get-url origin >/dev/null 2>&1; then
  echo "origin remote is missing; configuring origin -> ${REPO_URL}"
  git remote add origin "${REPO_URL}"
fi

echo "origin fetch URL: $(git remote get-url origin 2>/dev/null || echo 'missing')"
echo "origin push URL: $(git remote get-url --push origin 2>/dev/null || echo 'missing')"
echo

echo "Checking GitHub reachability through current environment..."
if git ls-remote --heads origin >/tmp/aion-git-heads.txt 2>/tmp/aion-git-error.txt; then
  echo "GitHub reachable. Available heads:"
  sed -n '1,20p' /tmp/aion-git-heads.txt
else
  echo "GitHub is not reachable from this environment. Error:"
  cat /tmp/aion-git-error.txt
  exit 2
fi

echo
if git rev-parse --verify "${BRANCH}" >/dev/null 2>&1; then
  echo "Local branch ${BRANCH} exists."
else
  echo "Creating local branch ${BRANCH}."
  git checkout -b "${BRANCH}"
fi

echo "Diagnostic complete. If authenticated, run: git push -u origin ${BRANCH}"
