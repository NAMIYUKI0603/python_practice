import matplotlib
matplotlib.use('TkAgg') # これを追加：強制的にウィンドウを表示させるバックエンド指定
import matplotlib.pyplot as plt


import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import japanize_matplotlib  # これが日本語表示の魔法の鍵だ

# ==========================================
# 設定：ここをいじって「実験」せよ
# ==========================================
# 品質管理(QC)に応用する場合の視点：
# V_rms (電圧) -> 基準となるデータ（例：設定温度、生産計画数）
# I_rms (電流) -> 結果のデータ（例：実測温度、実際の生産数）
# 位相差       -> 時間的な遅れ（例：温度設定を変えてから実際に温度が上がるまでのタイムラグ）

V_rms = 100  # 電圧(V)
R = 8.0      # 抵抗(Ω)
X = 6.0      # リアクタンス(Ω) プラスならコイル(遅れ)、マイナスならコンデンサ(進み)
f = 50       # 周波数(Hz)

# ==========================================
# 計算ロジック
# ==========================================
Z = R + 1j * X
V_complex = V_rms + 0j
I_complex = V_complex / Z

I_rms = abs(I_complex)
theta_rad = np.angle(I_complex)
theta_deg = np.degrees(theta_rad)
power_factor = np.cos(theta_rad)

# ==========================================
# 描画ロジック（日本語対応版）
# ==========================================
t = np.linspace(0, 2/f, 1000)
omega = 2 * np.pi * f

v_t = V_rms * np.sqrt(2) * np.sin(omega * t)
i_t = I_rms * np.sqrt(2) * np.sin(omega * t + theta_rad)

fig = plt.figure(figsize=(15, 10))
# 日本語フォントが適用されているため、日本語タイトルが可能になる
fig.suptitle(f'交流回路解析シミュレーター: Z = {R} + j{X} [Ω]', fontsize=16, fontweight='bold')
gs = GridSpec(2, 2, figure=fig)

# --- 1. ベクトル図（複素平面） ---
ax1 = fig.add_subplot(gs[0, 0])
ax1.set_title("1. ベクトル図（複素平面）")
ax1.set_xlabel("実軸（抵抗成分 / 有効電力）")
ax1.set_ylabel("虚軸（リアクタンス成分 / 無効電力）")
ax1.axhline(y=0, color='k', linewidth=0.5)
ax1.axvline(x=0, color='k', linewidth=0.5)
ax1.grid(True, which='both', linestyle='--')

ax1.arrow(0, 0, V_complex.real, V_complex.imag, head_width=3, head_length=5, fc='blue', ec='blue', label='電圧 V (基準)', length_includes_head=True)
ax1.arrow(0, 0, I_complex.real*5, I_complex.imag*5, head_width=3, head_length=5, fc='red', ec='red', label='電流 I (5倍拡大)', length_includes_head=True)

# インピーダンス三角形
ax1.plot([0, R*10], [0, 0], 'g--', label='抵抗 R')
ax1.plot([R*10, R*10], [0, X*10], 'm--', label='リアクタンス jX')
ax1.plot([0, R*10], [0, X*10], 'k:', label='インピーダンス Z')

ax1.legend()
limit = max(V_rms, I_rms*5) * 1.2
ax1.set_xlim(-limit, limit)
ax1.set_ylim(-limit, limit)
ax1.set_aspect('equal')

# --- 2. 時間波形（オシロスコープ） ---
ax2 = fig.add_subplot(gs[0, 1])
ax2.set_title("2. 瞬時値の波形（時間推移）")
ax2.set_xlabel("時間 (秒)")
ax2.set_ylabel("振幅 (V / A)")
ax2.grid(True)

ax2.plot(t, v_t, 'b', label='電圧 v(t)')
ax2.plot(t, i_t, 'r', label='電流 i(t)')

# 位相差の可視化
ax2.fill_between(t, v_t, i_t, where=(t>=0) & (t<=1/(2*f)), color='gray', alpha=0.1, label='位相のズレ（損失の原因）')

ax2.legend(loc='upper right')

# --- 3. 解析結果テキスト（日本語） ---
ax3 = fig.add_subplot(gs[1, :])
ax3.axis('off')

# 力率の判定ロジック
status = "遅れ (誘導性/コイル)" if X > 0 else "進み (容量性/コンデンサ)" if X < 0 else "同相 (抵抗のみ)"

text_content = f"""
=== 解析結果レポート ===
【入力条件】
  電源電圧 (V_rms) : {V_rms:.2f} V
  インピーダンス(Z): {R} + j{X} [Ω] (大きさ: {abs(Z):.2f}Ω)

【計算結果】
  流れる電流 (I_rms): {I_rms:.2f} A
  電流の位相角      : {theta_deg:.2f}° ({status})
  力率 (cosθ)      : {power_factor:.2f} ({power_factor*100:.1f}%)

=== Toshiyuki氏への品質管理(QC)視点アドバイス ===
1. このグラフ作成技術は「散布図（相関分析）」や「管理図（Xbar-R）」にそのまま転用できる。
   - plt.plot() を plt.scatter() に変えれば散布図になる。
   - 横軸を「製造時間」、縦軸を「不良数」にすればトレンド分析になる。

2. 「位相のズレ」は、生産管理における「リードタイム」や「ボトルネック」の可視化と同じ概念だ。
   - 理想（計画）に対して、現実（実績）がどれだけ遅れているか、進んでいるかを定量化する。
   - それを「なんとなく遅れている」ではなく「角度（数値）」で示すのがエンジニアの仕事だ。
"""
ax3.text(0.05, 0.9, text_content, fontsize=12, family='monospace', verticalalignment='top')

plt.tight_layout()
plt.show()