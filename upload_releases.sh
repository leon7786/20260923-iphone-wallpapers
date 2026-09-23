#!/usr/bin/env bash
# Upload one ZIP per wallpaper set to GitHub Releases (one release per platform).
set -u
cd /root/Projects/20260922-iphone-wallpapers
REPO=leon7786/20260923-iphone-wallpapers

declare -A TITLE=(
  ["01-iPhone"]="Apple 官方壁纸 · iPhone 13→18 跟机原图"
  ["02-iPad"]="Apple 官方壁纸 · iPad / iPadOS 14→27 原图"
  ["03-Mac"]="Apple 官方壁纸 · macOS 10.15→27 与 MacBook / iMac 原图"
  ["04-iOS-generic"]="Apple 官方壁纸 · iOS 通用壁纸 12→27 原图"
  ["05-Special"]="Apple 官方壁纸 · WWDC / 发布会 / Pride / 店铺主题原图"
)
declare -A TAG=(
  ["01-iPhone"]="v2.0-iphone"
  ["02-iPad"]="v2.0-ipad"
  ["03-Mac"]="v2.0-mac"
  ["04-iOS-generic"]="v2.0-ios"
  ["05-Special"]="v2.0-special"
)

for plat in 01-iPhone 02-iPad 03-Mac 04-iOS-generic 05-Special; do
  tag=${TAG[$plat]}
  echo "=== $tag  ($plat) =============================================="
  if ! gh release view "$tag" -R "$REPO" >/dev/null 2>&1; then
    gh release create "$tag" -R "$REPO" \
      --title "${TITLE[$plat]}" \
      --notes "每个 ZIP 对应一个壁纸套装，内含该套装的全部原始分辨率原图（未压缩、未重新编码）。" \
      || { echo "!! create failed $tag"; continue; }
  fi
  for f in zips_out/${plat}__*.zip; do
    [ -e "$f" ] || continue
    ok=0
    for try in 1 2 3; do
      if gh release upload "$tag" "$f" -R "$REPO" --clobber >/dev/null 2>&1; then ok=1; break; fi
      echo "   retry$try $(basename "$f")"; sleep 5
    done
    if [ $ok -eq 1 ]; then echo "   up   $(basename "$f")  $(du -m "$f" | cut -f1) MB"
    else echo "   FAIL $(basename "$f")"; fi
  done
done
echo "=== done:"
for t in v2.0-iphone v2.0-ipad v2.0-mac v2.0-ios v2.0-special; do
  echo "$t: $(gh release view "$t" -R "$REPO" --json assets -q '.assets|length') assets"
done
