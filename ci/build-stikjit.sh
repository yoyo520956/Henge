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
# BUILD_LIBRARY_FOR_DISTRIBUTION must stay OFF here. The module is named StikJIT and
# it also declares `public enum StikJIT`, so the generated .swiftinterface qualifies
# the top-level DDIPaths as `StikJIT.DDIPaths`. Swift 6.0 (Xcode 16.4) then resolves
# that prefix to the enum instead of the module and fails to parse its own interface:
#   error: 'DDIPaths' is not a member type of enum 'StikJIT.StikJIT'
# Upstream never hits this because their prebuilt xcframework was made with Xcode 27,
# whose compiler emits an unambiguous interface. Without library evolution we ship the
# binary .swiftmodule instead, which is fine because Henge and StikJIT are compiled by
# the same Xcode in this one CI run.
xcodebuild archive -project StikJIT.xcodeproj -scheme StikJIT -configuration Release \
    -sdk iphoneos -destination 'generic/platform=iOS' -archivePath build/StikJIT \
    BUILD_LIBRARY_FOR_DISTRIBUTION=NO CODE_SIGNING_ALLOWED=NO -quiet
xcodebuild -create-xcframework \
    -framework build/StikJIT.xcarchive/Products/Library/Frameworks/StikJIT.framework \
    -output StikJIT.xcframework
