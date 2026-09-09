#!/usr/bin/env bash

set -euo pipefail

# Verify that the current environment provides the development toolchain
# expected by this repository.
#
# This script is intentionally independent of how the environment was
# provisioned. It provides a shared contract for development environments
# such as:
#
#   - scripts/setup-dev.sh
#   - .devcontainer/
#
# Keep this verification aligned with both setup mechanisms while
# scripts/setup-dev.sh and the devcontainer are supported in parallel.
# The implementations do not need to install tools in the same way; they
# only need to provide the capabilities required by the project.
#
# This script should not install, modify, or configure the environment.
# It only verifies prerequisites and reports missing capabilities.

errors=0

check_command()
{
    local command_name="$1"
    local description="${2:-$1}"

    if command -v "${command_name}" >/dev/null 2>&1; then
        printf '[ok]      %s\n' "${description}"
    else
        printf '[missing] %s (%s)\n' "${description}" "${command_name}" >&2
        errors=$((errors + 1))
    fi
}

printf 'Guardian development environment\n'
printf '================================\n\n'

check_command python3 "Python"
check_command cargo "Rust/Cargo"
check_command rustc "Rust compiler"
check_command rustup "Rust toolchain manager"
check_command cargo-ndk "cargo-ndk"
check_command java "Java"
check_command node "Node.js"
check_command npm "npm"
check_command sdkmanager "Android SDK manager"
check_command adb "Android platform tools"
check_command git "Git"

printf '\n'

if (( errors > 0 )); then
    printf 'Development environment verification failed: %d capability/capabilities missing.\n' \
        "${errors}" >&2
    exit 1
fi

printf 'Development environment verification passed.\n'