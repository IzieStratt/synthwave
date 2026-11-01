#!/bin/sh
# synthwave installer for macOS and Linux:
#   curl -fsSL https://raw.githubusercontent.com/JosTheDude/synthwave/main/install.sh | sh
# Installs mpv (with your package manager), uv, yt-dlp and synthwave. Safe to run again to update.
set -u

main() {
  REPO="git+https://github.com/JosTheDude/synthwave"
  LOG="${TMPDIR:-/tmp}"
  LOG="${LOG%/}/synthwave-install.log"
  : >"$LOG"
  OLD_PATH=":$PATH:"

  if [ -t 1 ] && [ -z "${NO_COLOR:-}" ]; then
    e=$(printf '\033')
    pink="$e[38;5;199m" cyan="$e[38;5;51m" lilac="$e[38;5;183m" red="$e[38;5;203m"
    dim="$e[2m" bold="$e[1m" off="$e[0m" clr="$(printf '\r')$e[K" tty=1
  else
    pink= cyan= lilac= red= dim= bold= off= clr= tty=
  fi

  # the TUI's header: the setting sun, then the title in the synthwave gradient
  title=
  set -- 199 205 213 177 141 105 75 51 51
  for c in s y n t h w a v e; do
    title="$title${tty:+$e[38;5;${1}m}$c"
    shift
  done
  printf '\n  %s◓%s %s%s%s  %sinstaller%s\n\n' "$pink" "$off" "$bold" "$title" "$off" "$dim" "$off"

  # mpv comes from the system package manager; everything else from uv
  if command -v mpv >/dev/null 2>&1; then
    ok mpv "already installed"
  else
    sudo=
    [ "$(id -u)" = 0 ] || sudo="sudo -n"  # -n: the password was asked for up front, never mid-spinner
    case "$(uname -s)" in
      Darwin)
        command -v brew >/dev/null 2>&1 || fail mpv "needs Homebrew first: https://brew.sh"
        step mpv brew install mpv ;;
      *)
        if command -v apt-get >/dev/null 2>&1; then set -- sh -c "$sudo apt-get update && $sudo apt-get install -y mpv"
        elif command -v dnf >/dev/null 2>&1; then set -- $sudo dnf install -y mpv
        elif command -v pacman >/dev/null 2>&1; then set -- $sudo pacman -S --needed --noconfirm mpv
        elif command -v zypper >/dev/null 2>&1; then set -- $sudo zypper --non-interactive install mpv
        else fail mpv "install it with your package manager, then run this again"
        fi
        if [ -n "$sudo" ]; then
          printf '  %s◌%s %-10s %sneeds your password%s\n' "$lilac" "$off" mpv "$dim" "$off"
          sudo -v </dev/tty || fail mpv "sudo was cancelled"
        fi
        step mpv "$@" ;;
    esac
  fi

  export PATH="$HOME/.local/bin:$PATH"  # where uv puts itself and its tools
  if command -v uv >/dev/null 2>&1; then
    ok uv "already installed"
  else
    step uv sh -c "curl -LsSf https://astral.sh/uv/install.sh | sh"
  fi

  if command -v yt-dlp >/dev/null 2>&1; then
    ok yt-dlp "already installed"
  else
    step yt-dlp uv tool install yt-dlp
  fi

  # --reinstall so running this again pulls the latest synthwave; uv fetches Python 3.9+ if needed
  step synthwave uv tool install --reinstall "$REPO"
  uv tool update-shell >>"$LOG" 2>&1 || true  # puts ~/.local/bin on PATH in new shells

  case "$OLD_PATH" in
    *":$HOME/.local/bin:"*) how="run ${pink}synthwave${off} to tune in" ;;
    *) how="open a new terminal and run ${pink}synthwave${off}" ;;
  esac
  printf '\n  %s▶%s all set. %s\n\n' "$cyan" "$off" "$how"
}

ok() { printf '%s  %s✓%s %-10s %s%s%s\n' "$clr" "$cyan" "$off" "$1" "$dim" "$2" "$off"; }

fail() {
  printf '%s  %s✗%s %-10s %s\n' "$clr" "$red" "$off" "$1" "$2"
  if [ -s "$LOG" ]; then
    printf '\n%s' "$dim"
    tail -n 15 "$LOG" | sed 's/^/    /'
    printf '%s\n  full log: %s\n' "$off" "$LOG"
  fi
  printf '\n'
  exit 1
}

# step <label> <command...>: runs the command quietly behind a spinning sun
step() {
  label=$1
  shift
  "$@" </dev/null >>"$LOG" 2>&1 &  # </dev/null: under `curl | sh`, stdin is this script
  pid=$!
  if [ -n "$tty" ]; then
    while kill -0 "$pid" 2>/dev/null; do
      for f in ◐ ◓ ◑ ◒; do
        printf '%s  %s%s%s %-10s %sinstalling…%s' "$clr" "$pink" "$f" "$off" "$label" "$dim" "$off"
        sleep 0.1
      done
    done
  fi
  if wait "$pid"; then ok "$label" installed; else fail "$label" "couldn't install it"; fi
}

main "$@"  # last, so a half-downloaded script never runs
