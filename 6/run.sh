#!/usr/bin/env bash
# Прогон всех замеров для лабы 6 (уравнение теплопроводности, OpenACC).
#
# ВАЖНО: замеры идут ПОСЛЕДОВАТЕЛЬНО, не параллельно. Если гонять их
# одновременно, версии дерутся за CPU/память и тайминги становятся
# недостоверными (а ещё runs с одинаковым -n затирают result_N.txt).
#
# Использование:
#   ./run.sh                 # дефолтные сетки
#   ./run.sh 256 512 1024    # свои размеры для основного свипа
#
# Перед запуском собери проект:  cmake -S . -B build && cmake --build build -j

set -u

BUILD=build
OUTDIR=benchmark_results
mkdir -p "$OUTDIR"

# --- Параметры main.cpp (захардкожены здесь, чтобы каждая строка summary.csv
#     была самодостаточной). Должны совпадать с default_value(...) в main.cpp:
#       -t/--tolerance   1e-6
#       -i/--iterations  1000000
#       -c/--check       1   (для основного свипа; для graph 4 свипаем отдельно)
TOL=1e-6
ITER_MAX=1000000

# Сетки можно переопределить аргументами командной строки (основной свип).
SIZES=("$@")
[ ${#SIZES[@]} -eq 0 ] && SIZES=(128 256 512 1024)

# режим -> макс. сетка, которую для него вообще запускаем
#   host (1 ядро) на 1024 считает слишком долго -> пропускаем
declare -A MAXSIZE=( [host]=512 [multicore]=100000 [gpu]=100000 )

# summary.csv самодокументирующийся: одна колонка на каждый аргумент main.cpp
# (mode/n/tol/iter_max/check) + результаты прогона (iters_run/error/time_s).
#   mode      — host/multicore/gpu (определяется по бинарю, не аргумент main.cpp)
#   n         — -n/--size
#   tol       — -t/--tolerance
#   iter_max  — -i/--iterations (ПОТОЛОК итераций, вход)
#   check     — -c/--check (считать error раз в C итераций)
#   iters_run — фактически выполнено итераций (вывод "Iterations:")
#   error     — итоговая ошибка (вывод "Error:")
#   time_s    — время (вывод "Time:")
SUMMARY="$OUTDIR/summary.csv"
echo "mode,n,tol,iter_max,check,iters_run,error,time_s" > "$SUMMARY"

# run_one <mode> <n> <check>
run_one() {
    local mode=$1 n=$2 check=$3
    local bin="$BUILD/heat_eq_${mode}"

    if [ ! -x "$bin" ]; then
        echo "  [skip] $bin не найден — собери проект (cmake --build $BUILD)"
        return
    fi
    if [ "$n" -gt "${MAXSIZE[$mode]}" ]; then
        echo "  [skip] $mode -n $n (слишком большая сетка для этого режима)"
        return
    fi

    # каждый (mode,n,check) — в своём логе и подпапке, чтобы ничего не затиралось
    local tag="${mode}_n${n}_c${check}"
    local log="$OUTDIR/${tag}.log"
    local wd="$OUTDIR/run_${tag}"
    mkdir -p "$wd"

    echo "  -> $mode  -n $n  -c $check"
    # -t и -i передаём явно = дефолты main.cpp, чтобы записанное в CSV
    # в точности совпадало с тем, с чем реально запускались.
    ( cd "$wd" && "$(cd "$OLDPWD" && pwd)/$bin" \
        -n "$n" -t "$TOL" -i "$ITER_MAX" -c "$check" ) >"$log" 2>&1

    local iters err time
    iters=$(grep -m1 'Iterations:' "$log" | awk '{print $2}')
    err=$(  grep -m1 'Error:'      "$log" | awk '{print $2}')
    time=$( grep -m1 'Time:'       "$log" | awk '{print $2}')
    echo "     iters=$iters  error=$err  time=${time}s"
    echo "$mode,$n,$TOL,$ITER_MAX,$check,$iters,$err,$time" >> "$SUMMARY"
}

# ============ Основной свип: сравнение режимов по размеру сетки (check=1) ============
echo "=== CPU one-core (host) ==="
for n in "${SIZES[@]}"; do run_one host "$n" 1; done

echo "=== CPU multicore ==="
for n in "${SIZES[@]}"; do run_one multicore "$n" 1; done

echo "=== GPU ==="
for n in "${SIZES[@]}"; do run_one gpu "$n" 1; done

# ============ Свип --check на 1024 (graph 4: multicore vs gpu) ============
# check=1 для multicore/gpu 1024 уже посчитан в основном свипе выше.
echo "=== Свип --check на 1024x1024 (graph 4) ==="
for c in 100 1000 10000; do
    run_one multicore 1024 "$c"
    run_one gpu       1024 "$c"
done

echo
echo "Готово. Сводка: $SUMMARY"
echo "----------------------------------------"
column -t -s, "$SUMMARY" 2>/dev/null || cat "$SUMMARY"
