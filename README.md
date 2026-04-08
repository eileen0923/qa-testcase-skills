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
    └── project-backgrounds/
        └── README.md
```

### 各檔案的角色

| 檔案 | 內容 |
|---|---|
| `SKILL.md` | Skill 主體：Claude Code 讀取的執行指令，包含 KKday 通用業務知識（訂單狀態機、平台差異、BE2 等）、QA 格式規範（Priority、TC 撰寫規則）、XMind XML 結構範本 |
| `qa-design-methods.md` | 測試方法論參考文件：等價劃分、邊界值分析、狀態轉換、決策表、錯誤猜測法，各附 KKday 情境範例 |
| `generate-xmind.py` | 打包腳本：將 `content.xml` 壓縮為 `.xmind` 檔案，支援嵌入 Figma 截圖 |
| `README.md` | 本檔案：安裝說明、使用方式、各檔案角色說明 |
| `project-backgrounds/` | 功能級別的專屬業務知識（如：改期規則、訂單明細頁現有 UI），由使用者自行新增，每次遇到相同功能的 PRD 時自動載入；詳見目錄內的 `README.md` |

> **其他 Squad 也能用**：`SKILL.md` 與 `qa-design-methods.md` 的規則適用於 KKday 任何產品線。只需將角色描述第一行的 Squad 名稱改掉，並在 `project-backgrounds/` 放入自己 squad 的功能背景知識即可。

## 使用方式

在 Claude Code 對話中輸入：

```
/qa-testcase-generator /path/to/prd.pdf
```

或直接輸入指令，再貼上 PRD 文字：

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
