#!/usr/bin/env bash
# Свипы NVTX-профилирования для ГРАФИК 2.1 и ГРАФИК 2.2.
# Запускать НА СЕРВЕРЕ с GPU (там есть nsys и собран heat_eq_gpu с USE_NVTX).
#
# Идея: метки NVTX (solve / calcNext / swap) в main.cpp сами по себе ничего не
# пишут — их слышит только профайлер. nsys пишет .nsys-rep, а `nsys stats
# --report nvtx_pushpop_sum` достаёт таблицу, где для каждой метки есть колонка
# Avg (ns) = среднее время ОДНОГО проталкивания метки = среднее время на ИТЕРАЦИЮ.
# Именно это среднее и есть величина для обоих графиков, поэтому профилировать
# до сходимости не нужно — гоним фиксированное короткое число итераций.
#
#   ГРАФИК 2.1: время этапа (calcNext / swap) от размера сетки n (check фиксирован)
#   ГРАФИК 2.2: время calcNext от --check на фиксированной сетке
#
# Использование:
#   ./profile_stages.sh            # дефолтные свипы
#   ITERS=2000 ./profile_stages.sh # переопределить число итераций на замер
set -u

BIN=build/heat_eq_gpu
OUTDIR=stage_profiles

# Сколько итераций гонять на каждый замер. Среднее на итерацию стабилизируется
# быстро, поэтому до сходимости считать незачем — так профили мелкие и быстрые.
ITERS=${ITERS:-1000}

# ГРАФИК 2.1: размеры сетки. check=1 фиксирован => calcNext всегда с reduction,
# линия calcNext честно сравнима между размерами.
SIZES_21=(128 256 512 1024 2048 4096)
CHECK_21=1

# ГРАФИК 2.2: фиксированная сетка, свип --check. Чем больше check, тем реже
# calcNext считает reduction(max:error) => среднее calcNext должно падать.
N_22=1024
CHECKS_22=(1 2 5 10 50 100 1000)

# -t 0 => условие error>tol никогда не выполнится ложно раньше времени, цикл
# отработает ровно ITERS итераций => одинаковое число сэмплов во всех замерах.
TOL=0

if ! command -v nsys >/dev/null 2>&1; then
    echo "nsys не найден — это надо запускать на сервере с NVIDIA HPC SDK / CUDA."
    exit 1
fi
if [ ! -x "$BIN" ]; then
    echo "$BIN не собран:  cmake -S . -B build && cmake --build build -j"
    exit 1
fi

# Имя отчёта зависит от версии nsys: новые — nvtx_pushpop_sum, старые — nvtx_sum.
REPORT=nvtx_pushpop_sum
nsys stats --help-reports 2>/dev/null | grep -q nvtx_pushpop_sum || REPORT=nvtx_sum

mkdir -p "$OUTDIR"

# profile_one <выходной_csv> <аргументы main.cpp...>
profile_one() {
    local csv=$1; shift
    local rep="${csv%.csv}"          # .nsys-rep рядом с csv
    echo "  -> nsys: $* "
    nsys profile --trace=nvtx,cuda --force-overwrite=true \
         -o "$rep" "$BIN" "$@" >/dev/null 2>&1
    nsys stats --report "$REPORT" --format csv "${rep}.nsys-rep" > "$csv" 2>/dev/null
}

echo "=== ГРАФИК 2.1: свип по размеру сетки (check=$CHECK_21, iters=$ITERS) ==="
for n in "${SIZES_21[@]}"; do
    profile_one "$OUTDIR/g21_n${n}.csv" -n "$n" -t "$TOL" -i "$ITERS" -c "$CHECK_21"
done

echo "=== ГРАФИК 2.2: свип по --check (n=$N_22, iters=$ITERS) ==="
for c in "${CHECKS_22[@]}"; do
    profile_one "$OUTDIR/g22_c${c}.csv" -n "$N_22" -t "$TOL" -i "$ITERS" -c "$c"
done

echo
echo "Готово. CSV-файлы в $OUTDIR/."
echo

