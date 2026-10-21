# MRL_3D_AI_Reconstruction｜公式檢查與 Claude 建構交付 v1

## 0. 工程定錨

- 主線：MRL母體工程架構中心
- 本次分支：MRL_Branch_3D_AI_Reconstruction_Formula_Check_v1
- 分支目標：回到 3D 立體成像主任務，整理完整公式、確認目前工程缺口，交付 Claude 可建構規格。
- 分支交付物：本文件
- 分支完成條件：Claude 可依本文件補齊工程，不再只依零散對話建構。
- 回主線條件：真實資料跑通後，回填 `MRL_工程日誌.md`、`MRL_世界模組工程書_v1.md`。

---

## 1. 主任務定義

主任務不是把材料變成粒子本身，而是：

> 建立一套 3D 立體成像 / AI 重建分析系統，能把照片、影片、COLMAP、Mesh/OBJ/PLY 等輸入統一轉成可比對的分析結構，並透過 AI 注意力、上下文關聯與誤差/覆蓋公式找出缺口，輸出補拍 / 補掃 / 補算建議。

核心管線：

```text
input adapter
→ camera / point / mesh / image standard scene
→ projection / reprojection / coverage computation
→ AI attention weighting
→ heatmap aggregation
→ context graph
→ gap / NBV suggestion
→ report / visualization
→ next loop
```

---

## 2. 標準輸入結構

不管來源是照片、影片、COLMAP、OBJ、PLY，先統一成：

```python
cams: dict[str, Camera]
points: dict[int, (X,Y,Z)]
tracks: dict[str, [(u, v, point_id, value)]]
imgs: dict[str, image_array]
mesh: optional Mesh(vertices, faces, normals, textures)
```

其中：

- `value = reprojection error`：COLMAP / SfM 路徑。
- `value = coverage weight`：Mesh / OBJ / PLY 覆蓋路徑。
- `imgs` 可是真照片，也可以是影片切幀。

---

## 3. 公式總表

### A. 相機 / 投影 / SfM 公式

#### A1. 世界座標到相機座標

```math
X_c = R_i X_w + t_i = [x_c, y_c, z_c]^T
```

#### A2. 針孔投影

```math
x = \frac{x_c}{z_c}, \quad y = \frac{y_c}{z_c}
```

```math
u = f_x x + c_x, \quad v = f_y y + c_y
```

等價矩陣式：

```math
s \begin{bmatrix} u \\ v \\ 1 \end{bmatrix}
= K [R|t] \begin{bmatrix} X \\ Y \\ Z \\ 1 \end{bmatrix}
```

#### A3. COLMAP 四元數轉旋轉矩陣

若 `q=(qw,qx,qy,qz)` 已單位化：

```math
R =
\begin{bmatrix}
1-2(q_y^2+q_z^2) & 2(q_xq_y-q_zq_w) & 2(q_xq_z+q_yq_w) \\
2(q_xq_y+q_zq_w) & 1-2(q_x^2+q_z^2) & 2(q_yq_z-q_xq_w) \\
2(q_xq_z-q_yq_w) & 2(q_yq_z+q_xq_w) & 1-2(q_x^2+q_y^2)
\end{bmatrix}
```

若未單位化，先正規化，或把所有 `2(...)` 改為 `(2/||q||^2)(...)`。

#### A4. SIMPLE_RADIAL 畸變

```math
r^2 = x^2 + y^2
```

```math
x' = x(1+k_1 r^2), \quad y' = y(1+k_1 r^2)
```

```math
u = f_x x' + c_x, \quad v = f_y y' + c_y
```

#### A5. RADIAL 畸變

```math
radial = 1+k_1r^2+k_2r^4
```

```math
x' = x \cdot radial, \quad y' = y \cdot radial
```

#### A6. OPENCV 畸變

```math
radial = 1+k_1r^2+k_2r^4+k_3r^6
```

```math
x' = x \cdot radial + 2p_1xy + p_2(r^2+2x^2)
```

```math
y' = y \cdot radial + p_1(r^2+2y^2) + 2p_2xy
```

#### A7. Epipolar constraint

```math
x_2^T F x_1 = 0
```

```math
E = K_2^T F K_1 = [t]_\times R
```

#### A8. Sampson epipolar residual

```math
r_S = \frac{(x_2^T F x_1)^2}
{(Fx_1)_1^2 + (Fx_1)_2^2 + (F^Tx_2)_1^2 + (F^Tx_2)_2^2}
```

用途：RANSAC / 特徵匹配剔除錯配。

#### A9. 三角測量

```math
X^* = \arg\min_X \sum_i \| x_i - \pi(P_i X) \|_2^2
```

#### A10. Bundle Adjustment

```math
\min_{\{R_i,t_i,K_i\},\{X_j\}}
\sum_{i,j} \rho\left(\left\|x_{ij}-\pi(K_i,R_i,t_i,X_j)\right\|_2^2\right)
```

---

### B. 誤差 / Robust / Heatmap 公式

#### B1. 重投影誤差

```math
\hat{x}_{ij}=\pi(K_i[R_i|t_i]X_j)
```

```math
e_{ij}=\|x_{ij}-\hat{x}_{ij}\|_2
```

#### B2. Huber 魯棒損失

```math
\rho_\delta(e)=
\begin{cases}
\frac{1}{2}e^2, & |e|\le\delta \\
\delta(|e|-\frac{1}{2}\delta), & |e|>\delta
\end{cases}
```

#### B3. AI 注意力加權誤差

```math
\bar e_{ij}=w_{ij}\cdot\rho_\delta(e_{ij})
```

`w_ij` 來自 simple / ViT / DINO / segmentation attention。

#### B4. 影像域 Heatmap

```math
H_i(u,v)=Agg_{j:\hat{x}_{ij}\approx(u,v)}(\bar e_{ij})
```

可用：max / mean / p90 / weighted mean。

#### B5. Tile 分數

```math
S(T)=\frac{1}{|T|}\sum_{(u,v)\in T}H(u,v)
```

- error mode：選 `S(T)` 最大的 tile。
- coverage mode：選 `S(T)` 最小的 tile。

#### B6. 停止條件

```math
p90(e) < \tau_e \quad \land \quad coverage > \tau_c \quad \land \quad gap\_count = 0
```

---

### C. 注意力機制公式

#### C1. Transformer self-attention

```math
Attention(Q,K,V)=softmax\left(\frac{QK^T}{\sqrt{d_k}}+M\right)V
```

#### C2. Multi-head attention

```math
head_h = Attention(QW_h^Q, KW_h^K, VW_h^V)
```

```math
MHA(Q,K,V)=Concat(head_1,...,head_H)W^O
```

#### C3. 注意力融合權重

```math
w(u,v)=softmax(\gamma_a A(u,v)+\gamma_g G(u,v)+\gamma_s S(u,v)+\gamma_m M(u,v))
```

其中：

- `A`：ViT/DINO attention。
- `G`：邊緣/梯度強度。
- `S`：語義穩定度或物體遮罩。
- `M`：motion blur / 反光 / 低紋理懲罰遮罩。

#### C4. 不可靠區域抑制

```math
w'(u,v)=w(u,v)\cdot (1-r_{blur})(1-r_{reflect})(1-r_{dynamic})
```

---

### D. MVS / 深度 / 表面公式

#### D1. 視差深度

```math
Z = \frac{fB}{d}
```

#### D2. 多視角光度一致性

```math
E_{photo}(D)=\sum_{i,j}\sum_u
\left\| I_i(u)-I_j\left(\pi_j(T_{ji}\Pi_i^{-1}(u,D_i(u)))\right)\right\|_1
```

#### D3. 深度平滑項

```math
E_{smooth}(D)=\sum_u \|\nabla D(u)\|_1
```

#### D4. 總 MVS 能量

```math
E(D)=E_{photo}(D)+\lambda_s E_{smooth}(D)+\lambda_n E_{normal}(D)
```

---

### E. Mesh / OBJ / PLY 覆蓋與幾何缺陷公式

#### E1. 點密度 / 覆蓋場

```math
c(x)=\sum_j \exp\left(-\frac{\|x-X_j\|^2}{2h^2}\right)
```

```math
gap(x)=\frac{1}{c(x)+\epsilon}
```

#### E2. 相機可見次數

```math
n_j=\sum_i \mathbf{1}[X_j \text{ visible from camera } i]
```

```math
coverage_j=\frac{n_j}{N_{cams}}
```

#### E3. 法線方向覆蓋

```math
q_j = \max_i \max(0, n_j^T v_{ij})
```

其中 `n_j` 是表面法線，`v_ij` 是點到相機方向。

#### E4. Poisson Surface Reconstruction

```math
\nabla^2 \chi = \nabla \cdot V
```

#### E5. SDF 表面

```math
S(x)=0
```

```math
n(x)=\frac{\nabla S(x)}{\|\nabla S(x)\|}
```

#### E6. Chamfer Distance

```math
CD(P,Q)=\frac{1}{|P|}\sum_{p\in P}\min_{q\in Q}\|p-q\|_2^2
+\frac{1}{|Q|}\sum_{q\in Q}\min_{p\in P}\|q-p\|_2^2
```

#### E7. Hausdorff Distance

```math
HD(P,Q)=\max\left(
\max_{p\in P}\min_{q\in Q}\|p-q\|,
\max_{q\in Q}\min_{p\in P}\|q-p\|
\right)
```

#### E8. F-score

```math
Precision(\tau)=\frac{|\{p\in P:d(p,Q)<\tau\}|}{|P|}
```

```math
Recall(\tau)=\frac{|\{q\in Q:d(q,P)<\tau\}|}{|Q|}
```

```math
F(\tau)=\frac{2PR}{P+R}
```

---

### F. NeRF / Gaussian Splatting 補洞公式

#### F1. NeRF 體渲染

```math
C(r)=\int_{t_n}^{t_f}T(t)\sigma(r(t))c(r(t),d)dt
```

```math
T(t)=\exp\left(-\int_{t_n}^{t}\sigma(r(s))ds\right)
```

#### F2. Fourier feature / positional encoding

```math
\gamma(x)=\left[\sin(2^0\pi x),\cos(2^0\pi x),...,\sin(2^{L-1}\pi x),\cos(2^{L-1}\pi x)\right]
```

#### F3. 3D Gaussian

```math
G_i(x)=\alpha_i\exp\left(-\frac{1}{2}(x-\mu_i)^T\Sigma_i^{-1}(x-\mu_i)\right)
```

#### F4. 3D Gaussian 投影到 2D

```math
\Sigma' = J W \Sigma W^T J^T
```

其中 `W` 是 view transform，`J` 是投影 Jacobian。

#### F5. Alpha compositing

```math
C=\sum_i T_i \alpha_i c_i
```

```math
T_i=\prod_{j<i}(1-\alpha_j)
```

---

### G. Context Graph / 補拍建議 / NBV 公式

#### G1. 熱圖相關性

```math
corr(H_a,H_b)=\frac{cov(H_a,H_b)}{\sigma(H_a)\sigma(H_b)}
```

若 `corr < threshold`，表示兩個視角的缺口分布互補。

#### G2. 視角基線夾角

```math
\theta_{ab}=\arccos\left(\frac{(C_a-X)^T(C_b-X)}{\|C_a-X\|\|C_b-X\|}\right)
```

#### G3. 視角補充收益

```math
G_{ab}=\alpha(1-corr(H_a,H_b))+\beta \cdot baseline\_gain(\theta_{ab})-\gamma\cdot cost(a,b)
```

#### G4. Next Best View 目標

```math
C^* = \arg\max_C
\left[
\lambda_1 Gain_{coverage}(C)+
\lambda_2 Gain_{error}(C)+
\lambda_3 Gain_{normal}(C)-
\lambda_4 Cost(C)
\right]
```

#### G5. 由 heatmap tile 反推空間射線

```math
r = R_i^T K_i^{-1}\begin{bmatrix}u\\v\\1\end{bmatrix}
```

相機中心：

```math
C_i = -R_i^T t_i
```

新候選視角可沿熱點射線、表面法線或物體中心環繞生成。

---

### H. 影片輸入公式

#### H1. 抽幀間隔

```math
step = round\left(\frac{fps_{src}}{fps_{target}}\right)
```

#### H2. 影格清晰度

```math
sharpness(I)=Var(\nabla^2 I)
```

#### H3. 影格選擇分數

```math
Q(I_t)=\alpha sharpness(I_t)+\beta overlap(I_t,I_{t-1})-\gamma blur(I_t)
```

---

### I. MRL 放大 / 反推 / 閉環公式

#### I1. 放大律

```math
P_{k+1}=N_k\cdot P_k\cdot\eta_k
```

#### I2. 反推律

```math
P_k=\frac{P_{k+1}}{N_k\eta_k+\epsilon}
```

#### I3. 系統缺口分數

```math
\Delta^*=\lambda_1\Delta_{geom}+\lambda_2\Delta_{sem}+\lambda_3\Delta_{rev}
```

套到 3D 任務：

```math
\Delta_{geom}=norm(CD,HD,Fscore,error\_p90)
```

```math
\Delta_{sem}=attention\_uncertainty + unstable\_mask
```

```math
\Delta_{rev}=export\_diff + reprojection\_loop\_diff
```

---

## 4. 目前工程已完成狀態

目前 `MRL_3D_AI_Reconstruction_System_v1_REAL` 已可做到：

- 可安裝 Python package。
- CLI 執行。
- adapter：simulate / colmap / mesh_obj / video frames。
- simple attention 可跑。
- vit attention 為選配。
- 輸出 metrics / suggestions / links / heatmap png/npy。
- 本環境已實測 demo_simulate 與 mesh_obj 可執行。

---

## 5. 目前缺口

### 5.1 真實重建缺口

目前 pipeline 可讀 COLMAP 結果，但不內建 COLMAP/OpenMVS 二進位工具。

Claude 需補：

```text
scripts/MRL_Run_COLMAP_From_Frames.sh
scripts/MRL_Run_OpenMVS_From_COLMAP.sh
```

以及 Python runner：

```text
mrl3d/workers/colmap_runner.py
mrl3d/workers/openmvs_runner.py
```

### 5.2 影片真 SfM 缺口

目前 video adapter 只切幀，不會自動產生相機姿態與點雲。

Claude 需補：

```text
video → frames → COLMAP DB → sparse model → text model → pipeline
```

### 5.3 Mesh 幾何域缺口

目前 OBJ adapter 只用頂點 coverage，不含：

- faces
- normals
- ray visibility
- occlusion
- surface area weighted coverage

Claude 需補：

```text
PLY/OBJ mesh reader
face normals
ray-triangle visibility
surface heatmap
```

### 5.4 真 NBV 缺口

目前 suggestions 只給 tile，不給完整相機外參。

Claude 需補：

```math
C^*=argmax_C[coverage + error + normal - cost]
```

輸出：

```json
{
  "recommended_camera_pose": {
    "position": [x,y,z],
    "look_at": [x,y,z],
    "reason": "low coverage / high reprojection error"
  }
}
```

### 5.5 AI 注意力缺口

目前 simple attention 可跑，ViT 選配但不是產品級。

Claude 需補：

- DINOv2 / SAM / segmentation mask。
- motion blur detector。
- reflection / transparent surface mask。
- low-texture penalty。

### 5.6 3D Viewer / 主流檢視器輸出缺口

`.lnk` 只能當 Windows 3D Viewer 捷徑，不是模型資料。

Claude 需補輸出：

```text
exports/model.obj
exports/model.glb
exports/pointcloud.ply
exports/coverage_colored_mesh.obj 或 .ply
```

這樣才能用 3D Viewer / Blender / MeshLab 打開。

---

## 6. Claude 建構指令

### Claude 任務名稱

```text
MRL_Branch_3D_AI_Reconstruction_Completion_v1
```

### 目標

將目前 `MRL_3D_AI_Reconstruction_System_v1_REAL` 從「可跑分析管線」補成「可接真資料、可跑影片重建、可輸出幾何域 heatmap 與 3D Viewer 可讀模型」的工程版本。

### 必須完成

1. 保留現有 package 架構，不重建平行版本。
2. 補 COLMAP runner。
3. 補影片切幀後自動 SfM。
4. 補 OpenMVS runner 或至少 mesh import/export。
5. 補 PLY/OBJ face/normals/visibility coverage。
6. 補幾何域 heatmap。
7. 補 NBV 相機外參建議。
8. 補 GLB/OBJ/PLY 主流輸出。
9. 保留 simple attention，新增 DINOv2/SAM optional backend。
10. 所有輸出需包含 report：已完成 / 待驗證 / 不回填 / 下一步。

### 驗收標準

- `mrl3d run --config config/demo_simulate.yaml` 通過。
- `mrl3d run --config config/mesh_obj.yaml` 通過。
- `mrl3d run --config config/video_colmap.yaml` 能完成 video→frames→COLMAP→report。
- `mrl3d run --config config/colmap.yaml` 能讀真 COLMAP text model。
- `mrl3d run --config config/mesh_surface.yaml` 能輸出 colored mesh / point cloud。
- `data/outputs/*` 至少包含：
  - `metrics.json`
  - `metrics_summary.csv`
  - `suggestions.json`
  - `links.json`
  - `heatmap_*.png`
  - `geometry_heatmap.ply` 或 `coverage_colored_mesh.obj`
  - `MRL_Run_Report.md`

### 禁止

- 不得宣稱「完整 3D 重建已完成」除非 COLMAP/OpenMVS 真資料跑通。
- 不得把 video adapter 的切幀結果說成 SfM 結果。
- 不得把 `.lnk` 當 3D 模型資料。
- 不得刪除既有檔案；只能 additive patch。

---

## 7. 結論

目前不是公式缺少一點，而是工程層還缺「真重建閉環」：

```text
影片/照片
→ 真 SfM
→ 真 MVS/Mesh
→ AI 注意力誤差分析
→ 幾何域 coverage
→ NBV 相機建議
→ 主流 3D 輸出
```

公式層現在已補齊到 Claude 可建構程度。
下一步不是再擴散概念，而是讓 Claude 按本文件做 additive patch。
