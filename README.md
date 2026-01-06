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
│   └── security.md
├── prompts/                 # プロンプトテンプレート
│   └── outreach.md
├── src/                     # ソースコード (TBD)
├── .env                     # 環境変数（gitignore）
├── .env.example            # 環境変数テンプレート
└── requirements.txt        # 依存パッケージ
```

## 使い方

（実装後に追記予定）

## ドキュメント

- [MVP仕様](docs/spec.md)
- [完成条件](docs/acceptance.md)
- [セキュリティガイドライン](docs/security.md)
- [依頼文テンプレート](prompts/outreach.md)
