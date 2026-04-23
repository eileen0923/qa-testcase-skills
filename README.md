# qa-testcase-generator

KKday Ticket Squad QA 專用的 Claude Code skill，輸入 PRD 自動產出 XMind 格式的測試案例。

## 功能

- 讀取 PRD（PDF 檔案或貼上文字）
- 依照 KKday Ticket Squad 的 QA 規範自動分析功能模組、產出 Test Cases
- 輸出 `.xmind` 檔案至桌面，可直接用 XMind 開啟

## 安裝

**前置需求：** [Claude Code](https://claude.ai/code) CLI

```bash
# 進入 Claude Code skills 目錄
cd ~/.claude/skills

# Clone 此 repo
git clone <repo-url> qa-testcase-generator
```

完成後目錄結構如下：

```
~/.claude/skills/
└── qa-testcase-generator/
    ├── SKILL.md
    ├── README.md
    ├── generate-xmind.py
    ├── qa-design-methods.md
    ├── feature-backgrounds/
    │   └── payment-rules.md
    └── project-backgrounds/
        └── README.md
```

### 各檔案的角色

| 檔案 | 內容 |
|---|---|
| `SKILL.md` | Skill 主體：Claude Code 讀取的執行指令，包含 KKday 通用業務知識（訂單狀態機、平台差異、BE2 等）、QA 格式規範（Priority、TC 撰寫規則）、Compact TC 格式規格 |
| `qa-design-methods.md` | 測試方法論參考文件：等價劃分、邊界值分析、狀態轉換、決策表、錯誤猜測法，各附 KKday 情境範例 |
| `generate-xmind.py` | TC 格式轉換腳本：將 Claude 輸出的 compact 文字格式（`.txt`）解析並轉換為 `.xmind` 檔案，支援嵌入 Figma 截圖；也接受既有 `.xml` 直接打包（向下相容） |
| `README.md` | 本檔案：安裝說明、使用方式、各檔案角色說明 |
| `feature-backgrounds/` | 功能域層級的通用業務知識（如：金流 / repay 頁行為），由 skill 維護者管理；偵測到 PRD 含對應關鍵字時自動載入，無需使用者手動操作 |
| `project-backgrounds/` | 專案特定的既有業務知識（如：改期規則、訂單明細頁現有 UI），由使用者自行新增，每次遇到相同功能的 PRD 時自動載入；詳見目錄內的 `README.md` |

> **其他 Squad 也能用**：`SKILL.md` 與 `qa-design-methods.md` 的規則適用於 KKday 任何產品線。只需將角色描述第一行的 Squad 名稱改掉，並在 `project-backgrounds/` 放入自己 squad 的功能背景知識即可。

## 使用方式

在 Claude Code 對話中輸入指令，後面附上 prd (pdf 檔案) 的路徑：

```
/qa-testcase-generator /path/to/prd.pdf
```

> **Tip**：不用手動輸入路徑——直接把 PDF 檔案拖曳到 Claude Code 對話框，路徑會自動帶入。

呼叫時可在路徑後附上補充說明，優先層級最高，整個執行過程都會套用：

```
/qa-testcase-generator /path/to/prd.pdf 這次只測 Phase 1，忽略付款流程
```

或直接輸入指令，再貼上 PRD 文字內容：

```
/qa-testcase-generator
```

產出的 `.xmind` 檔案會自動存到 `~/Desktop/`。

## 專案背景知識（選用）

`project-backgrounds/` 目錄可放特定功能的既有業務知識，讓 Claude 不需要每次重新理解。詳見目錄內的 `README.md`。

## 更新到最新的 skills 版本

```bash
cd ~/.claude/skills/qa-testcase-generator
git pull
```
