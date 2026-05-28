import pandas as pd
import numpy as np
from scipy import stats
from statsmodels.stats.anova import AnovaRM
import json

# ============================================================
# 1. 读取数据
# ============================================================
df_main = pd.read_csv('survey_results_50.csv')

# 展开 test_results JSON 列
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
            'listening_frequency': row['listening_frequency'],
            'training_years': row['training_years'],
            'instrument_exp': row['instrument'],
            'audio_id': t['audio_id'],
            'instrument_type': t['instrument_type'],
            'audio_condition': t['audio_condition'],
            'valence_x': t['valence_x'],
            'arousal_y': t['arousal_y'],
            'first_click_rt_ms': t.get('first_click_rt_ms', None),
            'final_decision_rt_ms': t.get('final_decision_rt_ms', None),
        })

df = pd.DataFrame(all_trials)
print(f"总数据点: {len(df)}, 用户数: {df['user_id'].nunique()}")
print(f"真实数据点: {(~df['is_synth']).sum()}, 合成数据点: {df['is_synth'].sum()}")

# ============================================================
# 2. 描述性统计
# ============================================================
print("\n" + "="*60)
print("描述性统计：效价 (Valence) 均值 ± 标准差")
print("="*60)

val_pivot = df.pivot_table(
    values='valence_x',
    index='instrument_type',
    columns='audio_condition',
    aggfunc=['mean', 'std', 'count']
).round(3)
print(val_pivot.to_string())

print("\n" + "="*60)
print("描述性统计：唤醒度 (Arousal) 均值 ± 标准差")
print("="*60)

aro_pivot = df.pivot_table(
    values='arousal_y',
    index='instrument_type',
    columns='audio_condition',
    aggfunc=['mean', 'std']
).round(3)
print(aro_pivot.to_string())

# 导出到 Excel
with pd.ExcelWriter('analysis_output.xlsx') as writer:
    # Sheet 1: 效价均值
    val_mean = df.pivot_table(values='valence_x', index='instrument_type', columns='audio_condition', aggfunc='mean').round(3)
    val_std = df.pivot_table(values='valence_x', index='instrument_type', columns='audio_condition', aggfunc='std').round(3)
    val_mean.to_excel(writer, sheet_name='效价均值')
    val_std.to_excel(writer, sheet_name='效价标准差')

    # Sheet 2: 唤醒均值
    aro_mean = df.pivot_table(values='arousal_y', index='instrument_type', columns='audio_condition', aggfunc='mean').round(3)
    aro_std = df.pivot_table(values='arousal_y', index='instrument_type', columns='audio_condition', aggfunc='std').round(3)
    aro_mean.to_excel(writer, sheet_name='唤醒均值')
    aro_std.to_excel(writer, sheet_name='唤醒标准差')

    # Sheet 3: RT 均值
    rt_first = df.pivot_table(values='first_click_rt_ms', index='instrument_type', columns='audio_condition', aggfunc='mean').round(0)
    rt_final = df.pivot_table(values='final_decision_rt_ms', index='instrument_type', columns='audio_condition', aggfunc='mean').round(0)
    rt_first.to_excel(writer, sheet_name='首次点击RT均值ms')
    rt_final.to_excel(writer, sheet_name='最终决策RT均值ms')

    # Sheet 4: 样本量
    counts = df.pivot_table(values='valence_x', index='instrument_type', columns='audio_condition', aggfunc='count')
    counts.to_excel(writer, sheet_name='样本量')

print("\n[OK] 描述统计已导出到 analysis_output.xlsx")

# ============================================================
# 3. 推断统计 - Two-way Repeated Measures ANOVA
# ============================================================
print("\n" + "="*60)
print("推断统计：两因素重复测量 ANOVA")
print("="*60)

# 准备长格式数据（每个用户×条件组合一个值）
# 按用户聚合：每个用户在每种乐器×条件下的平均效价/唤醒
for measure, name in [('valence_x', '效价'), ('arousal_y', '唤醒度')]:
    print(f"\n--- {name} ---")
    
    agg = df.groupby(['user_id', 'instrument_type', 'audio_condition'])[measure].mean().reset_index()
    agg = agg.rename(columns={measure: 'value'})
    
    try:
        model = AnovaRM(
            agg,
            depvar='value',
            subject='user_id',
            within=['instrument_type', 'audio_condition']
        ).fit()
        print(model.anova_table.round(4).to_string())
    except Exception as e:
        print(f"ANOVA 失败: {e}")

# ============================================================
# 4. 事后比较 - 乐器主效应的 Tukey HSD
# ============================================================
print("\n" + "="*60)
print("事后比较：乐器间效价差异 (独立样本 t-test, Bonferroni 校正)")
print("="*60)

instruments = df['instrument_type'].unique()
alpha = 0.05
n_comparisons = len(instruments) * (len(instruments) - 1) / 2
bonferroni_alpha = alpha / n_comparisons

print(f"Bonferroni 校正 alpha = {alpha} / {int(n_comparisons)} = {bonferroni_alpha:.4f}\n")

for measure, name in [('valence_x', '效价'), ('arousal_y', '唤醒度')]:
    print(f"--- {name} ---")
    for i, inst1 in enumerate(instruments):
        for inst2 in instruments[i+1:]:
            g1 = df[df['instrument_type'] == inst1][measure]
            g2 = df[df['instrument_type'] == inst2][measure]
            t_stat, p_val = stats.ttest_ind(g1, g2, equal_var=False)
            sig = '***' if p_val < bonferroni_alpha else ''
            print(f"  {inst1:8s} vs {inst2:8s}  t={t_stat:7.3f}  p={p_val:.4f} {sig}")

# ============================================================
# 5. 汇总
# ============================================================
print("\n" + "="*60)
print("分析完成！")
print("  - 数据点数:", len(df))
print("  - 用户数:", df['user_id'].nunique())
print("  - Excel 输出: analysis_output.xlsx (含 5 个 sheet)")
