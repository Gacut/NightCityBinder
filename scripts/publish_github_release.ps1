# Run from Windows PowerShell after build_github_apk.sh has produced the signed APK.
# Requires GitHub CLI authenticated as Gacut: gh auth login -h github.com
$ErrorActionPreference = 'Continue'
$project = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $project
# Codex may have created this local repository under a sandbox account.
# Trust this exact path for this process and its GitHub CLI child processes only.
$env:GIT_CONFIG_COUNT = '1'
$env:GIT_CONFIG_KEY_0 = 'safe.directory'
$env:GIT_CONFIG_VALUE_0 = $project.Replace('\', '/')

$version = '1.0.18'
$tag = 'v1.0.0'
$repo = 'Gacut/NightCityBinder'
$apk = Join-Path $project "dist/NightCityBinder-$version-github.apk"
$checksum = "$apk.sha256"
$notes = Join-Path $project 'RELEASE_NOTES_1.0.0.md'
if (-not (Test-Path -LiteralPath $apk) -or -not (Test-Path -LiteralPath $checksum)) {
    throw "Signed APK or SHA-256 file missing. Run scripts/build_github_apk.sh in Ubuntu/WSL first."
}
if (-not (Test-Path -LiteralPath $notes)) { throw "Release notes missing: $notes" }

& gh auth status
if ($LASTEXITCODE -ne 0) { throw 'Log in to GitHub CLI: gh auth login -h github.com' }
$login = (& gh api user --jq .login)
if ($LASTEXITCODE -ne 0 -or $login -ne 'Gacut') { throw "GitHub account is '$login'; expected Gacut." }

$changes = @(& git status --porcelain=v1 --untracked-files=normal)
if ($LASTEXITCODE -ne 0) { throw 'Could not inspect the local Git working tree.' }
if ($changes.Count -gt 0 -and $changes[0]) {
    $changes | ForEach-Object { Write-Output $_ }
    throw 'The Git working tree is not clean. Review the listed files before publishing.'
}
& git rev-parse --verify $tag 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) { throw "Local tag $tag is missing." }

& gh repo view $repo --json nameWithOwner *> $null
if ($LASTEXITCODE -ne 0) {
    & gh repo create $repo --public --source . --remote origin --push --description 'Unofficial Cyberpunk TCG binder for Android'
    if ($LASTEXITCODE -ne 0) { throw "Could not create repository $repo." }
} else {
    $origin = (& git remote get-url origin 2>$null)
    if ($LASTEXITCODE -ne 0) {
        & git remote add origin "https://github.com/$repo.git"
    } elseif ($origin -notmatch 'github\.com[:/]Gacut/NightCityBinder(?:\.git)?$') {
        throw "Origin points to a different repository: $origin"
    }
    & git push -u origin main
    if ($LASTEXITCODE -ne 0) { throw 'Could not push main branch.' }
}
& git push origin $tag
if ($LASTEXITCODE -ne 0) { throw "Could not push tag $tag." }
& gh release view $tag --repo $repo --json url *> $null
if ($LASTEXITCODE -eq 0) { throw "Release $tag already exists. Review it before publishing again." }
& gh release create $tag $apk $checksum --repo $repo --title 'NightCityBinder 1.0.0' --notes-file $notes --verify-tag
if ($LASTEXITCODE -ne 0) { throw 'Release creation failed.' }
& gh release view $tag --repo $repo --json url,assets
if ($LASTEXITCODE -ne 0) { throw 'Release was created but could not be verified.' }
