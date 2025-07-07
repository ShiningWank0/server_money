# Server Money - Claude AI アシスタント向け開発情報

## プロジェクト概要

Server Moneyは、個人や小規模組織向けの高機能Web家計簿アプリケーションです。FlaskとVue.jsを使用したフルスタック構成で、複数口座の収支管理と可視化機能を提供します。

### 主要機能
- **セキュアな認証システム** - bcryptハッシュ化、セッション管理、ログイン試行制限
- 複数口座（現金・銀行口座・電子マネー等）の管理
- 収入・支出の記録と残高自動計算
- 検索・フィルタリング機能
- データ可視化（残高推移グラフ、収支比率分析）
- CSVバックアップ・エクスポート機能
- 詳細なログ管理システム

## 技術スタック

### バックエンド
- **Python 3.12+**
- **Flask 3.1+** - Webフレームワーク
- **SQLAlchemy 2.0+** - ORM
- **SQLite** - データベース
- **Waitress** - WSGIサーバー
- **bcrypt** - パスワードハッシュ化
- **python-dotenv** - 環境変数管理
- **uv** - パッケージマネージャー

### フロントエンド
- **Vue.js 3.0** - JavaScriptフレームワーク
- **Chart.js** - データ可視化
- **CSS3** - グラスモーフィズムデザイン
- **Material Icons** - アイコン

## プロジェクト構造

```
server_money/
├── app.py                 # メインアプリケーション（簡素化済み）
├── auth_setup.py          # 初回認証セットアップスクリプト
├── models.py              # データベースモデル（SQLAlchemy）
├── auth.py                # 認証システム（bcryptハッシュ化、セッション管理）
├── config.py              # 設定管理（ログシステム、環境設定）
├── utils.py               # ユーティリティ関数（バックアップ、バリデーション）
├── routes/                # ルートパッケージ
│   ├── __init__.py        # パッケージ初期化
│   ├── auth_routes.py     # 認証関連ルート
│   ├── api_routes.py      # APIエンドポイント
│   └── main_routes.py     # メイン画面ルート
├── pyproject.toml         # プロジェクト設定・依存関係
├── .env.example           # 環境変数設定例
├── .gitignore            # Git除外設定（.env含む）
├── README.md             # 詳細ドキュメント
├── LICENSE               # MITライセンス
├── templates/
│   ├── index.html        # メインHTMLテンプレート
│   └── login.html        # ログイン画面
├── static/
│   ├── css/
│   │   └── style.css     # グラスモーフィズムスタイル
│   └── js/
│       └── main.js       # Vue.jsアプリケーション
├── instance/
│   └── money_tracker.db  # SQLiteデータベース
├── logs/
│   └── money_tracker.log # アプリケーションログ
└── backups/              # CSVバックアップ
```

## 主要なデータベース

### Transactionテーブル
- `id`: 主キー
- `account`: 口座名（資金項目）
- `date`: 取引日時
- `item`: 取引項目名
- `type`: 取引種別（'income' or 'expense'）
- `amount`: 金額
- `balance`: 残高（自動計算）

## API エンドポイント

### 認証
- `GET /login` - ログイン画面
- `POST /api/login` - ログイン認証
- `POST /api/logout` - ログアウト
- `GET /api/auth_status` - 認証状態確認

### 取引管理（要認証）
- `GET /api/transactions` - 取引履歴取得（検索・フィルタ対応）
- `POST /api/transactions` - 新規取引追加
- `PUT /api/transactions/<id>` - 取引編集
- `DELETE /api/transactions/<id>` - 取引削除

### データ参照（要認証）
- `GET /api/accounts` - 口座一覧取得
- `GET /api/items` - 項目一覧取得
- `GET /api/balance_history` - 残高推移データ取得

### ユーティリティ（要認証）
- `GET /api/backup_csv` - CSVバックアップダウンロード
- `GET /api/download_log` - ログファイルダウンロード

## 重要な設定

### 環境変数
- `LOGIN_USERNAME`: ログインID
- `LOGIN_PASSWORD_HASH`: bcryptハッシュ化されたパスワード
- `SECRET_KEY`: Flaskセッション暗号化キー
- `ENVIRONMENT`: 実行環境（development/production）
- `LOG_LEVEL`: ログレベル（DEBUG/INFO/WARNING/ERROR/CRITICAL）

### セットアップ・開発コマンド
```bash
# 初回認証設定（初回のみ）
uv run auth_setup.py

# 開発環境での実行
ENVIRONMENT=development uv run app.py

# 本番環境での実行
ENVIRONMENT=production uv run app.py

# 依存関係の同期
uv sync
```

## 重要なファイル構成（モジュール化済み）

### app.py - メインアプリケーション
- **アプリケーションファクトリ** - create_app()関数でアプリ構成
- **Blueprint登録** - 機能別ルートの統合管理
- **起動シーケンス** - 初期化からサーバー起動までの制御

### models.py - データベースモデル
- **Transactionモデル** - SQLAlchemy ORMでのデータ構造定義
- **to_dict()メソッド** - JSONシリアライゼーション
- **データベースインスタンス** - dbオブジェクトの統一管理

### auth.py - 認証システム
- **パスワード検証** - bcryptハッシュ化と照合処理
- **ログイン試行制限** - IPアドレス別ロック機能
- **@login_requiredデコレータ** - エンドポイント保護
- **認証設定チェック** - .envファイルの存在検証

### config.py - 設定管理
- **Configクラス** - アプリケーション設定の一元管理
- **ログシステム設定** - 環境別ログ出力制御
- **ローテーション設定** - 10MBファイルサイズ、5ファイル保持

### utils.py - ユーティリティ関数
- **バックアップ管理** - 古いCSVファイルの自動削除
- **データベース初期化** - テーブル存在確認と作成
- **バリデーション** - 取引データの入力検証
- **日付解析** - 日付・時刻文字列のdatetime変換

### routes/ - ルートパッケージ
- **auth_routes.py** - ログイン、ログアウト、認証状態確認
- **api_routes.py** - 取引CRUD、データ分析、バックアップAPI
- **main_routes.py** - メイン画面表示

### auth_setup.py - 初回認証セットアップ
- **自動セットアップ** - ユーザー入力から.envファイル生成まで
- **パスワードハッシュ化** - bcryptでソルト付きハッシュ化
- **セキュアキー生成** - ランダムSECRET_KEYの作成
- **パスワード強度チェック** - 8文字以上の制限

### main.js の主要コンポーネント
- Vue.js リアクティブデータ管理
- API通信とデータ処理
- **ログアウト機能** - セキュアなセッション終了
- グラフ表示（Chart.js統合）
- 検索・フィルタリング機能
- モーダル管理

### login.html の特徴
- グラスモーフィズムデザイン
- リアルタイムバリデーション
- ログイン試行回数表示
- アニメーション効果

### style.css の特徴
- グラスモーフィズムデザイン
- レスポンシブレイアウト
- モバイルファーストアプローチ
- Material Design準拠

## 開発時の注意事項

### コード規約
- Python: PEP 8準拠
- JavaScript: ES6+標準
- 日本語コメントとログメッセージ
- 詳細なエラーハンドリング

### テスト・デバッグ
- 開発環境では詳細ログ出力
- ブラウザ開発者ツールでフロントエンド確認
- SQLiteデータベースの直接確認可能

### セキュリティ対策
- **bcryptパスワードハッシュ化** - ソルト付きハッシュ
- **セッション管理** - 2時間タイムアウト、セキュアクッキー
- **ログイン試行制限** - 5回失敗で30分ロック
- **環境変数保護** - .envファイルをGit管理から除外
- **認証必須化** - 全API エンドポイントに@login_required
- 入力値検証
- SQLインジェクション対策（SQLAlchemy ORM使用）
- 本番環境でのログ制限

## よくある開発タスク

### 新機能追加
1. バックエンドAPI実装（app.py）
2. データベースモデル変更（必要に応じて）
3. フロントエンドUI実装（main.js, index.html）
4. スタイル調整（style.css）

### バグ修正
1. ログファイル確認（logs/money_tracker.log）
2. ブラウザ開発者ツール確認
3. データベース直接確認
4. 段階的デバッグ

### パフォーマンス最適化
- SQLクエリの最適化
- フロントエンドの仮想化
- 大量データ対応のページネーション
- 画像・CSS最適化

## 運用情報

### ログ管理
- ファイルローテーション: 10MB, 5ファイル保持
- 環境別ログ出力制御
- 詳細なAPI呼び出し追跡

### バックアップ
- CSVエクスポート機能
- 自動古ファイル削除（最新3件保持）
- SQLiteデータベースバックアップ

### 監視ポイント
- ディスク使用量（ログ・データベース）
- メモリ使用量
- API応答時間
- エラー発生率

## ライセンス

MIT License - 商用利用可能