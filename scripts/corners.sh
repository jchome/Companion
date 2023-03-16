unset x y w h

eval $(xwininfo -id  $(xprop -root 32x '\t$0' _NET_ACTIVE_WINDOW | cut -f 2) |
  sed -n -e "s/^ \+Absolute upper-left X: \+\([0-9]\+\).*/x=\1/p" \
          -e "s/^ \+Absolute upper-left Y: \+\([0-9]\+\).*/y=\1/p" \
          -e "s/^ \+Width: \+\([0-9]\+\).*/w=\1/p" \
          -e "s/^ \+Height: \+\([0-9]\+\).*/h=\1/p" )
echo "$x $y $w $h"