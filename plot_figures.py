import pandas as pd
import numpy as np
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import seaborn as sns

# ============================================================
# 读取数据
# ============================================================
df_main = pd.read_csv('survey_results_50.csv')
all_trials = []
for _, row in df_main.iterrows():
    try:
        results = json.loads(row['test_results'])
    except:
        continue
    for t in results:
        all_trials.append({
            'user_id': row['user_id'],
            'is_synth': row['user_id'].startswith('synth_'),
            'age': row['age'],
            'gender': row['gender'],
            'training_years': row['training_years'],
            'instrument_type': t['instrument_type'],
            'audio_condition': t['audio_condition'],
            'valence_x': t['valence_x'],
            'arousal_y': t['arousal_y'],
            'first_click_rt_ms': t.get('first_click_rt_ms', None),
            'final_decision_rt_ms': t.get('final_decision_rt_ms', None),
        })
df = pd.DataFrame(all_trials)

# 配色方案
colors = {
    'celeste': '#E8A87C',
    'flute': '#95B8D1',
    'harp': '#D4A5A5',
    'trumpet': '#E85D75',
    'viola': '#6C5B7B'
}
# seaborn 风格
sns.set_style("whitegrid")
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 11

# ============================================================
# 图 1: 情感环状散点图 (Russell's Circumplex)
# ============================================================
fig, ax = plt.subplots(figsize=(7, 7))

# 画象限分割线
ax.axhline(0, color='#ccc', linewidth=0.8, linestyle='--')
ax.axvline(0, color='#ccc', linewidth=0.8, linestyle='--')

# 象限标签
ax.text(0.85, 0.85, 'Excited\n亢奋', ha='center', va='center', fontsize=9, color='#999')
ax.text(-0.85, 0.85, 'Tense\n紧张', ha='center', va='center', fontsize=9, color='#999')
ax.text(-0.85, -0.85, 'Sad\n悲伤', ha='center', va='center', fontsize=9, color='#999')
ax.text(0.85, -0.85, 'Calm\n平静', ha='center', va='center', fontsize=9, color='#999')

# 按乐器画散点（小透明度，看分布）
for inst in ['harp', 'celeste', 'viola', 'flute', 'trumpet']:
    sub = df[df['instrument_type'] == inst]
    ax.scatter(sub['valence_x'], sub['arousal_y'],
               c=colors[inst], label=inst.capitalize(),
               alpha=0.3, s=15, edgecolors='none')

# 画各乐器的均值大圆点
for inst in ['harp', 'celeste', 'viola', 'flute', 'trumpet']:
    sub = df[df['instrument_type'] == inst]
    ax.scatter(sub['valence_x'].mean(), sub['arousal_y'].mean(),
               c=colors[inst], edgecolors='white', linewidth=2,
               s=250, zorder=5, marker='D')

ax.set_xlabel('Valence (Negative → Positive)', fontsize=12)
ax.set_ylabel('Arousal (Calm → Excited)', fontsize=12)
ax.set_title('Emotion Circumplex by Instrument', fontsize=14, fontweight='bold')
ax.set_xlim(-1, 1)
ax.set_ylim(-1, 1)
ax.legend(loc='upper left', frameon=True, fontsize=10)
plt.tight_layout()
fig.savefig('fig1_circumplex.png', dpi=200, bbox_inches='tight')
plt.close()
print('[OK] fig1_circumplex.png')

# ============================================================
# 图 2: 效价柱状图 (Valence barchart + error bars)
# ============================================================
fig, ax = plt.subplots(figsize=(8, 5))

stats_val = df.groupby('instrument_type')['valence_x'].agg(['mean', 'std']).reset_index()
stats_val = stats_val.sort_values('mean', ascending=False)
inst_order = stats_val['instrument_type'].tolist()

bars = ax.bar(range(len(inst_order)), stats_val['mean'],
              yerr=stats_val['std'], capsize=5,
              color=[colors[i] for i in inst_order],
              edgecolor='white', linewidth=1.5)

ax.set_xticks(range(len(inst_order)))
ax.set_xticklabels([i.capitalize() for i in inst_order], fontsize=11)
ax.set_ylabel('Mean Valence (± SD)', fontsize=12)
ax.set_title('Valence by Instrument (Higher = More Positive)', fontsize=14, fontweight='bold')
ax.axhline(0, color='#999', linewidth=0.8, linestyle='--')

# 标数值
for bar, val in zip(bars, stats_val['mean']):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
            f'{val:.3f}', ha='center', va='bottom', fontsize=9)

ax.set_ylim(-0.3, 0.5)
plt.tight_layout()
fig.savefig('fig2_valence_bar.png', dpi=200, bbox_inches='tight')
plt.close()
print('[OK] fig2_valence_bar.png')

# ============================================================
# 图 3: 唤醒柱状图 (Arousal barchart + error bars)
# ============================================================
fig, ax = plt.subplots(figsize=(8, 5))

stats_aro = df.groupby('instrument_type')['arousal_y'].agg(['mean', 'std']).reset_index()
stats_aro = stats_aro.sort_values('mean', ascending=False)
inst_order_aro = stats_aro['instrument_type'].tolist()

bars = ax.bar(range(len(inst_order_aro)), stats_aro['mean'],
              yerr=stats_aro['std'], capsize=5,
              color=[colors[i] for i in inst_order_aro],
              edgecolor='white', linewidth=1.5)

ax.set_xticks(range(len(inst_order_aro)))
ax.set_xticklabels([i.capitalize() for i in inst_order_aro], fontsize=11)
ax.set_ylabel('Mean Arousal (± SD)', fontsize=12)
ax.set_title('Arousal by Instrument (Higher = More Excited)', fontsize=14, fontweight='bold')
ax.axhline(0, color='#999', linewidth=0.8, linestyle='--')

for bar, val in zip(bars, stats_aro['mean']):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
            f'{val:.3f}', ha='center', va='bottom', fontsize=9)

plt.tight_layout()
fig.savefig('fig3_arousal_bar.png', dpi=200, bbox_inches='tight')
plt.close()
print('[OK] fig3_arousal_bar.png')

# ============================================================
# 图 4: RT 箱线图 (Reaction Time)
# ============================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# 过滤负值 RT
df_rt = df[df['first_click_rt_ms'] > 0].copy()

# 首次点击 RT
inst_rt = df_rt.groupby('instrument_type')['first_click_rt_ms'].apply(list).to_dict()
inst_order_rt = ['celeste', 'flute', 'harp', 'trumpet', 'viola']
bp1 = ax1.boxplot([inst_rt[i] for i in inst_order_rt],
                  patch_artist=True,
                  medianprops=dict(color='white', linewidth=1.5))

for patch, inst in zip(bp1['boxes'], inst_order_rt):
    patch.set_facecolor(colors[inst])

ax1.set_xticklabels([i.capitalize() for i in inst_order_rt])
ax1.set_ylabel('First Click RT (ms)', fontsize=12)
ax1.set_title('Hesitation Time by Instrument', fontsize=13, fontweight='bold')

# 最终决策 RT
inst_rt2 = df_rt.groupby('instrument_type')['final_decision_rt_ms'].apply(list).to_dict()
bp2 = ax2.boxplot([inst_rt2[i] for i in inst_order_rt],
                  patch_artist=True,
                  medianprops=dict(color='white', linewidth=1.5))

for patch, inst in zip(bp2['boxes'], inst_order_rt):
    patch.set_facecolor(colors[inst])

ax2.set_xticklabels([i.capitalize() for i in inst_order_rt])
ax2.set_ylabel('Final Decision RT (ms)', fontsize=12)
ax2.set_title('Final Decision Time by Instrument', fontsize=13, fontweight='bold')

plt.tight_layout()
fig.savefig('fig4_reaction_time.png', dpi=200, bbox_inches='tight')
plt.close()
print('[OK] fig4_reaction_time.png')

# ============================================================
# 图 5: 训练经验分组 (Valence & Arousal)
# ============================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

train_order = ['0', '1-3', '3-5', '>5']
train_labels = ['No Training\n(0 yr)', 'Beginner\n(1-3 yr)', 'Intermediate\n(3-5 yr)', 'Advanced\n(>5 yr)']

# Valence by training
train_val = df.groupby(['training_years', 'instrument_type'])['valence_x'].mean().reset_index()
for i, inst in enumerate(inst_order):
    sub = train_val[train_val['instrument_type'] == inst]
    sub = sub.set_index('training_years').reindex(train_order).reset_index()
    ax1.plot(range(len(train_order)), sub['valence_x'].fillna(0),
             'o-', color=colors[inst], label=inst.capitalize(), markersize=6)

ax1.set_xticks(range(len(train_order)))
ax1.set_xticklabels(train_labels, fontsize=9)
ax1.set_ylabel('Mean Valence', fontsize=12)
ax1.set_title('Valence by Training Experience', fontsize=13, fontweight='bold')
ax1.legend(fontsize=9)
ax1.axhline(0, color='#ccc', linewidth=0.8, linestyle='--')

# Arousal by training
train_aro = df.groupby(['training_years', 'instrument_type'])['arousal_y'].mean().reset_index()
for i, inst in enumerate(inst_order):
    sub = train_aro[train_aro['instrument_type'] == inst]
    sub = sub.set_index('training_years').reindex(train_order).reset_index()
    ax2.plot(range(len(train_order)), sub['arousal_y'].fillna(0),
             's-', color=colors[inst], label=inst.capitalize(), markersize=6)

ax2.set_xticks(range(len(train_order)))
ax2.set_xticklabels(train_labels, fontsize=9)
ax2.set_ylabel('Mean Arousal', fontsize=12)
ax2.set_title('Arousal by Training Experience', fontsize=13, fontweight='bold')
ax2.legend(fontsize=9)
ax2.axhline(0, color='#ccc', linewidth=0.8, linestyle='--')

plt.tight_layout()
fig.savefig('fig5_training_effect.png', dpi=200, bbox_inches='tight')
plt.close()
print('[OK] fig5_training_effect.png')

# ============================================================
# 图 6: 交互效应热力图 (Instrument × Condition)
# ============================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

val_hm = df.pivot_table(values='valence_x', index='instrument_type', columns='audio_condition', aggfunc='mean')
val_hm = val_hm.reindex(index=['celeste','flute','harp','trumpet','viola'])
val_hm = val_hm[['single','dorian','major','minor']]

sns.heatmap(val_hm, annot=True, fmt='.2f', cmap='RdYlGn', center=0,
            ax=ax1, cbar_kws={'label': 'Valence'}, linewidths=0.5)
ax1.set_title('Valence: Instrument × Condition', fontsize=12, fontweight='bold')
ax1.set_ylabel('')
ax1.set_xlabel('')

aro_hm = df.pivot_table(values='arousal_y', index='instrument_type', columns='audio_condition', aggfunc='mean')
aro_hm = aro_hm.reindex(index=['celeste','flute','harp','trumpet','viola'])
aro_hm = aro_hm[['single','dorian','major','minor']]

sns.heatmap(aro_hm, annot=True, fmt='.2f', cmap='coolwarm', center=0,
            ax=ax2, cbar_kws={'label': 'Arousal'}, linewidths=0.5)
ax2.set_title('Arousal: Instrument × Condition', fontsize=12, fontweight='bold')
ax2.set_ylabel('')
ax2.set_xlabel('')

plt.tight_layout()
fig.savefig('fig6_heatmap.png', dpi=200, bbox_inches='tight')
plt.close()
print('[OK] fig6_heatmap.png')

print('\nAll 6 figures saved to 问卷/ folder.')
