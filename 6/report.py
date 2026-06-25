import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

# после `cmake --build build`:
#   ./build/heat_eq_host      -n 128   (и 256, 512)
#   ./build/heat_eq_multicore -n 128   (256, 512, 1024)
#   ./build/heat_eq_gpu       -n 128   (256, 512, 1024)
# смотреть "Time" из вывода.

grids = ['128x128', '256x256', '512x512', '1024x1024']

cpu_one   = [1.391, 19.632, 262.536, None]   # one-core: 1024 обычно слишком медленно -> None
cpu_multi = [3.427,  9.375,  37.061, 237.908]
gpu       = [1.062,  3.428,  11.458,  62.297]

# Этапы оптимизации GPU на одной сетке:
#   Этап 1 — наивно, без data-региона (копирование host<->device каждую итерацию)
#   Этап 2 — добавлен #pragma acc data (один copyin на весь решатель)
#   Этап 3 — error считается раз в C итераций (флаг --check, напр. -c 100)
stages      = ['Этап 1\n(без data)', 'Этап 2\n(data-регион)', 'Этап 3\n(--check 100)']
stage_times = [337.0, 11.453, 3.916]


# ============ ГРАФИК 1: CPU one vs multi ============
x = np.arange(3)  # только 128, 256, 512
w = 0.35
fig, ax = plt.subplots(figsize=(8, 5))
ax.bar(x - w/2, cpu_one[:3],   w, label='CPU one-core')
ax.bar(x + w/2, cpu_multi[:3], w, label='CPU multicore')
ax.set_xticks(x); ax.set_xticklabels(grids[:3])
ax.set_ylabel('Время, с')
ax.set_title('CPU one-core vs multicore')
ax.legend()
fig.tight_layout()
fig.savefig('chart_cpu.png', dpi=140)
print('chart_cpu.png')


# ============ ГРАФИК 2: этапы оптимизации GPU ============
fig, ax = plt.subplots(figsize=(7, 5))
ax.bar(stages, stage_times, color=['#e74c3c', '#3498db', '#2ecc71'])
ax.set_ylabel('Время, с')
ax.set_title('Этапы оптимизации GPU (512x512)')
for i, t in enumerate(stage_times):
    ax.text(i, t + max(stage_times) * 0.01, f'{t:.1f} с', ha='center')
fig.tight_layout()
fig.savefig('chart_stages.png', dpi=140)
print('chart_stages.png')


# ============ ГРАФИК 3: CPU one / CPU multi / GPU ============
x = np.arange(3)
w = 0.27
fig, ax = plt.subplots(figsize=(8, 5))
ax.bar(x - w,   cpu_one[:3],   w, label='CPU one-core')
ax.bar(x,       cpu_multi[:3], w, label='CPU multicore')
ax.bar(x + w,   gpu[:3],       w, label='GPU')
ax.set_xticks(x); ax.set_xticklabels(grids[:3])
ax.set_ylabel('Время, с')
ax.set_title('Сравнение CPU one-core / multicore / GPU')
ax.legend()
fig.tight_layout()
fig.savefig('chart_all.png', dpi=140)
print('chart_all.png')

print('Готово!')
