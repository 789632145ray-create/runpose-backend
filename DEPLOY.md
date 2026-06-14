# 雲端部署指南（出門也能用）

把後端部署到公開網路後，App 用 **4G / 5G / 任何 Wi‑Fi** 都能登入、上傳節點、做品質辨識，不再需要和 Mac 在同一區域網路。

## 架構

```
iPhone（任何地方）
    │  HTTPS
    ▼
Railway / Render（FastAPI 容器）
    └── MongoDB Atlas
            ├── users（帳號）
            └── pose_sessions（姿勢節點 / 訓練標籤）
```

本機 iPhone 另以 **Realm Database** 存放：
- 姿勢節點 session（取代舊版 SQLite）
- 分析摘要歷史（取代舊版 JSON）

## 第一步：MongoDB Atlas（免費）

1. 到 [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) 註冊
2. 建立 **Free M0** 叢集
3. **Database Access** → 新增使用者（記下帳密）
4. **Network Access** → Add IP Address → **Allow Access from Anywhere**（`0.0.0.0/0`）
5. **Connect** → Drivers → 複製連線字串，例如：
   ```
   mongodb+srv://user:pass@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```

## 第二步：部署到 Railway（建議）

1. 到 [Railway](https://railway.app) 用 GitHub 登入
2. **New Project** → **Deploy from GitHub repo**
3. **選哪個 repo？**
   - Railway **只會列出 GitHub 上已有的 repo**，不會出現本機資料夾名稱 `pose`。
   - 若你已建立 **`runpose-backend`**（或類似名稱的後端 repo）→ **選它**。
   - 若列表裡沒有任何後端 repo → 先把 `backend` 推到 GitHub（見下方「還沒有 repo」）。
4. **Root Directory**（很重要）：
   - 選 **`runpose-backend`**（repo 根目錄就是 `main.py`）→ Root Directory **留空** 或填 `.`
   - 選 **整包 pose 專案**（repo 裡有 `pose/`、`backend/` 兩層）→ Root Directory 填 **`backend`**
5. **Variables** 新增：

   | 變數 | 值 |
   |------|-----|
   | `POSE_SECRET_KEY` | 隨機長字串（`openssl rand -hex 32`） |
   | `POSE_MONGO_URL` | 上一步 Atlas 連線字串 |
   | `POSE_MONGO_DB` | `pose` |
   | `POSE_RELOAD` | `0` |

6. **Networking** → **Generate Domain**，得到網址如：
   `https://pose-production-xxxx.up.railway.app`
8. 等部署完成，瀏覽器開啟該網址應看到 `{"status":"ok",...}`  
   帳號健康檢查：`GET /health/auth` 應回傳 `{"status":"ok","storage":"mongodb_atlas",...}`

### 還沒有 GitHub repo？（本機 pose 尚未上傳）

在 Mac 終端機執行（把 `你的帳號` 換成 GitHub 使用者名）：

```bash
cd /Users/guojiahao/Desktop/pose/backend
git init
git add main.py train.py requirements.txt Dockerfile railway.toml DEPLOY.md README.md .dockerignore .gitignore
git commit -m "Add cloud deploy files"
gh repo create runpose-backend --public --source=. --push
# 若沒有 gh 指令：到 github.com → New repository → 手動 push
```

完成後回到 Railway 按 **Refresh**，就會看到 `runpose-backend`。

### 上傳訓練模型（品質辨識）

在本機訓練好模型後：

```bash
cd backend
source .venv/bin/activate
python train.py   # 產生 pose_quality_model.joblib
```

把 `pose_quality_model.joblib` 放到 Railway 容器的 `/app/`（可重新 deploy 時把檔案 commit 進 repo，或用 Railway CLI / Volume 上傳），然後 **重啟服務**。

## 第三步：設定 iOS App

1. 在 Xcode 開啟 `pose/Info.plist`
2. 把 `PoseServerBaseURL` 改成你的 Railway 網址（**必須 https**）：
   ```xml
   <key>PoseServerBaseURL</key>
   <string>https://pose-production-xxxx.up.railway.app</string>
   ```
3. 用 **Release** 或一般實機安裝重新編譯 App

> **Debug 模擬器**仍連 `http://127.0.0.1:8000` 本機開發，不受 plist 雲端網址影響。

## 第四步：重新註冊帳號

帳號改存 **MongoDB Atlas** 後，若你從舊版 SQLite 部署升級，Railway 上的舊帳號**不會自動搬移**。請在 App 重新 **註冊** 一次。

App 本機若仍有舊版 `pose.sqlite3` / `pose_summaries.json`，首次啟動會自動匯入 Realm 並重新命名備份。

---

## 其他平台

### Render

1. [Render](https://render.com) → New **Web Service** → 連 GitHub repo
2. Root Directory: `backend`，Environment: **Docker**
3. 同上設定環境變數（**不再需要 SQLite Volume**）

### 本機 Docker 測試

```bash
cd backend
docker build -t pose-api .
docker run -p 8000:8000 \
  -e POSE_SECRET_KEY=dev-secret \
  -e POSE_MONGO_URL="mongodb+srv://..." \
  pose-api
```

---

## 常見問題

**Q: 還會問「區域網路」嗎？**  
A: 連 **HTTPS 雲端** 時通常不會。只有 Debug 模擬器連本機 localhost 才可能出現。

**Q: 沒網路能用嗎？**  
A: 已登入過的使用者仍可進 App 做**本機姿勢偵測**與看**本機歷史紀錄**；登入、上傳、AI 辨識需要網路。

**Q: Build 失敗「Failed to build an image」（幾秒就失敗）？**  
A: 幾乎一定是 **Root Directory 設錯**。選 `runpose-backend` repo 時，Root Directory 必須**留空**（不要填 `backend`）。到 Service → **Settings** → **Source** → Root Directory 清空 → 重新 Deploy。

**Q: Settings 裡找不到 Volume？**  
A: 帳號已改存 MongoDB Atlas，**不再需要 Railway Volume**。

**Q: Atlas / Railway 要付費嗎？**  
A: 兩者都有免費方案，個人使用通常足夠。Railway 免費額度用盡後可能需付費或改 Render。

**Q: 資料安全？**  
A: 正式使用請務必設定強 `POSE_SECRET_KEY`，Atlas 不要用 `0.0.0.0/0` 開放給 production 敏感資料（個人專案可接受）。
