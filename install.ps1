# synthwave installer for Windows:
#   irm https://raw.githubusercontent.com/JosTheDude/synthwave/main/install.ps1 | iex
# Installs mpv (with Scoop or winget), uv, yt-dlp and synthwave. Safe to run again to update.
# Non-ASCII characters are built from code points so this also works saved as a file on PowerShell 5.

& {
    $ErrorActionPreference = 'Stop'
    [Console]::OutputEncoding = [Text.Encoding]::UTF8
    $Repo = 'git+https://github.com/JosTheDude/synthwave'
    $Log = Join-Path $env:TEMP 'synthwave-install.log'
    $ErrLog = Join-Path $env:TEMP 'synthwave-install.err.log'
    $OldPath = ";$env:Path;"

    $e = [char]27
    $pink, $cyan, $lilac, $red = "$e[38;5;199m", "$e[38;5;51m", "$e[38;5;183m", "$e[38;5;203m"
    $dim, $bold, $off, $clr = "$e[2m", "$e[1m", "$e[0m", "`r$e[K"
    if ($env:NO_COLOR) { $pink = $cyan = $lilac = $red = $dim = $bold = $off = ''; $clr = "`r" }
    $sun = [char]0x25D3
    $frames = [char]0x25D0, [char]0x25D3, [char]0x25D1, [char]0x25D2
    $check, $cross, $play, $dots = [char]0x2713, [char]0x2717, [char]0x25B6, [char]0x2026

    function Ok($label, $note) { Write-Host "$clr  $cyan$check$off $($label.PadRight(10)) $dim$note$off" }

    function Fail($label, $note) {
        Write-Host "$clr  $red$cross$off $($label.PadRight(10)) $note"
        foreach ($f in $Log, $ErrLog) {
            if ((Test-Path $f) -and (Get-Item $f).Length) {
                Write-Host ''
                Get-Content $f -Tail 15 | ForEach-Object { Write-Host "    $dim$_$off" }
                Write-Host "  full log: $f"
            }
        }
        Write-Host ''
        throw "synthwave: couldn't install $label"
    }

    # Step <label> <exe> <arguments>: runs the command quietly behind a spinning sun
    function Step($label, $exe, $argv) {
        $p = Start-Process $exe -ArgumentList $argv -NoNewWindow -PassThru `
            -RedirectStandardOutput $Log -RedirectStandardError $ErrLog
        $null = $p.Handle  # without this, ExitCode comes back empty
        $i = 0
        while (-not $p.HasExited) {
            Write-Host -NoNewline "$clr  $pink$($frames[$i++ % 4])$off $($label.PadRight(10)) ${dim}installing$dots$off"
            Start-Sleep -Milliseconds 100
        }
        $p.WaitForExit()
        if ($p.ExitCode -eq 0) { Ok $label 'installed' } else { Fail $label "couldn't install it" }
    }

    function Has($cmd) { [bool](Get-Command $cmd -ErrorAction SilentlyContinue) }

    function RefreshPath {
        $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' +
            [Environment]::GetEnvironmentVariable('Path', 'User') + ";$HOME\.local\bin"
    }

    # the TUI's header: the setting sun, then the title in the synthwave gradient
    $title = ''
    $colors = 199, 205, 213, 177, 141, 105, 75, 51, 51
    for ($i = 0; $i -lt 9; $i++) {
        $title += $(if ($env:NO_COLOR) { '' } else { "$e[38;5;$($colors[$i])m" }) + 'synthwave'[$i]
    }
    Write-Host "`n  $pink$sun$off $bold$title$off  ${dim}installer$off`n"

    # mpv comes from Scoop or winget; everything else from uv
    if (Has mpv) {
        Ok 'mpv' 'already installed'
    } else {
        if (Has scoop) {
            Step 'mpv' 'powershell' '-NoProfile -Command "scoop bucket add extras; scoop install mpv"'
        } elseif (Has winget) {
            Step 'mpv' 'winget' 'install --id shinchiro.mpv --exact --silent --accept-source-agreements --accept-package-agreements'
        } else {
            Fail 'mpv' 'needs Scoop (https://scoop.sh) or winget first'
        }
        RefreshPath
        if (-not (Has mpv)) {
            Write-Host "  $lilac$([char]0x25CC)$off $('mpv'.PadRight(10)) ${dim}not on PATH yet; if a new terminal can't find it, add its folder to PATH$off"
        }
    }

    $env:Path += ";$HOME\.local\bin"  # where uv puts itself and its tools
    if (Has uv) {
        Ok 'uv' 'already installed'
    } else {
        Step 'uv' 'powershell' '-NoProfile -ExecutionPolicy ByPass -Command "irm https://astral.sh/uv/install.ps1 | iex"'
    }

    if (Has yt-dlp) {
        Ok 'yt-dlp' 'already installed'
    } else {
        Step 'yt-dlp' 'uv' 'tool install yt-dlp'
    }

    # --reinstall so running this again pulls the latest synthwave; uv fetches Python 3.9+ if needed
    Step 'synthwave' 'uv' "tool install --reinstall $Repo"
    & uv tool update-shell *> $null  # puts ~\.local\bin on PATH in new terminals

    $how = if ($OldPath -like "*;$HOME\.local\bin;*") { "run ${pink}synthwave$off to tune in" }
           else { "open a new terminal and run ${pink}synthwave$off" }
    Write-Host "`n  $cyan$play$off all set. $how`n"
}
