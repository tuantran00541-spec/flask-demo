#!/usr/bin/env bash
set -euo pipefail

release=$(realpath -e -- "$1")
releases=$(dirname -- "$release")
current=$(dirname -- "$releases")/current
next="$release/.next-current"
service=flask-demo.service

is_release() {
    [[ $(dirname -- "$1") == "$releases" && $(basename -- "$1") == release.* && -d "$1" && ! -L "$1" ]]
}

previous=$(readlink -- "$current" || true)
if [[ $(basename -- "$releases") != releases ]] || ! is_release "$release" ||
   [[ ! -x "$release/venv/bin/python" || -e "$current" && ! -L "$current" ]] ||
   { [[ -n "$previous" ]] && ! is_release "$previous"; }; then
    echo "Invalid release directory or current release link: $release" >&2
    exit 1
fi
if [[ "$previous" == "$release" ]]; then
    echo "Release is already active: $release" >&2
    exit 1
fi

point_current_at() {
    ln -s -- "$1" "$next" && mv -Tf -- "$next" "$current"
}

restart_and_check() {
    sudo -n /usr/bin/systemctl restart "$service" &&
        curl -fsS --noproxy '*' --connect-timeout 1 --max-time 2 \
            --retry 5 --retry-connrefused --retry-delay 1 --retry-max-time 10 \
            http://127.0.0.1:5000/health &&
        systemctl is-active --quiet "$service"
}

rollback() {
    if [[ $(readlink -- "$current") != "$release" ]]; then
        return
    fi
    if [[ -n "$previous" ]]; then
        if point_current_at "$previous" && restart_and_check; then
            echo "Deployment failed. Restored $previous." >&2
            return
        fi
    elif unlink -- "$current" && sudo -n /usr/bin/systemctl stop "$service"; then
        echo "Deployment failed. Stopped the first release." >&2
        return
    fi
    echo "Rollback of $service failed. Check its systemd journal." >&2
}

trap rollback EXIT
trap 'exit 1' HUP INT TERM
point_current_at "$release"
restart_and_check
trap - EXIT HUP INT TERM

if [[ -n "$previous" ]] && ! find "$previous" -depth -delete; then
    echo "Unable to remove superseded release: $previous" >&2
fi
