#!/usr/bin/env bash
# Rebuild StikJIT 2.0.1 under this runner's Xcode so its .swiftinterface can be
# parsed by the same compiler that will consume it.
#
# Why a rebuild at all: Husk ships a prebuilt StikJIT.xcframework made with
# Xcode 27. Its .swiftinterface uses Swift 6.2-era syntax that Xcode 16.4's
# Swift 6.0 cannot parse, so importing StikJIT fails before Henge compiles.
#
# Why the module rename: upstream's module is named `StikJIT` and it also
# declares `public enum StikJIT`. When Xcode 16.4 emits the .swiftinterface,
# references to the module-level `DDIPaths` inside that enum are qualified as
# `StikJIT.DDIPaths`. A Swift 6.0 compiler reading that interface resolves the
# prefix to the enum rather than to the module and fails with:
#     error: 'DDIPaths' is not a member type of enum 'StikJIT.StikJIT'
# Upstream never hits this because their prebuilt framework was made with
# Xcode 27, whose compiler emits `StikJIT::DDIPaths` (C++-style, unambiguous).
# Renaming the Swift module to StikJITKit removes the ambiguity for every
# compiler. The framework binary stays StikJIT.framework, so the xcframework
# layout, the Embed StikJIT phase and the Husk layout are untouched; only
# `import StikJIT` in Henge becomes `import StikJITKit`.
#
# BUILD_LIBRARY_FOR_DISTRIBUTION must stay ON: `xcodebuild -create-xcframework`
# refuses a framework that has no .swiftinterface (exit 70).
set -euo pipefail

HENGE_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
STIKJIT_ROOT="${1:?StikJIT checkout path required}"

git clone --depth 1 --branch 2.0.1 https://github.com/StikDebug/StikJIT.git "$STIKJIT_ROOT"
test "$(git -C "$STIKJIT_ROOT" describe --tags)" = "2.0.1"

# Full-width debugserver addresses: the shipped nine-digit packet format
# truncates JIT mappings above 0xfffffffff on iPads.
git -C "$STIKJIT_ROOT" apply "$HENGE_ROOT/ci/stikjit-high-address.patch"
# Give the Swift module a different name from the public enum inside it.
git -C "$STIKJIT_ROOT" apply "$HENGE_ROOT/ci/stikjit-module-rename.patch"

cd "$STIKJIT_ROOT"
xcodegen generate
xcodebuild archive -project StikJIT.xcodeproj -scheme StikJIT -configuration Release \
    -sdk iphoneos -destination 'generic/platform=iOS' -archivePath build/StikJIT \
    BUILD_LIBRARY_FOR_DISTRIBUTION=YES CODE_SIGNING_ALLOWED=NO -quiet
xcodebuild -create-xcframework \
    -framework build/StikJIT.xcarchive/Products/Library/Frameworks/StikJIT.framework \
    -output StikJIT.xcframework
