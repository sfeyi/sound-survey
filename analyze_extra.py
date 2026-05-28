import pandas as pd
import numpy as np
import json
from scipy import stats
from statsmodels.stats.anova import AnovaRM

df_main = pd.read_csv('survey_results_50.csv')

# ============================================================
# 3a. 训练经验 ANOVA（混合设计：组间 training_years × 组内 instrument_type）
# ============================================================
all_trials = []
for _, row in df_main.iterrows():
    try:
        results = json.loads(row['test_results'])
    except:
        continue
    for t in results:
        all_trials.append({
            'user_id': row['user_id'],
            'training_years': row['training_years'],
            'instrument_type': t['instrument_type'],
            'valence_x': t['valence_x'],
            'arousal_y': t['arousal_y'],
        })
df = pd.DataFrame(all_trials)

# 按训练年限分组
print("="*60)
print("训练经验分组描述统计")
print("="*60)

for measure, name in [('valence_x', '效价'), ('arousal_y', '唤醒度')]:
    train_stats = df.groupby('training_years')[measure].agg(['mean', 'std', 'count']).round(3)
    train_stats = train_stats.reindex(['0', '1-3', '3-5', '>5'])
    print(f"\n--- {name} ---")
    print(train_stats.to_string())

# 独立样本 ANOVA（组间因子 training_years）
# 先按用户聚合（每人所有试次的均值）
user_agg = df.groupby(['user_id', 'training_years']).agg(
    val_mean=('valence_x', 'mean'),
    aro_mean=('arousal_y', 'mean')
).reset_index()

print("\n" + "="*60)
print("训练经验组间 ANOVA（每用户均值）")
print("="*60)

for measure, name in [('val_mean', '效价'), ('aro_mean', '唤醒度')]:
    groups = [user_agg[user_agg['training_years'] == t][measure].dropna() 
              for t in ['0', '1-3', '3-5', '>5']]
    f_stat, p_val = stats.f_oneway(*groups)
    print(f"\n{name}: F = {f_stat:.3f}, p = {p_val:.4f}")
    
    # Post hoc
    labels = ['0', '1-3', '3-5', '>5']
    for i, g1_name in enumerate(labels):
        for g2_name in labels[i+1:]:
            g1 = user_agg[user_agg['training_years'] == g1_name][measure].dropna()
            g2 = user_agg[user_agg['training_years'] == g2_name][measure].dropna()
            t, p = stats.ttest_ind(g1, g2, equal_var=False)
            sig = '***' if p < 0.05/6 else ''  # Bonferroni: 6 comparisons
            print(f"  {g1_name} vs {g2_name}: t={t:.3f}, p={p:.4f} {sig}")

# ============================================================
# 3b. 定性文字分析
# ============================================================
print("\n" + "="*60)
print("定性反馈摘要 (difference_perception)")
print("="*60)

# 只取真实用户（非合成）
real_feedback = df_main[~df_main['user_id'].str.startswith('synth_', na=False)]
texts = real_feedback['difference_perception'].dropna().tolist()
texts = [t.strip() for t in texts if t.strip() and t.strip() != '']

print(f"\n共 {len(texts)} 条有效反馈:\n")
for i, t in enumerate(texts):
    print(f"  [{i+1}] {t[:120]}{'...' if len(t)>120 else ''}")

# 简单关键词统计
keywords_cn = {
    '旋律更有情感': ['旋律', '情感', '情绪', '表达'],
    '单音纯粹': ['单音', '单一', '纯粹', '干净'],
    '无明显差异': ['没有', '差不多', '区别', '无差', '一样'],
    '旋律丰富': ['丰富', '多样', '变化', '复杂'],
}
print("\n--- 关键词归类 ---")
for label, words in keywords_cn.items():
    count = sum(1 for t in texts if any(w in t for w in words))
    print(f"  {label}: {count} 条")

print("\n[OK] 分析完成")
