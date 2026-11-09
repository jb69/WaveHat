#!/bin/zsh
# Regenerate the WaveHat KiCad project end to end: schematic + ERC, placement, Freerouting, import, DRC.
# Needs KiCad 10, Java (brew install openjdk) and the Freerouting jar (FREEROUTING=/path/to/freerouting.jar).
set -e
cd "$(dirname "$0")"
PY=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3
K=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli
J=${JAVA:-/opt/homebrew/opt/openjdk/bin/java}
FR=${FREEROUTING:?set FREEROUTING to the freerouting jar}
python3 -I gen_schematic.py
$K sch erc --severity-all --format json -o reports/erc.json wavehat.kicad_sch 2>/dev/null | grep Found
$PY gen_pcb.py place 2>&1 | grep -v -E "Fontconfig|assert"
# Route, import and check; if DRC is not clean, start again from a freshly placed board with a different number of
# routing passes (Freerouting's result depends on it), up to six times
attempt=0
for passes in ${PASSES:-100} 150 200 80 250 120; do
  attempt=$((attempt + 1))
  if [ $attempt -gt 1 ]; then $PY gen_pcb.py place 2>&1 | grep -v -E "Fontconfig|assert" > /dev/null; fi
  rm -f wavehat.ses
  $J -Djava.awt.headless=true -jar $FR -de wavehat.dsn -do wavehat.ses -mp $passes --gui.enabled=false > /tmp/wavehat-freerouting.log 2>&1
  grep -E "Auto-routing stage completed" /tmp/wavehat-freerouting.log | sed 's/.*final score/final score/' | cut -c1-80
  $PY gen_pcb.py import 2>&1 | grep -v -E "Fontconfig|assert"
  $K pcb drc --severity-all --schematic-parity --format json -o reports/drc.json wavehat.kicad_pcb 2>/dev/null | grep Found
  if python3 -I -c "import json,sys; d=json.load(open('reports/drc.json')); sys.exit(any(v['severity']=='error' for v in d['violations']) or bool(d.get('unconnected_items')) or bool(d.get('schematic_parity')))"; then
    echo "DRC clean on routing attempt $attempt ($passes passes)"; break
  fi
  echo "routing attempt $attempt ($passes passes) not clean"
  [ $attempt = 6 ] && { echo "giving up: fix by hand in KiCad"; exit 1; }
done
# fabrication outputs and renders
mkdir -p fab/gerbers img
$K pcb export gerbers --use-drill-file-origin -o fab/gerbers/ --layers F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts wavehat.kicad_pcb >/dev/null 2>&1
$K pcb export drill --drill-origin plot -o fab/gerbers/ wavehat.kicad_pcb >/dev/null 2>&1
$K pcb export pos --side front --format csv --units mm --exclude-dnp --use-drill-file-origin -o fab/wavehat-cpl-top.csv wavehat.kicad_pcb >/dev/null 2>&1
$K pcb export pos --side back --format csv --units mm --exclude-dnp --use-drill-file-origin -o fab/wavehat-cpl-bottom.csv wavehat.kicad_pcb >/dev/null 2>&1
$K sch export bom --fields 'Reference,Value,Footprint,MPN,${QUANTITY},${DNP}' --labels 'Designator,Value,Footprint,MPN,Qty,DNP' --group-by 'Value,Footprint,MPN,${DNP}' --ref-range-delimiter '' -o fab/wavehat-bom.csv wavehat.kicad_sch >/dev/null 2>&1
$K sch export pdf -o wavehat-schematic.pdf wavehat.kicad_sch >/dev/null 2>&1
(cd fab/gerbers && rm -f ../wavehat-gerbers.zip && zip -q ../wavehat-gerbers.zip *)
$K pcb render --side top --rotate '-35,0,25' --quality high --width 1400 --height 1000 --background opaque -o img/wavehat-3d-angle.png wavehat.kicad_pcb >/dev/null 2>&1
$K pcb render --side top --quality high --width 1000 --height 1600 --background opaque -o img/wavehat-3d-top.png wavehat.kicad_pcb >/dev/null 2>&1
$K pcb render --side bottom --quality high --width 1000 --height 1600 --background opaque -o img/wavehat-3d-bottom.png wavehat.kicad_pcb >/dev/null 2>&1
python3 -I gen_docs.py
python3 -I gen_seeed.py
python3 -I gen_jlcpcb.py
echo "outputs in fab/ and img/"
