import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

# ==========================================
# 設定：ここをいじって「実験」せよ
# ==========================================
# 電圧(V)の実効値
V_rms = 100 
# インピーダンス Z = R + jX (オーム)
# 抵抗(R): 電気エネルギーを熱として消費する成分
R = 8.0  
# リアクタンス(X): コイルやコンデンサがエネルギーを行き来させる成分
# 正の値なら誘導性(コイル)、負の値なら容量性(コンデンサ)
X = 6.0  

# 周波数(Hz)
f = 50 

# ==========================================
# 計算ロジック（電験の試験で手計算する部分）
# ==========================================

# 1. 複素インピーダンス Z
Z = R + 1j * X

# 2. 電流 I (オームの法則 V = IZ => I = V/Z)
# 位相の基準を電圧(角度0)とする
V_complex = V_rms + 0j
I_complex = V_complex / Z

# 3. 各種値の取得
I_rms = abs(I_complex)        # 電流の大きさ(絶対値)
theta_rad = np.angle(I_complex) # 電流の位相角(ラジアン)
theta_deg = np.degrees(theta_rad) # 電流の位相角(度数法)
power_factor = np.cos(theta_rad) # 力率(cosθ)

# ==========================================
# 描画ロジック（Pythonにやらせる部分）
# ==========================================

# 時間軸の作成 (0から2周期分)
t = np.linspace(0, 2/f, 1000)
omega = 2 * np.pi * f

# 正弦波の計算 (瞬時値 v(t), i(t))
# ※最大値 = 実効値 * √2
v_t = V_rms * np.sqrt(2) * np.sin(omega * t)
i_t = I_rms * np.sqrt(2) * np.sin(omega * t + theta_rad)

# プロットエリアの設定
fig = plt.figure(figsize=(15, 10))
fig.suptitle(f'AC Circuit Analysis: Z = {R} + j{X} [Ω]', fontsize=16, fontweight='bold')
gs = GridSpec(2, 2, figure=fig)

# --- 1. 複素平面（ベクトル図） ---
ax1 = fig.add_subplot(gs[0, 0])
ax1.set_title("1. Vector Diagram (Complex Plane)")
ax1.set_xlabel("Real Axis (Resistance component)")
ax1.set_ylabel("Imaginary Axis (Reactance component)")
ax1.axhline(y=0, color='k', linewidth=0.5)
ax1.axvline(x=0, color='k', linewidth=0.5)
ax1.grid(True, which='both', linestyle='--')

# 電圧ベクトル（基準）
ax1.arrow(0, 0, V_complex.real, V_complex.imag, head_width=3, head_length=5, fc='blue', ec='blue', label='Voltage (V)', length_includes_head=True)
# 電流ベクトル（計算結果）
# 見やすくするために電流ベクトルを少し拡大表示する場合があるが、ここはそのまま表示
ax1.arrow(0, 0, I_complex.real*5, I_complex.imag*5, head_width=3, head_length=5, fc='red', ec='red', label='Current (I) x5 scale', length_includes_head=True)

# インピーダンス三角形の描画 (R, X, Zの関係)
ax1.plot([0, R*10], [0, 0], 'g--', label='Resistance (R)')
ax1.plot([R*10, R*10], [0, X*10], 'm--', label='Reactance (jX)')
ax1.plot([0, R*10], [0, X*10], 'k:', label='Impedance (Z)')

ax1.legend()
limit = max(V_rms, I_rms*5) * 1.2
ax1.set_xlim(-limit, limit)
ax1.set_ylim(-limit, limit)
ax1.set_aspect('equal')

# --- 2. 時間波形（オシロスコープの映像） ---
ax2 = fig.add_subplot(gs[0, 1])
ax2.set_title("2. Time Domain Waveforms (Sine Waves)")
ax2.set_xlabel("Time (s)")
ax2.set_ylabel("Amplitude")
ax2.grid(True)

ax2.plot(t, v_t, 'b', label='Voltage v(t)')
ax2.plot(t, i_t, 'r', label='Current i(t)')

# 位相差の可視化
ax2.fill_between(t, v_t, i_t, where=(t>=0) & (t<=1/(2*f)), color='gray', alpha=0.1, label='Phase Difference')

ax2.legend(loc='upper right')

# --- 3. 解説テキスト ---
ax3 = fig.add_subplot(gs[1, :])
ax3.axis('off')
text_content = f"""
=== Analysis Result ===
Applied Voltage (V_rms): {V_rms:.2f} V
Impedance (Z): {R} + j{X} = {abs(Z):.2f} ∠ {np.degrees(np.angle(Z)):.2f}° Ω

Calculated Current (I_rms): {I_rms:.2f} A
Current Phase Angle: {theta_deg:.2f}°
Power Factor (cosθ): {power_factor:.2f} ({(lambda x: 'Lagging' if x>0 else 'Leading' if x<0 else 'Unity')(X)})

=== What Toshiyuki Needs to See ===
1. Look at the Vector Diagram (Top Left).
   - The Voltage (Blue) is on the Real axis (Right).
   - The Current (Red) is pointing {('DOWN' if theta_deg < 0 else 'UP')}.
   - Because X is {('Positive (Inductive/Coil)' if X > 0 else 'Negative (Capacitive/Capacitor)')}, Current {('Lags' if X > 0 else 'Leads')} Voltage.
   - "j" in math literally means "90 degree rotation".

2. Look at the Waveforms (Top Right).
   - Notice the Red wave (Current) peaks {('AFTER' if X > 0 else 'BEFORE')} the Blue wave (Voltage).
   - This time delay IS the angle shown in the Vector Diagram.
   - Complex numbers are just a tool to calculate this time delay without drawing waves every time.
"""
ax3.text(0.05, 0.9, text_content, fontsize=12, family='monospace', verticalalignment='top')

plt.tight_layout()
plt.show()