#!/usr/bin/env python3
# Строит ГРАФИК 2.1 и ГРАФИК 2.2 по NVTX-профилям, которые делает profile_stages.sh.
#
#   ГРАФИК 2.1 (chart_stage_n.png)     — среднее время этапа на итерацию
#                                        (calcNext / swap) от размера сетки n.
#   ГРАФИК 2.2 (chart_stage_check.png) — среднее время calcNext на итерацию
#                                        от --check (на фиксированной сетке).
#
# Вход — папка с CSV из `nsys stats --report nvtx_pushpop_sum --format csv`:
#   g21_n<N>.csv  — замеры для свипа по сетке
#   g22_c<C>.csv  — замеры для свипа по --check
# Ключевая колонка nsys — Avg (ns): среднее время ОДНОГО проталкивания метки,
# т.е. среднее время этапа на одну итерацию (не зависит от числа итераций).
#
#   python report_stages.py [stage_profiles]
import sys, os, csv, glob, re
import matplotlib
matplotlib.use('Agg')
import matplotlib.ticker
import matplotlib.pyplot as plt

SRC = sys.argv[1] if len(sys.argv) > 1 else 'stage_profiles'

# --- разбор одного nsys-CSV -------------------------------------------------
# В CSV есть мусорные строки до таблицы — ищем заголовок по "Total Time",
# колонки находим по имени (их набор/порядок зависит от версии nsys).
def parse_nvtx(path):
    rows = list(csv.reader(open(path, newline='')))
    hdr_i = next(i for i, r in enumerate(rows) if any('Total Time' in c for c in r))
    header = rows[hdr_i]
    body   = [r for r in rows[hdr_i + 1:] if len(r) == len(header) and any(r)]

    def col(name):
        return next(i for i, c in enumerate(header) if name in c)

    i_range = col('Range')
    i_tot   = col('Total Time')
    try:
        i_avg = col('Avg')          # Avg (ns) — среднее на одно проталкивание
    except StopIteration:
        i_avg = None
    try:
        i_inst = col('Instances')   # сколько раз метка проталкивалась
    except StopIteration:
        i_inst = None

    out = {}
    for r in body:
        name = r[i_range].strip()
        f = lambda i: float(r[i].replace(',', ''))
        # предпочитаем готовый Avg; на старом отчёте — Total/Instances
        if i_avg is not None:
            avg = f(i_avg)
        else:
            inst = f(i_inst) if i_inst is not None else 0
            avg = f(i_tot) / inst if inst else 0.0
        out[name] = avg   # нс
    return out

def collect(pattern, key_re):
    data = []
    for path in glob.glob(os.path.join(SRC, pattern)):
        m = re.search(key_re, os.path.basename(path))
        if not m:
            continue
        t = parse_nvtx(path)
        data.append((int(m.group(1)), t.get('calcNext', 0.0), t.get('swap', 0.0)))
    data.sort()
    return data

NS_US = 1e-3   # нс -> мкс

# ============================ ГРАФИК 2.1 ====================================
d21 = collect('g21_n*.csv', r'g21_n(\d+)\.csv')
if d21:
    ns   = [r[0] for r in d21]
    calc = [r[1] * NS_US for r in d21]
    swap = [r[2] * NS_US for r in d21]

    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.plot(ns, calc, 'o-', color='#3498db', label='calcNext (5-точечный стенсил)')
    ax.plot(ns, swap, 's-', color='#2ecc71', label='swap (копирование)')
    ax.set_xscale('log', base=2)
    ax.set_yscale('log')
    ax.set_xticks(ns)
    ax.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
    ax.set_xlabel('Размер сетки n (NxN)')
    ax.set_ylabel('Среднее время этапа на итерацию, мкс')
    ax.set_title('ГРАФИК 2.1 — время этапов решателя от размера сетки (GPU, check=1)')
    ax.grid(True, which='both', ls=':', alpha=0.5)
    ax.legend()
    for x, y in zip(ns, calc):
        ax.annotate(f'{y:.3g}', (x, y), textcoords='offset points',
                    xytext=(0, 7), ha='center', fontsize=8)
    fig.tight_layout()
    fig.savefig('chart_stage_n.png', dpi=140)
    print('saved chart_stage_n.png  (n:', ns, ')')
else:
    print('нет g21_n*.csv в', SRC, '— пропускаю ГРАФИК 2.1')

# ============================ ГРАФИК 2.2 ====================================
N_22 = 1024   # см. N_22 в profile_stages.sh
d22 = collect('g22_c*.csv', r'g22_c(\d+)\.csv')
if d22:
    checks = [r[0] for r in d22]
    calc   = [r[1] * NS_US for r in d22]
    swap   = [r[2] * NS_US for r in d22]

    fig, ax = plt.subplots(figsize=(8, 5.5))
    ax.plot(checks, calc, 'o-', color='#3498db', label='calcNext (среднее на итерацию)')
    # swap не зависит от check — рисуем как опорную горизонталь
    swap_ref = sum(swap) / len(swap)
    ax.axhline(swap_ref, color='#2ecc71', ls='--',
               label=f'swap ≈ {swap_ref:.3g} мкс (от check не зависит)')
    # асимптота — стоимость дешёвой ветки calcNext (без reduction) при большом check
    ax.axhline(min(calc), color='#95a5a6', ls=':',
               label=f'calcNext без reduction ≈ {min(calc):.3g} мкс')
    ax.set_xscale('log')
    ax.set_xticks(checks)
    ax.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
    ax.set_xlabel('--check (error считается раз в C итераций)')
    ax.set_ylabel('Среднее время calcNext на итерацию, мкс')
    ax.set_title(f'ГРАФИК 2.2 — влияние --check на calcNext (GPU, n={N_22})')
    ax.grid(True, which='both', ls=':', alpha=0.5)
    ax.legend()
    for x, y in zip(checks, calc):
        ax.annotate(f'{y:.3g}', (x, y), textcoords='offset points',
                    xytext=(0, 7), ha='center', fontsize=8)
    fig.tight_layout()
    fig.savefig('chart_stage_check.png', dpi=140)
    print('saved chart_stage_check.png  (check:', checks, ')')
else:
    print('нет g22_c*.csv в', SRC, '— пропускаю ГРАФИК 2.2')
