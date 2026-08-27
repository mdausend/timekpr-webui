FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04

ARG DEBIAN_FRONTEND=noninteractive

COPY scripts/dev-versions.env /tmp/dev-versions.env

ENV ANDROID_HOME=/opt/android-sdk
ENV ANDROID_SDK_ROOT=/opt/android-sdk
ENV PATH="${PATH}:/opt/android-sdk/cmdline-tools/latest/bin:/opt/android-sdk/platform-tools"

# System dependencies already required by scripts/setup-dev.sh and CI.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        curl \
        git \
        libdbus-1-dev \
        libssl-dev \
        openjdk-17-jdk \
        pkg-config \
        podman \
        python3 \
        python3-dev \
        python3-pip \
        python3-venv \
        unzip \
        wget \
    && rm -rf /var/lib/apt/lists/*

# Python 3.12+ is required by the project.
RUN python3 -c 'import sys; assert sys.version_info >= (3, 12), sys.version'

# Rust stable, matching the repository requirement of Rust >= 1.85.
USER vscode

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs \
        | sh -s -- -y --default-toolchain stable \
    && /home/vscode/.cargo/bin/rustup target add \
        aarch64-linux-android \
        armv7-linux-androideabi \
        x86_64-linux-android

ENV PATH="/home/vscode/.cargo/bin:${PATH}"

# cargo-ndk is used by scripts/android-native-build.sh and Android CI.
RUN cargo install cargo-binstall \
    && cargo binstall -y --force cargo-ndk

USER root

# Android command-line tools version already used by scripts/setup-dev.sh.
RUN set -a \
    && . /tmp/dev-versions.env \
    && set +a \
    && mkdir -p "${ANDROID_SDK_ROOT}/cmdline-tools" \
    && curl -fsSL \
        "https://dl.google.com/android/repository/commandlinetools-linux-${ANDROID_CMDLINE_TOOLS_VERSION}_latest.zip" \
        -o /tmp/android-commandline-tools.zip \
    && unzip -q /tmp/android-commandline-tools.zip -d /tmp/android-commandline-tools \
    && mv /tmp/android-commandline-tools/cmdline-tools \
        "${ANDROID_SDK_ROOT}/cmdline-tools/latest" \
    && rm -rf \
        /tmp/android-commandline-tools \
        /tmp/android-commandline-tools.zip

RUN yes | sdkmanager --sdk_root="${ANDROID_SDK_ROOT}" --licenses >/dev/null || true

RUN set -a \
    && . /tmp/dev-versions.env \
    && set +a \
    && sdkmanager --sdk_root="${ANDROID_SDK_ROOT}" \
        "platform-tools" \
        "platforms;android-${ANDROID_API_LEVEL}" \
        "build-tools;${ANDROID_BUILD_TOOLS_VERSION}" \
        "ndk;${ANDROID_NDK_VERSION}" \
    && ln -sfn \
        "${ANDROID_SDK_ROOT}/ndk/${ANDROID_NDK_VERSION}" \
        "${ANDROID_SDK_ROOT}/ndk/current"

ENV ANDROID_NDK_HOME="${ANDROID_SDK_ROOT}/ndk/current"
ENV ANDROID_NDK_ROOT="${ANDROID_NDK_HOME}"

RUN chown -R vscode:vscode "${ANDROID_SDK_ROOT}"

RUN set -a \
    && . /tmp/dev-versions.env \
    && set +a \
    && curl -fsSL \
        "https://deb.nodesource.com/setup_${NODE_MAJOR_VERSION}.x" \
        | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

USER vscode