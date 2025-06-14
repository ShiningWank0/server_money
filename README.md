# Server Money - 高機能家計簿・資金管理アプリケーション

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.1+-green.svg)](https://flask.palletsprojects.com/)
[![Vue.js](https://img.shields.io/badge/Vue.js-3.0+-brightgreen.svg)](https://vuejs.org/)
[![SQLite](https://img.shields.io/badge/SQLite-Database-orange.svg)](https://sqlite.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Server Moneyは、個人や小規模組織の収支管理を効率的に行うWebベースの家計簿システムです。直感的なユーザーインターフェースと豊富な分析機能を持ち、金銭の流れを可視化してより良い財務管理をサポートします。

## 📋 目次

- [特徴](#-特徴)
- [デモ・スクリーンショット](#-デモスクリーンショット)
- [技術スタック](#-技術スタック)
- [プロジェクト構造](#-プロジェクト構造)
- [機能詳細](#-機能詳細)
- [API仕様](#-api仕様)
- [UIデザイン哲学](#-uiデザイン哲学)
- [インストール・実行方法](#-インストール実行方法)
- [設定・環境変数](#-設定環境変数)
- [開発ガイド](#-開発ガイド)
- [トラブルシューティング](#-トラブルシューティング)
- [ライセンス](#-ライセンス)

## 🚀 特徴

### 💰 包括的な収支管理
- **複数口座対応**: 現金、銀行口座、電子マネーなど複数の資金項目を個別に管理
- **詳細な取引記録**: 日付、時刻、項目、金額、残高を自動計算・記録
- **リアルタイム残高更新**: 取引追加・編集・削除時に残高を自動再計算

### 📊 高度な分析・可視化機能
- **残高推移グラフ**: 時系列での資金の流れを直感的に把握
- **収支比率グラフ**: 収入と支出の割合をピエチャートで表示
- **項目別分析**: 収入・支出を項目別に分類して詳細分析
- **期間・単位指定**: 日別・月別・年別での表示切り替え

### 🔍 強力な検索・フィルタリング
- **リアルタイム検索**: 項目名、口座名、金額での即座検索
- **口座別フィルタ**: 特定の資金項目のみを表示
- **日付ソート**: 昇順・降順での日付並び替え

### 💾 データ管理・バックアップ
- **CSVエクスポート**: 全取引データをCSVファイルでバックアップ
- **自動ログ記録**: 詳細なアプリケーションログを自動保存
- **データ整合性**: SQLiteデータベースによる安全なデータ保存

### 📱 レスポンシブデザイン
- **モバイル対応**: スマートフォン・タブレットでの最適化表示
- **直感的UI**: モダンなグラスモーフィズムデザイン
- **アクセシビリティ**: 使いやすさを重視したインターフェース

## 🖼️ デモ・スクリーンショット

### メイン画面
- 美しいグラデーション背景とフローティングカードデザイン
- リアルタイム残高表示とスティッキーヘッダー
- 直感的な取引履歴テーブル

### 分析ダッシュボード
- インタラクティブなグラフとチャート
- 複数の表示形式（日別・月別・年別）
- 口座別・項目別の詳細分析

## 🛠️ 技術スタック

### バックエンド
- **Python 3.12+**: メインプログラミング言語
- **Flask 3.1+**: 軽量Webフレームワーク
- **SQLAlchemy 2.0+**: ORM（オブジェクトリレーショナルマッピング）
- **SQLite**: 軽量埋め込みデータベース
- **Waitress**: WSGIサーバー（本番・開発環境共通）

### フロントエンド
- **Vue.js 3.0**: プログレッシブJavaScriptフレームワーク
- **Chart.js**: データ可視化ライブラリ
- **CSS3**: グラスモーフィズムデザイン
- **Material Icons**: Google Material Designアイコン

### 開発・運用ツール
- **uv**: 高速Pythonパッケージマネージャー・環境管理
- **RotatingFileHandler**: ログローテーション機能
- **環境変数サポート**: 開発・本番環境の設定分離

## 📁 プロジェクト構造

```
server_money/
├── 📄 app.py                      # メインFlaskアプリケーション
├── 📄 pyproject.toml               # プロジェクト設定・依存関係
├── 📄 uv.lock                      # 依存関係ロックファイル
├── 📄 README.md                    # プロジェクト説明書（本ファイル）
├── 📁 templates/                   # HTMLテンプレート
│   └── 📄 index.html               # メインHTML構造
├── 📁 static/                      # 静的ファイル
│   ├── 📁 css/
│   │   └── 📄 style.css            # UIスタイルシート
│   └── 📁 js/
│       └── 📄 main.js              # Vue.jsアプリケーションロジック
├── 📁 instance/                    # インスタンス固有データ
│   └── 📄 money_tracker.db         # SQLiteデータベースファイル
├── 📁 logs/                        # アプリケーションログ
│   ├── 📄 money_tracker.log        # 現在のログファイル
│   └── 📄 money_tracker.log.*      # ローテーション済みログ
├── 📁 backups/                     # CSVバックアップファイル
│   └── 📄 transactions_backup_*.csv
└── 📁 __pycache__/                 # Pythonキャッシュ
```

### 各ディレクトリの役割

#### 🏗️ コアアプリケーション
- **`app.py`**: Flask WebサーバーとAPI エンドポイント、データベースモデル定義
- **`templates/index.html`**: SPA（Single Page Application）のメインHTML構造
- **`static/css/style.css`**: グラスモーフィズムデザインとレスポンシブレイアウト
- **`static/js/main.js`**: Vue.js リアクティブUI、API通信、データ可視化ロジック

#### 💾 データ・ストレージ
- **`instance/money_tracker.db`**: 取引データ、残高情報をSQLiteで管理
- **`logs/`**: アプリケーション動作ログ（エラー、操作履歴、デバッグ情報）
- **`backups/`**: ユーザーがダウンロード可能なCSVバックアップファイル

#### ⚙️ 設定・依存関係
- **`pyproject.toml`**: プロジェクトメタデータ、依存ライブラリ指定
- **`uv.lock`**: 依存関係の詳細バージョン固定（再現可能ビルド）

## 🎯 機能詳細

### 1. 取引管理
**新規取引追加**
- 資金項目（口座）選択
- 日付・時刻指定（時刻は任意）
- 項目名入力（過去履歴から自動補完）
- 収入・支出区分選択
- 金額入力（正の整数のみ）
- 残高自動計算・更新

**取引編集・削除**
- 既存取引のクリック編集
- フィールド単位での部分編集
- 削除時の残高自動再計算
- データ整合性の自動維持

### 2. 残高・口座管理
**複数口座対応**
- 口座別の独立した残高管理
- 口座間での取引移動サポート
- 口座名の動的追加・管理

**残高計算システム**
- 取引時系列に基づく自動計算
- 編集・削除時の影響波及処理
- 検索・フィルタ時の仮想残高表示

### 3. 検索・フィルタリング
**リアルタイム検索**
- 項目名の部分一致検索
- 口座名・金額・日付での検索
- 検索結果での仮想残高表示

**口座別フィルタ**
- 特定口座のみの表示
- 「すべて」での全口座統合表示
- フィルタ状態の視覚的フィードバック

### 4. データ可視化・分析
**残高推移グラフ**
- Chart.jsベースのインタラクティブグラフ
- 日別・月別・年別表示切り替え
- 複数口座の同時表示・比較
- ズーム・パン操作対応

**収支分析**
- 期間別収支比率（ピエチャート）
- 項目別収入・支出分析
- 口座別パフォーマンス比較

### 5. データ管理・バックアップ
**CSVエクスポート**
- 全取引データのCSV出力
- タイムスタンプ付きファイル名
- 古いバックアップの自動削除（最新3件保持）

**ログ管理**
- 詳細なアプリケーション動作ログ
- ファイルローテーション（10MB、5ファイル保持）
- ログレベル別フィルタリング
- ログファイルのダウンロード機能

## 🔌 API仕様

Server MoneyはRESTful APIを提供し、フロントエンドとの効率的な通信を実現しています。

### 口座・項目管理

#### `GET /api/accounts`
**概要**: データベースから資金項目（口座）リストを取得

**レスポンス例**:
```json
["現金", "メインバンク", "電子マネー", "クレジットカード"]
```

#### `GET /api/items`
**概要**: 過去の取引項目名リストを取得（自動補完用）

**レスポンス例**:
```json
["給与", "食費", "交通費", "娯楽費", "書籍", "通信費"]
```

### 取引データ管理

#### `GET /api/transactions`
**概要**: 取引履歴を取得（検索・フィルタ対応）

**クエリパラメータ**:
- `search`: 項目名での部分一致検索
- `account`: 特定口座での絞り込み

**レスポンス例**:
```json
[
  {
    "id": 1, 
    "fundItem": "現金", 
    "date": "2025-06-14 14:30:00", 
    "item": "スーパーマーケット", 
    "type": "expense", 
    "amount": 3500, 
    "balance": 145000
  }
]
```

#### `POST /api/transactions`
**概要**: 新規取引追加

**リクエストボディ**:
```json
{
  "account": "現金",
  "date": "2025-06-14",
  "time": "14:30",  // 任意
  "item": "ランチ代",
  "type": "expense",  // "income" or "expense"
  "amount": 1200
}
```

#### `PUT /api/transactions/<id>`
**概要**: 既存取引の編集

#### `DELETE /api/transactions/<id>`
**概要**: 取引削除（残高自動再計算）

### 分析・レポート

#### `GET /api/balance_history`
**概要**: 残高推移データ取得（グラフ表示用）

**レスポンス例**:
```json
{
  "accounts": ["現金", "銀行口座"],
  "dates": ["2025-06-01", "2025-06-02", "2025-06-03"],
  "balances": {
    "現金": [100000, 98500, 97200],
    "銀行口座": [500000, 500000, 503000]
  }
}
```

### ユーティリティ

#### `GET /api/backup_csv`
**概要**: CSVバックアップファイルダウンロード

#### `GET /api/download_log`
**概要**: アプリケーションログファイルダウンロード

## 🎨 UIデザイン哲学

Server MoneyのUIデザインは、**機能性と美しさの両立**を目指しています。

### デザインコンセプト

**グラスモーフィズム（Glassmorphism）**
- 半透明な白いカードが美しいグラデーション背景に浮かぶデザイン
- `backdrop-filter: blur(10px)` によるぼかし効果
- 柔らかな影（`box-shadow`）による奥行き表現

**カラーパレット**
- **背景**: `linear-gradient(135deg, #667eea 0%, #764ba2 100%)` （紫〜青のグラデーション）
- **カード**: `rgba(255, 255, 255, 0.9)` （半透明白）
- **アクセント**: 収入（薄緑 `#e6ffed`）、支出（薄赤 `#ffe6e6`）

### レスポンシブデザイン原則

**モバイルファースト**
- スマートフォンでの使いやすさを最優先
- タッチインターフェースに最適化されたボタンサイズ
- 片手操作を考慮したレイアウト

**アダプティブレイアウト**
- 画面サイズに応じた要素の再配置
- デスクトップでは横並び、モバイルでは縦積み
- 最適な情報密度の自動調整

### ユーザビリティ設計

**直感的操作**
- 一目で機能が分かるアイコンと配色
- 操作結果の即座フィードバック
- エラー状態の明確な表示

**アクセシビリティ**
- キーボードナビゲーション対応
- 適切なコントラスト比の維持
- スクリーンリーダー対応のARIA属性

## 🚀 インストール・実行方法

Server Moneyは**uv**（高速Pythonパッケージマネージャー）を使用した環境管理を推奨しています。

### 前提条件

- **Python 3.12+** 
- **uv**: [公式インストールガイド](https://docs.astral.sh/uv/getting-started/installation/)

### uvのインストール

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# または、pipを使用
pip install uv
```

### プロジェクトのセットアップ

```bash
# リポジトリのクローン
git clone <repository-url>
cd server_money

# 依存関係の自動インストール（uvが仮想環境も自動作成）
uv sync

# アプリケーションの実行
uv run app.py
```

### 開発環境での実行

```bash
# 開発環境として実行（コンソールログ有効）
ENVIRONMENT=development uv run app.py

# デバッグログレベルで実行
ENVIRONMENT=development LOG_LEVEL=DEBUG uv run app.py

# または環境変数なしでも開発環境として動作（デフォルト）
uv run app.py
```

### 本番環境での実行

```bash
# 本番環境として実行（ファイルログのみ）
ENVIRONMENT=production uv run app.py
```

**アクセス**: ブラウザで `http://localhost:4000`　または `http://[IP_Address]:4000` にアクセス

### Docker実行（オプション）

```dockerfile
# Dockerfile例
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install uv && uv sync
EXPOSE 4000
CMD ["uv", "run", "app.py"]
```

```bash
# Docker build & run
docker build -t server-money .
docker run -p 4000:4000 server-money
```

## ⚙️ 設定・環境変数

### 環境変数

| 変数名 | デフォルト値 | 説明 |
|--------|-------------|------|
| `ENVIRONMENT` | `production` | 実行環境（`development` / `production`） |
| `LOG_LEVEL` | `INFO` | ログレベル（`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`） |

### 環境別設定

#### 開発環境（`ENVIRONMENT=development`）
- **コンソール出力**: 有効（ターミナルにログ表示）
- **ファイル出力**: 有効（`logs/money_tracker.log`）
- **Werkzeugログ**: 詳細表示
- **用途**: ローカル開発、デバッグ

#### 本番環境（`ENVIRONMENT=production`または未設定）
- **コンソール出力**: 無効（セキュリティ向上）
- **ファイル出力**: 有効（`logs/money_tracker.log`）
- **Werkzeugログ**: 警告レベル以上のみ
- **用途**: プロダクション環境、サーバーデプロイ

### ログローテーション設定

- **ファイルサイズ上限**: 10MB
- **保持ファイル数**: 5個
- **ログファイル**: `logs/money_tracker.log`, `logs/money_tracker.log.1`, ...

### データベース設定

- **データベースファイル**: `instance/money_tracker.db`
- **自動テーブル作成**: 初回起動時に自動実行
- **バックアップ**: CSVエクスポート機能で手動バックアップ

## 🔧 開発ガイド

### 開発環境のセットアップ

```bash
# 開発用依存関係の追加（例：テストツール）
uv add --dev pytest pytest-flask

# 新しい依存関係の追加
uv add requests

# 開発モードでの実行
ENVIRONMENT=development LOG_LEVEL=DEBUG uv run app.py
```

### コード構造の理解

#### バックエンド（`app.py`）

**主要コンポーネント**:
1. **ログシステム設定**: 環境別ログ設定、ローテーション
2. **データベースモデル**: SQLAlchemy ORMによるTransactionモデル
3. **API エンドポイント**: REST APIの実装
4. **エラーハンドリング**: 例外処理とログ記録

**重要な関数**:
- `setup_logging()`: ログシステム初期化
- `init_db()`: データベース・テーブル自動作成
- `ensure_table_exists()`: テーブル存在確認・作成

#### フロントエンド（`static/js/main.js`）

**Vue.jsアプリケーション構造**:
1. **リアクティブデータ**: 取引履歴、口座情報、UI状態
2. **computed プロパティ**: フィルタリング、ソート、残高計算
3. **メソッド**: API通信、UI操作、データ可視化
4. **ライフサイクル**: 初期データロード

**重要なcomputed**:
- `filteredTransactions`: 検索・フィルタリング結果
- `transactionsWithRecalculatedBalance`: 残高再計算
- `currentBalance`: 現在残高の算出

### APIエンドポイントの拡張

新しいエンドポイントの追加例:

```python
@app.route("/api/statistics")
def get_statistics():
    """統計情報取得API"""
    try:
        # データ処理ロジック
        stats = calculate_statistics()
        app.logger.info("統計情報を取得しました")
        return jsonify(stats)
    except Exception as e:
        app.logger.error(f"統計情報取得エラー: {str(e)}", exc_info=True)
        return jsonify({'error': '統計情報の取得に失敗しました'}), 500
```

### UIコンポーネントの追加

新しいモーダルの追加例:

```javascript
// main.jsのdataに追加
showNewModal: false,

// メソッドに追加
showNewModal() {
    this.showNewModal = true;
},
hideNewModal() {
    this.showNewModal = false;
}
```

### データベーススキーマの変更

```python
# 新しいカラムの追加例
class Transaction(db.Model):
    # 既存フィールド...
    category = db.Column(db.String(50), nullable=True)  # 新規フィールド
    
    def to_dict(self):
        return {
            # 既存フィールド...
            'category': self.category  # 新規フィールドをJSONに含める
        }
```

### テストの実行

```bash
# テストフレームワークの追加
uv add --dev pytest pytest-flask

# テスト実行
uv run pytest

# カバレッジ付きテスト
uv add --dev pytest-cov
uv run pytest --cov=app
```

## 🐛 トラブルシューティング

### よくある問題と解決方法

#### 1. アプリケーションが起動しない

**症状**: `uv run app.py` でエラーが発生
```bash
ModuleNotFoundError: No module named 'flask'
```

**解決方法**:
```bash
# 依存関係の再インストール
uv sync

# キャッシュのクリア
uv cache clean

# プロジェクトディレクトリの確認
ls -la  # pyproject.tomlの存在確認
```

#### 2. データベースエラー

**症状**: `sqlite3.OperationalError: no such table: transaction`

**解決方法**:
```bash
# データベースファイルの削除（データが失われます）
rm instance/money_tracker.db

# アプリケーション再起動（テーブル自動作成）
uv run app.py
```

**データを保持する場合**:
1. 事前にCSVバックアップを作成
2. データベースファイルを削除
3. アプリケーション起動
4. CSVからデータを手動復元

#### 3. ポート競合エラー

**症状**: `OSError: [Errno 48] Address already in use`

**解決方法**:
```bash
# ポート4000を使用中のプロセスを確認
lsof -i :4000

# プロセスを終了
kill -9 <PID>

# または別のポートを使用（app.py内のポート番号を変更）
```

#### 4. ログファイルの権限エラー

**症状**: ログファイルの作成・書き込みができない

**解決方法**:
```bash
# ログディレクトリの権限確認
ls -la logs/

# 権限の修正
chmod 755 logs/
chmod 644 logs/money_tracker.log
```

#### 5. フロントエンドの表示問題

**症状**: Vue.jsアプリケーションが正しく表示されない

**確認事項**:
1. ブラウザの開発者ツールでJavaScriptエラーを確認
2. `static/js/main.js` のシンタックスエラー
3. Vue.js CDNの読み込み確認
4. ブラウザキャッシュのクリア

### ログの確認方法

#### アプリケーションログ
```bash
# 現在のログファイル
tail -f logs/money_tracker.log

# ログレベル別の確認
grep "ERROR" logs/money_tracker.log
grep "WARNING" logs/money_tracker.log
```

#### ブラウザ側の確認
1. 開発者ツール（F12）を開く
2. Console タブでJavaScriptエラーを確認
3. Network タブでAPI通信状況を確認

### パフォーマンス問題

#### データベースが重い場合
```bash
# データベースサイズの確認
ls -lah instance/money_tracker.db

# 古いデータの削除（手動）
sqlite3 instance/money_tracker.db
> DELETE FROM transaction WHERE date < '2024-01-01';
> VACUUM;
```

#### 大量データでの表示が遅い場合
- ページネーション機能の実装を検討
- データベースインデックスの追加
- フロントエンドでの仮想スクロール実装

## 🚀 デプロイメント

### クラウドプラットフォームでのデプロイ

#### Heroku
```bash
# Procfileの作成
echo "web: uv run app.py" > Procfile

# Heroku CLIでデプロイ
heroku create your-app-name
git push heroku main
```

#### Railway
```toml
# railway.toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "uv run app.py"
```

#### Render
- GitHub連携で自動デプロイ
- Start Command: `uv run app.py`
- Environment: `ENVIRONMENT=production`

### セルフホスティング

#### systemd サービス化（Linux）
```ini
# /etc/systemd/system/server-money.service
[Unit]
Description=Server Money Application
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/server_money
Environment=ENVIRONMENT=production
ExecStart=/usr/local/bin/uv run app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# サービスの有効化
sudo systemctl enable server-money
sudo systemctl start server-money
```

#### Nginx リバースプロキシ
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:4000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📝 今後の開発予定

### 短期目標（v1.1）
- [ ] データ検証強化（入力値サニタイゼーション）
- [ ] ページネーション機能
- [ ] データベースインデックス最適化
- [ ] 単体テストの実装

### 中期目標（v1.5）
- [ ] 予算設定・アラート機能
- [ ] 定期取引の自動記録
- [ ] カテゴリー別分析の強化
- [ ] データベースのPostgreSQL移行オプション

### 長期目標（v2.0）
- [ ] マルチユーザー対応
- [ ] 銀行API連携（自動取引取得）
- [ ] モバイルアプリ版の開発
- [ ] 機械学習による支出予測機能

## 🤝 コントリビューション

### 貢献方法

1. **Fork** このリポジトリ
2. **Feature branch** を作成 (`git checkout -b feature/AmazingFeature`)
3. **Commit** 変更内容 (`git commit -m 'Add some AmazingFeature'`)
4. **Push** ブランチ (`git push origin feature/AmazingFeature`)
5. **Pull Request** を作成

### 開発ガイドライン

#### コードスタイル
- **Python**: PEP 8準拠
- **JavaScript**: ES6+標準
- **CSS**: BEM記法推奨

#### コミットメッセージ
```
feat: 新機能追加
fix: バグ修正
docs: ドキュメント更新
style: コードスタイル修正
refactor: リファクタリング
test: テスト追加・修正
```

#### プルリクエスト
- 明確なタイトルと説明
- 関連するIssueの参照
- テストの実装・実行確認
- ドキュメントの更新

## 📞 サポート・コミュニティ

### 問題報告
- **GitHub Issues**: バグ報告・機能要望
- **詳細な情報**: 環境、エラーメッセージ、再現手順

### よくある質問（FAQ）

**Q: uvを使わず通常のpipで実行できますか？**
A: 可能ですが、uvの使用を強く推奨します。依存関係の管理とパフォーマンスが大幅に向上します。

**Q: データベースをMySQLやPostgreSQLに変更できますか？**
A: SQLAlchemyを使用しているため、設定変更で対応可能です。`app.py`の`SQLALCHEMY_DATABASE_URI`を変更してください。

**Q: 複数ユーザーでの利用は可能ですか？**
A: 現在はシングルユーザー向けです。マルチユーザー対応は将来のバージョンで予定しています。

## 📄 ライセンス

このプロジェクトは[MIT License](https://opensource.org/licenses/MIT)の下で公開されています。

```
MIT License

Copyright (c) 2025 ShingWank0

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 👨‍💻 作者

**ShingWank0**
- 個人の収支管理を効率化するため、実用性とデザイン性を両立したWebアプリケーションを開発
- Python・Flask・Vue.jsの組み合わせによるフルスタック開発に注力
- オープンソースソフトウェアの普及と改善に貢献

---

**Server Money**で、あなたの財務管理をより簡単で楽しいものにしましょう！ 💰✨

*最終更新: 2025年6月14日*