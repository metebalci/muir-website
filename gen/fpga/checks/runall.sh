#!/bin/sh
# Run every geometric checker against one pages directory ($1), with $2 as the base for the comparing ones.
D=$1; B=$2; C=$(dirname "$0")
for s in check_geom.py check_text.py check_same.py check_cross_marks.py; do echo "== $s"; python3 $C/$s "$D" 2>&1; echo "exit $?"; done
echo "== check_seq.py"; python3 $C/check_seq.py "$D/booting.html" 2>&1; echo "exit $?"
echo "== check_cross.py"; python3 $C/check_cross.py "$B" "$D" 2>&1; echo "exit $?"
echo "== check_points.py"; python3 $C/check_points.py "$B" "$D" 2>&1; echo "exit $?"
echo "== check_tags.py"; python3 $C/check_tags.py "$D" 2>&1; echo "exit $?"
