#!/usr/bin/env bash
# Прогон всех замеров для лабы 6 (уравнение теплопроводности, OpenACC).
#
# ВАЖНО: замеры идут ПОСЛЕДОВАТЕЛЬНО, не параллельно. Если гонять их
# одновременно, версии дерутся за CPU/память и тайминги становятся
# недостоверными (а ещё runs с одинаковым -n затирают result_N.txt).
#
# Использование:
#   ./run.sh                 # дефолтные сетки
#   ./run.sh 256 512 1024    # свои размеры
#
# Перед запуском собери проект:  cmake -S . -B build && cmake --build build -j

set -u

BUILD=build
OUTDIR=benchmark_results
mkdir -p "$OUTDIR"

# Сетки можно переопределить аргументами командной строки.
SIZES=("$@")
[ ${#SIZES[@]} -eq 0 ] && SIZES=(128 256 512 1024)

# режим -> макс. сетка, которую для него вообще запускаем
#   host (1 ядро) на 1024 считает слишком долго -> пропускаем
declare -A MAXSIZE=( [host]=512 [multicore]=100000 [gpu]=100000 )

SUMMARY="$OUTDIR/summary.csv"
echo "mode,size,iterations,error,time_s" > "$SUMMARY"

run_one() {
    local mode=$1 n=$2; shift 2
    local bin="$BUILD/heat_eq_${mode}"
    local extra=("$@")

    if [ ! -x "$bin" ]; then
        echo "  [skip] $bin не найден — собери проект (cmake --build $BUILD)"
        return
    fi
    if [ "$n" -gt "${MAXSIZE[$mode]}" ]; then
        echo "  [skip] $mode -n $n (слишком большая сетка для этого режима)"
        return
    fi

    local log="$OUTDIR/${mode}_${n}.log"
    echo "  -> $mode  -n $n  ${extra[*]}"
    # каждый run в своей подпапке, чтобы result_N.txt не затирались
    local wd="$OUTDIR/run_${mode}_${n}"
    mkdir -p "$wd"
    ( cd "$wd" && "$(cd "$OLDPWD" && pwd)/$bin" -n "$n" "${extra[@]}" ) >"$log" 2>&1

    local iters err time
    iters=$(grep -m1 'Iterations:' "$log" | awk '{print $2}')
    err=$(  grep -m1 'Error:'      "$log" | awk '{print $2}')
    time=$( grep -m1 'Time:'       "$log" | awk '{print $2}')
    echo "     iters=$iters  error=$err  time=${time}s"
    echo "$mode,$n,$iters,$err,$time" >> "$SUMMARY"
}

echo "=== CPU one-core (host) ==="
for n in "${SIZES[@]}"; do run_one host "$n"; done

echo "=== CPU multicore ==="
for n in "${SIZES[@]}"; do run_one multicore "$n"; done

echo "=== GPU ==="
for n in "${SIZES[@]}"; do run_one gpu "$n"; done

# Этап 3 оптимизации: GPU с проверкой ошибки раз в 100 итераций
echo "=== GPU --check 100 (этап оптимизации) ==="
run_one gpu 512 -c 100

echo
echo "Готово. Сводка: $SUMMARY"
echo "----------------------------------------"
column -t -s, "$SUMMARY" 2>/dev/null || cat "$SUMMARY"
