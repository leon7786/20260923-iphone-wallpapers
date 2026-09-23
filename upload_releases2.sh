#!/usr/bin/env bash
# Resume-able release asset uploader: skips what is already up, per-file timeout, retries.
set -u
cd /root/Projects/20260922-iphone-wallpapers
REPO=leon7786/20260923-iphone-wallpapers
TAGS=(v2.0-iphone v2.0-ipad v2.0-mac v2.0-ios v2.0-special)
PDIR=(01-iPhone 02-iPad 03-Mac 04-iOS-generic 05-Special)

for i in "${!TAGS[@]}"; do
  tag=${TAGS[$i]}; plat=${PDIR[$i]}
  echo "=== $tag ($plat)"
  up=$(gh release view "$tag" -R "$REPO" --json assets -q '.assets[].name' 2>/dev/null)
  for f in zips_out/${plat}__*.zip; do
    [ -e "$f" ] || continue
    b=$(basename "$f")
    if printf '%s\n' "$up" | grep -Fxq "$b"; then echo "   skip $b"; continue; fi
    ok=0
    for try in 1 2 3; do
      if timeout 600 gh release upload "$tag" "$f" -R "$REPO" --clobber >/dev/null 2>&1; then ok=1; break; fi
      echo "   retry$try $b (timeout/err)"; sleep 5
    done
    if [ $ok -eq 1 ]; then echo "   up   $b  $(du -m "$f" | cut -f1) MB"; else echo "   FAIL $b"; fi
  done
done

echo "=== asset counts:"
tot=0
for tag in "${TAGS[@]}"; do
  n=$(gh release view "$tag" -R "$REPO" --json assets -q '.assets|length')
  echo "$tag: $n"; tot=$((tot+n))
done
echo "TOTAL ASSETS: $tot / 76"
