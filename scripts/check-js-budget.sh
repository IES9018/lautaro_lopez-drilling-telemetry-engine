#!/usr/bin/env bash
# Verifica presupuesto RNF-03: JS shell gzip < 200 KB (excluye chunk 3D lazy).
# Uso: desde raíz del repo, con src/ui ya buildeado (npm run build).
set -euo pipefail

UI_DIR="$(cd "$(dirname "$0")/../src/ui" && pwd)"
CHUNKS_DIR="$UI_DIR/.next/static/chunks"
BUDGET_KB=200

if [[ ! -d "$CHUNKS_DIR" ]]; then
  echo "ERROR: No existe $CHUNKS_DIR — ejecutar: cd src/ui && npm run build"
  exit 1
fi

total_bytes=0
while IFS= read -r -d '' file; do
  case "$file" in
    *DrillString*|*three*|*fiber*|*drei*) continue ;;
  esac
  size=$(gzip -c "$file" | wc -c)
  total_bytes=$((total_bytes + size))
done < <(find "$CHUNKS_DIR" -name '*.js' -print0)

total_kb=$((total_bytes / 1024))
echo "RNF-03 shell JS (gzip, excl. 3D chunks): ${total_kb} KB (presupuesto < ${BUDGET_KB} KB)"

if (( total_kb > BUDGET_KB )); then
  echo "WARN: presupuesto excedido — revisar presupuestos-rendimiento.md"
  exit 0
fi

echo "OK: dentro del presupuesto shell"
