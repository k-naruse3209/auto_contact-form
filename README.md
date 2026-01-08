# Auto Contact Form

企業名CSVから、公式URL特定→事業分析→協業依頼文作成→問い合わせフォーム自動入力まで一気通貫で行う自動化ツール。

## セットアップ

### 1. Python環境の準備

```bash
# 仮想環境の作成
python3 -m venv venv

# 仮想環境の有効化
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 依存パッケージのインストール
uv sync
# または
pip install -r requirements.txt

# Playwright ブラウザのインストール
playwright install
```

### 2. 環境変数の設定

`.env.example`をコピーして`.env`を作成し、APIキーを設定：

```bash
cp .env.example .env
```

`.env`を編集して、実際のAPIキーを入力：

```
GOOGLE_CSE_API_KEY="your_actual_api_key_here"
GOOGLE_CSE_CX="your_actual_cx_here"
GEMINI_API_KEY="your_actual_gemini_api_key_here"
GEMINI_MODEL="gemini-3-flash-preview"
```

### 3. ディレクトリ構成

```
auto_contact-form/
├── data/
│   ├── company_names.csv    # 入力CSVファイル
│   └── out/                 # 出力ディレクトリ
├── docs/                    # ドキュメント
│   ├── spec.md
│   ├── acceptance.md
│   ├── security.md
│   └── decisions.md
├── prompts/                 # プロンプトテンプレート
│   └── outreach.md
├── src/                     # ソースコード
│   └── main.py
├── .env                     # 環境変数（gitignore）
├── .env.example            # 環境変数テンプレート
├── AGENTS.md               # Codex用作業ルール
├── CLAUDE.md               # Claude Code用メモリ
└── requirements.txt        # 依存パッケージ
```

## 使い方

```bash
# Dry run（送信は行わない）
python -m src.main --dry-run
```

## ダッシュボードでの入力支援（送信は手動）

`docs/phase4_dashboard.html` をブラウザで開くと、各社フォームの入力計画が確認できます。

### 1) Open+Prep + ブックマークレット（コンソール不要）

1. ダッシュボードの `DXAI Fill` をブックマークバーへドラッグ  
2. `Open+Prep` を押してフォームを開く  
3. フォームタブでブックマークの `DXAI Fill` をクリック  

### 2) Open+Prep + Tampermonkey（フォーム側のクリック不要）

1. Chrome拡張で Tampermonkey を追加  
2. `chrome://extensions/` で「デベロッパーモード」を ON  
3. ダッシュボードの「Copy Tampermonkey Script」を押す  
4. Tampermonkeyで新規スクリプトを作成し、内容を貼り付けて保存  
5. `Open+Prep` を押すと自動で入力される  

## ドキュメント

- [MVP仕様](docs/spec.md)
- [完成条件](docs/acceptance.md)
- [セキュリティガイドライン](docs/security.md)
- [依頼文テンプレート](prompts/outreach.md)
