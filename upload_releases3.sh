#!/usr/bin/env bash
# Create (if missing) each platform Release and upload/resume its per-set ZIPs.
set -u
cd /root/Projects/20260922-iphone-wallpapers
REPO=leon7786/20260923-iphone-wallpapers
TAGS=(v2.0-iphone v2.0-ipad v2.0-mac v2.0-ios v2.0-special)
PDIR=(01-iPhone 02-iPad 03-Mac 04-iOS-generic 05-Special)
TITLE=("Apple 官方壁纸 · iPhone 13→18 跟机原图"
       "Apple 官方壁纸 · iPad / iPadOS 14→27 原图"
       "Apple 官方壁纸 · macOS 10.15→27 与 MacBook / iMac 原图"
       "Apple 官方壁纸 · iOS 通用壁纸 12→27 原图"
       "Apple 官方壁纸 · WWDC / 发布会 / Pride / 店铺主题原图")

for i in "${!TAGS[@]}"; do
  tag=${TAGS[$i]}; plat=${PDIR[$i]}
  if ! gh release view "$tag" -R "$REPO" >/dev/null 2>&1; then
    echo "=== create $tag"
    gh release create "$tag" -R "$REPO" --title "${TITLE[$i]}" \
      --notes "每个 ZIP 对应一个壁纸套装，内含该套装全部原始分辨率原图（未压缩、未重新编码）。" \
      || { echo "!! create failed $tag"; continue; }
  fi
  echo "=== $tag ($plat)"
  up=$(gh release view "$tag" -R "$REPO" --json assets -q '.assets[].name' 2>/dev/null)
  for f in zips_out/${plat}__*.zip; do
    [ -e "$f" ] || continue
    b=$(basename "$f")
    if printf '%s\n' "$up" | grep -Fxq "$b"; then continue; fi
    ok=0
    for try in 1 2 3; do
      if out=$(timeout 900 gh release upload "$tag" "$f" -R "$REPO" --clobber 2>&1); then ok=1; break; fi
      echo "   retry$try $b :: $(printf '%s' "$out" | tail -1)"; sleep 8
    done
    if [ $ok -eq 1 ]; then echo "   up   $b  $(du -m "$f" | cut -f1) MB"; else echo "   FAIL $b"; fi
  done
done

echo "=== asset counts:"
tot=0
for tag in "${TAGS[@]}"; do
  n=$(gh release view "$tag" -R "$REPO" --json assets -q '.assets|length' 2>/dev/null || echo 0)
  echo "$tag: $n"; tot=$((tot+${n:-0}))
done
echo "TOTAL ASSETS: $tot / 76"
