#!/usr/bin/env bash
# Size-aware release uploader: skips an asset only when name AND size already match.
set -u
cd /root/Projects/20260922-iphone-wallpapers
REPO=leon7786/20260923-iphone-wallpapers
TAGS=(v2.0-iphone v2.0-ipad v2.0-mac v2.0-ios v2.0-special)
PDIR=(01-iPhone 02-iPad 03-Mac 04-iOS-generic 05-Special)
ONLY="${1:-}"

for i in "${!TAGS[@]}"; do
  tag=${TAGS[$i]}; plat=${PDIR[$i]}
  [ -n "$ONLY" ] && [ "$ONLY" != "$plat" ] && continue
  if ! gh release view "$tag" -R "$REPO" >/dev/null 2>&1; then
    echo "!! missing release $tag"; continue
  fi
  echo "=== $tag ($plat)"
  gh release view "$tag" -R "$REPO" --json assets -q '.assets[]|"\(.name)\t\(.size)"' > /tmp/rem_$tag.txt 2>/dev/null
  for f in zips_out/${plat}__*.zip; do
    [ -e "$f" ] || continue
    b=$(basename "$f"); sz=$(stat -c%s "$f")
    if awk -F'\t' -v n="$b" -v s="$sz" '$1==n && $2==s{found=1} END{exit !found}' /tmp/rem_$tag.txt; then
      continue
    fi
    ok=0
    for try in 1 2 3; do
      if out=$(timeout 1200 gh release upload "$tag" "$f" -R "$REPO" --clobber 2>&1); then ok=1; break; fi
      echo "   retry$try $b :: $(printf '%s' "$out" | tail -1)"; sleep 10
    done
    if [ $ok -eq 1 ]; then echo "   up   $b  $((sz/1048576)) MB"; else echo "   FAIL $b"; fi
  done
done

echo "=== verify:"
tot=0
for i in "${!TAGS[@]}"; do
  tag=${TAGS[$i]}; plat=${PDIR[$i]}
  [ -n "$ONLY" ] && [ "$ONLY" != "$plat" ] && continue
  gh release view "$tag" -R "$REPO" --json assets -q '.assets[]|"\(.name)\t\(.size)"' > /tmp/rem_$tag.txt 2>/dev/null
  n=0; bad=0
  for f in zips_out/${plat}__*.zip; do
    [ -e "$f" ] || continue
    n=$((n+1))
    b=$(basename "$f"); sz=$(stat -c%s "$f")
    awk -F'\t' -v n="$b" -v s="$sz" '$1==n && $2==s{found=1} END{exit !found}' /tmp/rem_$tag.txt || { bad=$((bad+1)); echo "   MISMATCH $b"; }
  done
  echo "$tag: $n local / $(wc -l < /tmp/rem_$tag.txt) remote, mismatch=$bad"
  tot=$((tot+n))
done
echo "LOCAL SETS CHECKED: $tot"
