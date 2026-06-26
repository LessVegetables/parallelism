import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import csv
import os
import sys

# Все числа берутся из benchmark_results/summary.csv (его пишет run.sh).
# Ничего не зашито вручную: правишь замеры -> перегенери summary.csv -> запусти этот скрипт.
#
# Формат summary.csv (самодокументирующийся, по колонке на каждый аргумент main.cpp):
#   mode,n,tol,iter_max,check,iters_run,error,time_s
#     mode      = host | multicore | gpu (по бинарю)
#     n         = сторона сетки NxN            (-n)
#     tol       = порог сходимости             (-t)
#     iter_max  = потолок итераций (вход)       (-i)
#     check     = error считается раз в C итер. (-c)
#     iters_run = фактически итераций (выход)
#     error     = итоговая ошибка (выход)
#     time_s    = время, с (выход)
#
# Графики:
#   chart_cpu.png   (ГРАФИК 1) host vs multicore по размеру сетки, check=1
#   chart_all.png   (ГРАФИК 3) host/multicore/gpu по размеру сетки, check=1
#   chart_check.png (ГРАФИК 4) multicore vs gpu на 1024x1024 по --check
# (бывший ГРАФИК 2 — этапы оптимизации GPU — убран: его данные в NVTX-профиле.)
#
# Путь к CSV можно переопределить первым аргументом (удобно для проверки).

CSV_PATH = sys.argv[1] if len(sys.argv) > 1 else os.path.join('benchmark_results', 'summary.csv')

rows = []
with open(CSV_PATH, newline='') as f:
    for r in csv.DictReader(f):
        rows.append({
            'mode':      r['mode'],
            'n':         int(r['n']),
            'tol':       float(r['tol']),
            'iter_max':  int(r['iter_max']),
            'check':     int(r['check']),
            'iters_run': int(r['iters_run']),
            'error':     float(r['error']),
            'time_s':    float(r['time_s']),
        })


def lookup(predicate, key_fn):
    """Строит {key_fn(row): time_s} по строкам, прошедшим predicate.
    При дублях ключа оставляет первое вхождение с предупреждением."""
    out = {}
    for r in rows:
        if not predicate(r):
            continue
        k = key_fn(r)
        if k in out:
            print(f'  [warn] дубль {k}: пропускаю time={r["time_s"]} '
                  f'(оставляю первое {out[k]})')
            continue
        out[k] = r['time_s']
    return out


# ============ ГРАФИКИ 1 и 3: сравнение режимов по размеру сетки (check=1) ============
# Берём только дефолтный режим проверки (check=1), иначе свип из graph 4 смешался бы
# с замерами по размеру сетки.
by_mode_size = lookup(lambda r: r['check'] == 1, lambda r: (r['mode'], r['n']))

sizes = sorted({n for (_, n) in by_mode_size})
size_labels = [f'{s}x{s}' for s in sizes]
x = np.arange(len(sizes))


def size_series(mode):
    """Времена режима по порядку sizes; отсутствующие замеры -> nan (бар не рисуется)."""
    return np.array([by_mode_size.get((mode, s), np.nan) for s in sizes])


host  = size_series('host')
multi = size_series('multicore')
gpu   = size_series('gpu')

# --- ГРАФИК 1: CPU one-core vs multicore ---
# host на 1024 не считали (слишком долго) -> там бара не будет (nan).
w = 0.35
fig, ax = plt.subplots(figsize=(8, 5))
ax.bar(x - w/2, host,  w, label='CPU one-core')
ax.bar(x + w/2, multi, w, label='CPU multicore')
ax.set_xticks(x); ax.set_xticklabels(size_labels)
ax.set_ylabel('Время, с')
ax.set_title('CPU one-core vs multicore')
ax.legend()
fig.tight_layout()
fig.savefig('chart_cpu.png', dpi=140)
print('chart_cpu.png')

# --- ГРАФИК 3: CPU one-core / multicore / GPU ---
w = 0.27
fig, ax = plt.subplots(figsize=(8, 5))
ax.bar(x - w, host,  w, label='CPU one-core')
ax.bar(x,     multi, w, label='CPU multicore')
ax.bar(x + w, gpu,   w, label='GPU')
ax.set_xticks(x); ax.set_xticklabels(size_labels)
ax.set_ylabel('Время, с')
ax.set_title('Сравнение CPU one-core / multicore / GPU')
ax.legend()
fig.tight_layout()
fig.savefig('chart_all.png', dpi=140)
print('chart_all.png')


# ============ ГРАФИК 4: multicore vs gpu на 1024x1024 по --check ============
# На 1024 решатель упирается в iter_max (не сходится), поэтому ВСЕ значения check
# гонят одинаковое число итераций — разница во времени = накладные расходы на
# подсчёт error. Чем реже считаем (больше check), тем быстрее.
GRID4 = 1024
by_mode_check = lookup(lambda r: r['n'] == GRID4, lambda r: (r['mode'], r['check']))

checks = sorted({c for (m, c) in by_mode_check if m in ('multicore', 'gpu')})
check_labels = [str(c) for c in checks]
xc = np.arange(len(checks))


def check_series(mode):
    return np.array([by_mode_check.get((mode, c), np.nan) for c in checks])


w = 0.35
fig, ax = plt.subplots(figsize=(8, 5))
# Цвета зафиксированы под палитру ГРАФИКА 3 (multicore=C1 оранжевый, gpu=C2 зелёный),
# чтобы режимы выглядели одинаково на всех графиках.
ax.bar(xc - w/2, check_series('multicore'), w, label='CPU multicore', color='C1')
ax.bar(xc + w/2, check_series('gpu'),       w, label='GPU',           color='C2')
ax.set_xticks(xc); ax.set_xticklabels(check_labels)
ax.set_xlabel('--check (error раз в N итераций)')
ax.set_ylabel('Время, с')
ax.set_title(f'Влияние --check на время ({GRID4}x{GRID4})')
ax.legend()
fig.tight_layout()
fig.savefig('chart_check.png', dpi=140)
print('chart_check.png')

print('Готово!')
