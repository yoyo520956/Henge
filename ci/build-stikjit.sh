#!/usr/bin/env bash
# Rebuild StikJIT 1.9.0 with full-width debugserver addresses.
set -euo pipefail

HENGE_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STIKJIT_ROOT="${1:?StikJIT checkout path required}"

git clone --depth 1 --branch 1.9.0 https://github.com/StikDebug/StikJIT.git "$STIKJIT_ROOT"
# Verify we got the right tag
test "$(git -C "$STIKJIT_ROOT" describe --tags)" = "1.9.0"
git -C "$STIKJIT_ROOT" apply "$HENGE_ROOT/ci/stikjit-high-address.patch"

cd "$STIKJIT_ROOT"
xcodegen generate
xcodebuild archive -project StikJIT.xcodeproj -scheme StikJIT -configuration Release \
    -sdk iphoneos -destination 'generic/platform=iOS' -archivePath build/StikJIT \
    BUILD_LIBRARY_FOR_DISTRIBUTION=YES CODE_SIGNING_ALLOWED=NO -quiet
xcodebuild -create-xcframework \
    -framework build/StikJIT.xcarchive/Products/Library/Frameworks/StikJIT.framework \
    -output StikJIT.xcframework
