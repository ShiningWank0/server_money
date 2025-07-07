"""
Server Money - 複数資金項目家計簿管理アプリケーション

このアプリケーションは、個人の収支管理を行うWebベースの家計簿システムです。

主な機能:
- 収入・支出の記録と管理
- 口座別の残高追跡
- 取引履歴の検索・編集・削除
- CSVファイルへのバックアップ
- 残高推移の可視化データ提供

技術スタック:
- Backend: Flask (Python)
- Database: SQLite with SQLAlchemy ORM
- Server: Waitress WSGI Server
- Logging: Python標準ライブラリ（ファイルローテーション対応）

API エンドポイント:
- GET  /api/accounts        - 口座一覧取得
- GET  /api/items          - 項目一覧取得
- GET  /api/transactions   - 取引履歴取得（検索対応）
- POST /api/transactions   - 新規取引追加
- PUT  /api/transactions/<id> - 取引編集
- DELETE /api/transactions/<id> - 取引削除
- GET  /api/backup_csv     - CSVバックアップダウンロード
- GET  /api/balance_history - 残高推移データ取得

環境設定:
- ENVIRONMENT=development  : 開発環境（コンソール + ファイルログ）
- ENVIRONMENT=production   : 本番環境（ファイルログのみ）※デフォルト
- LOG_LEVEL=DEBUG/INFO/WARNING/ERROR/CRITICAL : ログレベル設定

データベース:
- SQLite (money_tracker.db)
- 自動テーブル作成機能
- バックアップ機能付き

ログ機能:
- ファイルローテーション（10MB, 5ファイル保持）
- 環境別ログ出力制御
- 詳細なエラートラッキング

開発環境:
- uvを使用したライブラリと仮想環境の管理
- uv run app.pyで実行される

Author: ShiningWank0
Created: 2025
License: MIT
"""

from flask import Flask, render_template, jsonify, request, send_file, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from waitress import serve
from sqlalchemy import text, inspect
import csv
import os
import glob
import logging
from logging.handlers import RotatingFileHandler
from functools import wraps
import bcrypt
from dotenv import load_dotenv

# .envファイルの読み込み
load_dotenv()

app = Flask(__name__)

# セッション設定
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)  # 2時間でセッションタイムアウト

# ログイン試行回数制限のためのメモリ辞書
login_attempts = {}
LOGIN_ATTEMPT_LIMIT = 5
LOCKOUT_DURATION = 30  # 30分

# ログ設定
def setup_logging():
    """ログシステムを設定"""
    # ログディレクトリを作成
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # 環境変数からログレベルを取得（デフォルトはINFO）
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    # 本番環境フラグを追加(デフォルトはセキュリティのために開発環境)
    is_production = os.getenv('ENVIRONMENT', 'development').lower() == 'production'
    log_level_mapping = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    log_level = log_level_mapping.get(log_level, logging.INFO)
    
    # ログフォーマット
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s'
    )
    
    # ファイルハンドラー(ローテーション付き)(常に有効)
    file_handler = RotatingFileHandler(
        'logs/money_tracker.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    app.logger.addHandler(file_handler)
    
    # コンソールハンドラー(開発環境のみ)
    if not is_production:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(log_level)
        app.logger.addHandler(console_handler)
    
    # アプリケーションロガー設定
    app.logger.setLevel(log_level)
    
    # Werkzeugのログレベルを調整（本番環境では不要なログを抑制）
    werkzeug_level = logging.WARNING if log_level >= logging.INFO else logging.INFO
    logging.getLogger('werkzeug').setLevel(werkzeug_level)
    
    environment_type = "本番環境" if is_production else "開発環境"
    app.logger.info(f"ログシステムを初期化しました ({environment_type}, レベル: {logging.getLevelName(log_level)})")

# 環境変数チェック
def check_auth_setup():
    """認証設定の確認"""
    if not os.path.exists('.env'):
        print("\n⚠️  認証設定が見つかりません")
        print("初回セットアップを実行してください: uv run auth_setup.py")
        print("その後、アプリケーションを開始してください: uv run app.py")
        return False
    
    required_vars = ['LOGIN_USERNAME', 'LOGIN_PASSWORD_HASH', 'SECRET_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n❌ 以下の環境変数が設定されていません: {', '.join(missing_vars)}")
        print("認証設定を再実行してください: uv run auth_setup.py")
        return False
    
    return True

setup_logging()

# 認証設定チェック
if not check_auth_setup():
    exit(1)

app.logger.info("認証設定を確認しました")

# データベース設定
# 相対パスが推奨
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///money_tracker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# デバッグ情報をログ出力
app.logger.info(f"現在の作業ディレクトリ: {os.getcwd()}")
app.logger.info(f"データベースURI: {app.config['SQLALCHEMY_DATABASE_URI']}")

# Transactionモデル
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    item = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(10), nullable=False)  # 'income' or 'expense'
    amount = db.Column(db.Integer, nullable=False)
    balance = db.Column(db.Integer, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'fundItem': self.account,  # フロントエンド用にfundItemとして返す
            'account': self.account,   # 後方互換性のため残す
            'date': self.date.strftime('%Y-%m-%d %H:%M:%S') if self.date.time() != datetime.min.time() else self.date.strftime('%Y-%m-%d'),
            'item': self.item,
            'type': self.type,
            'amount': self.amount,
            'balance': self.balance
        }

def init_db():
    """データベースを初期化する(SQLAlchemy 2.0対応)"""
    try:
        with app.app_context():
            # テーブルの存在確認(SQLAlchemy 2.0対応)
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()

            if 'transaction' not in tables:
                app.logger.info("テーブル 'transaction' が存在しないので作成します。")
                db.create_all()
                app.logger.info("データベースとテーブルが正常に作成されました。")
            else:
                app.logger.info("テーブル 'transaction' は既に存在します。")
    except Exception as e:
        app.logger.error(f"データベース初期化エラー: {e}")
        try:
            with app.app_context():
                db.create_all()
                app.logger.info("フォールバック: テーブルを作成しました。")
        except Exception as fallback_error:
            app.logger.error(f"フォールバック失敗: {fallback_error}")
            raise


def cleanup_old_backups(backup_dir, max_files=3):
    """バックアップディレクトリ内の古いCSVファイルを削除し、最新のmax_files件のみを保持する"""
    # バックアップファイルのパターン
    pattern = os.path.join(backup_dir, 'transactions_backup_*.csv')
    backup_files = glob.glob(pattern)
    
    if len(backup_files) <= max_files:
        return  # ファイル数が上限以下なら何もしない
    
    # ファイルを更新日時でソート（新しい順）
    backup_files.sort(key=os.path.getmtime, reverse=True)
    
    # 古いファイルを削除
    files_to_delete = backup_files[max_files:]
    for file_path in files_to_delete:
        try:
            os.remove(file_path)
            app.logger.info(f"古いバックアップファイルを削除しました: {file_path}")
        except OSError as e:
            app.logger.error(f"バックアップファイルの削除に失敗しました: {file_path}, エラー: {e}")

# 認証関連のユーティリティ関数
def verify_password(password, hash_str):
    """パスワード検証"""
    try:
        password_bytes = password.encode('utf-8')
        hash_bytes = hash_str.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except Exception as e:
        app.logger.error(f"パスワード検証エラー: {e}")
        return False

def is_ip_locked(ip_address):
    """IPアドレスがロックされているかチェック"""
    if ip_address in login_attempts:
        attempts, last_attempt = login_attempts[ip_address]
        if attempts >= LOGIN_ATTEMPT_LIMIT:
            time_since_last = datetime.now() - last_attempt
            if time_since_last.total_seconds() < LOCKOUT_DURATION * 60:
                return True
            else:
                # ロック期間が過ぎたらリセット
                del login_attempts[ip_address]
    return False

def record_login_attempt(ip_address, success=False):
    """ログイン試行を記録"""
    if success:
        # 成功時はリセット
        if ip_address in login_attempts:
            del login_attempts[ip_address]
    else:
        # 失敗時は回数をカウント
        if ip_address in login_attempts:
            attempts, _ = login_attempts[ip_address]
            login_attempts[ip_address] = (attempts + 1, datetime.now())
        else:
            login_attempts[ip_address] = (1, datetime.now())

def login_required(f):
    """ログイン必須デコレータ"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or not session['logged_in']:
            if request.is_json:
                return jsonify({'error': '認証が必要です', 'login_required': True}), 401
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

# テーブル存在確認とテーブル作成のヘルパー関数
def ensure_table_exists():
    """テーブルが存在しない場合に作成する(SQLAlchemy 2.0対応)"""
    try:
        # テーブルの存在確認（簡単なクエリを実行）
        with db.engine.connect() as conn:
            conn.execute(text("SELECT 1 FROM transaction LIMIT 1"))
    except Exception:
        # テーブルが存在しない場合は作成
        app.logger.info("テーブルが存在しないため、作成します...")
        with app.app_context():
            db.create_all()
        app.logger.info("テーブルを作成しました")

# 認証エンドポイント
@app.route("/login")
def login_page():
    """ログインページ"""
    if 'logged_in' in session and session['logged_in']:
        return redirect(url_for('hello_world'))
    return render_template('login.html')

@app.route("/api/login", methods=['POST'])
def login():
    """ログインAPI"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'リクエストデータが無効です'}), 400
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
        
        # IPアドレスロックチェック
        if is_ip_locked(ip_address):
            app.logger.warning(f"ロックされたIPからのログイン試行: {ip_address}")
            return jsonify({
                'error': f'ログイン試行回数が上限に達しました。{LOCKOUT_DURATION}分後に再試行してください。'
            }), 429
        
        # 認証情報の検証
        expected_username = os.getenv('LOGIN_USERNAME')
        expected_password_hash = os.getenv('LOGIN_PASSWORD_HASH')
        
        if not expected_username or not expected_password_hash:
            app.logger.error("認証設定が不完全です")
            return jsonify({'error': 'サーバー設定エラー'}), 500
        
        # ユーザー名とパスワードの検証
        if username == expected_username and verify_password(password, expected_password_hash):
            # ログイン成功
            session['logged_in'] = True
            session['username'] = username
            session['login_time'] = datetime.now().isoformat()
            session.permanent = True
            
            record_login_attempt(ip_address, success=True)
            app.logger.info(f"ユーザー '{username}' がログインしました (IP: {ip_address})")
            
            return jsonify({
                'success': True,
                'message': 'ログインしました',
                'redirect': url_for('hello_world')
            })
        else:
            # ログイン失敗
            record_login_attempt(ip_address, success=False)
            app.logger.warning(f"ログイン失敗: ユーザー '{username}' (IP: {ip_address})")
            
            remaining_attempts = LOGIN_ATTEMPT_LIMIT - login_attempts.get(ip_address, (0, None))[0]
            return jsonify({
                'error': 'ユーザー名またはパスワードが正しくありません',
                'remaining_attempts': max(0, remaining_attempts)
            }), 401
            
    except Exception as e:
        app.logger.error(f"ログイン処理エラー: {str(e)}", exc_info=True)
        return jsonify({'error': 'ログイン処理に失敗しました'}), 500

@app.route("/api/logout", methods=['POST'])
@login_required
def logout():
    """ログアウトAPI"""
    username = session.get('username', 'unknown')
    session.clear()
    app.logger.info(f"ユーザー '{username}' がログアウトしました")
    return jsonify({'success': True, 'message': 'ログアウトしました'})

@app.route("/api/auth_status")
def auth_status():
    """認証状態確認API"""
    if 'logged_in' in session and session['logged_in']:
        return jsonify({
            'authenticated': True,
            'username': session.get('username'),
            'login_time': session.get('login_time')
        })
    return jsonify({'authenticated': False})

@app.route("/")
@login_required
def hello_world():
    return render_template('index.html')

@app.route("/api/accounts")
@login_required
def get_accounts():
    """データベースから口座名（資金項目名）のリストを取得するAPI"""
    app.logger.debug("口座リストを取得中")
    ensure_table_exists()
    # Get distinct accounts from transactions in the database
    db_accounts_query = db.session.query(Transaction.account.distinct()).all()
    # Use a set for efficient addition and uniqueness
    fund_items_set = {acc[0] for acc in db_accounts_query if acc[0]} 
    
    # Convert set to list and sort alphabetically
    sorted_fund_item_list = sorted(list(fund_items_set))
    
    app.logger.debug(f"口座リスト取得完了: {len(sorted_fund_item_list)}件")
    return jsonify(sorted_fund_item_list)

@app.route("/api/items")
@login_required
def get_items():
    """データベースから項目名（item）のリストを取得するAPI"""
    app.logger.debug("項目リストを取得中")
    ensure_table_exists()
    items = db.session.query(Transaction.item.distinct()).order_by(Transaction.item).all()
    item_list = [item[0] for item in items]
    app.logger.debug(f"項目リスト取得完了: {len(item_list)}件")
    return jsonify(item_list)

@app.route("/api/transactions")
@login_required
def get_transactions():
    """取引履歴をJSON形式で返すAPI"""
    search_query = request.args.get('search', '').strip()
    account = request.args.get('account', '').strip()
    
    app.logger.debug(f"取引履歴を取得中 - 検索: '{search_query}', 口座: '{account}'")
    
    ensure_table_exists()
    
    query = Transaction.query
    
    # 検索クエリがある場合、項目名で部分一致検索
    if search_query:
        query = query.filter(Transaction.item.like(f'%{search_query}%'))
    
    # 口座指定がある場合、口座でフィルタ
    if account:
        query = query.filter(Transaction.account == account)
    
    transactions = query.all()
    app.logger.debug(f"取引履歴取得完了: {len(transactions)}件")
    return jsonify([t.to_dict() for t in transactions])

@app.route("/api/transactions", methods=['POST'])
@login_required
def add_transaction():
    """新しい取引を追加するAPI"""
    try:
        data = request.get_json()
        
        # 必須フィールドの検証
        required_fields = ['account', 'date', 'item', 'type', 'amount']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'{field}は必須項目です'}), 400
        
        # 日付の解析
        try:
            if 'time' in data and data['time'].strip():
                date_str = f"{data['date']} {data['time']}"
                date_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M')
            else:
                date_obj = datetime.strptime(data['date'], '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': '日付形式が正しくありません'}), 400
        
        # 金額の検証
        try:
            amount = int(data['amount'])
            if amount <= 0:
                return jsonify({'error': '金額は正の数値である必要があります'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': '金額は数値である必要があります'}), 400
        
        # タイプの検証
        if data['type'] not in ['income', 'expense']:
            return jsonify({'error': 'typeは"income"または"expense"である必要があります'}), 400
        
        # 指定された口座の最新残高を取得
        account = data['account']
        latest_transaction = Transaction.query.filter_by(account=account).order_by(Transaction.date.desc(), Transaction.id.desc()).first()
        current_balance = latest_transaction.balance if latest_transaction else 0
        
        # 新しい残高を計算
        if data['type'] == 'income':
            new_balance = current_balance + amount
        else:
            new_balance = current_balance - amount
        
        # 新しいトランザクションを作成
        transaction = Transaction(
            account=account,
            date=date_obj,
            item=data['item'],
            type=data['type'],
            amount=amount,
            balance=new_balance
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        app.logger.info(f"新しい取引を追加しました: {account} - {data['item']} - {amount}円")
        
        return jsonify({
            'message': '取引が正常に追加されました',
            'transaction': transaction.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"取引の追加に失敗しました: {str(e)}", exc_info=True)
        return jsonify({'error': f'取引の追加に失敗しました: {str(e)}'}), 500

@app.route("/api/backup_csv")
@login_required
def backup_to_csv():
    """データベースのデータをCSVファイルにバックアップ"""
    app.logger.info("CSVバックアップを開始しています")
    
    transactions = Transaction.query.order_by(Transaction.date).all()
    
    # バックアップディレクトリがなければ作成
    backup_dir = 'backups'
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        app.logger.info(f"バックアップディレクトリを作成しました: {backup_dir}")
    
    # 古いバックアップファイルを先にクリーンアップ（最新3件のみ保持）
    cleanup_old_backups(backup_dir, max_files=2)  # 新しいファイルを作成するので2件に制限
    
    # CSVファイル名（タイムスタンプ付き、マイクロ秒も含めて重複を防ぐ）
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    csv_filename = f'{backup_dir}/transactions_backup_{timestamp}.csv'
    
    # 既に同じファイル名が存在する場合は、追加のタイムスタンプを付ける
    counter = 1
    original_filename = csv_filename
    while os.path.exists(csv_filename):
        base_name = original_filename.rsplit('.', 1)[0]
        csv_filename = f'{base_name}_{counter}.csv'
        counter += 1
    
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['id', 'account', 'date', 'item', 'type', 'amount', 'balance']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for transaction in transactions:
            # CSVには必要なフィールドのみを含める
            row_data = {
                'id': transaction.id,
                'account': transaction.account,
                'date': transaction.date.strftime('%Y-%m-%d %H:%M:%S') if transaction.date.time() != datetime.min.time() else transaction.date.strftime('%Y-%m-%d'),
                'item': transaction.item,
                'type': transaction.type,
                'amount': transaction.amount,
                'balance': transaction.balance
            }
            writer.writerow(row_data)
    
    app.logger.info(f"CSVバックアップファイルを作成しました: {csv_filename}")
    
    # ファイルをダウンロードとして返す
    return send_file(csv_filename, mimetype='text/csv', as_attachment=True, download_name=os.path.basename(csv_filename))

@app.route("/api/download_log")
@login_required
def download_log():
    """最新のログファイルをダウンロードするAPI"""
    app.logger.info("ログファイルダウンロードを開始しています")
    
    try:
        # ログディレクトリの確認
        log_dir = 'logs'
        if not os.path.exists(log_dir):
            app.logger.warning("ログディレクトリが存在しません")
            return jsonify({'error': 'ログファイルが見つかりません'}), 404
        
        # ログファイルの検索パターン
        log_pattern = os.path.join(log_dir, 'money_tracker.log*')
        log_files = glob.glob(log_pattern)
        
        if not log_files:
            app.logger.warning("ログファイルが見つかりません")
            return jsonify({'error': 'ログファイルが見つかりません'}), 404
        
        # 最新のログファイルを取得（ファイル名でソート）
        # money_tracker.logが最新、money_tracker.log.1が次に新しい
        log_files.sort(key=lambda x: (
            0 if x.endswith('money_tracker.log') else int(x.split('.')[-1])
        ))
        
        latest_log_file = log_files[0]
        
        # ファイルの存在確認
        if not os.path.exists(latest_log_file):
            app.logger.error(f"ログファイルが存在しません: {latest_log_file}")
            return jsonify({'error': 'ログファイルにアクセスできません'}), 500
        
        # ダウンロード用のファイル名を生成（タイムスタンプ付き）
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        download_name = f'money_tracker_log_{timestamp}.log'
        
        app.logger.info(f"ログファイルをダウンロード提供: {latest_log_file}")
        
        # ファイルをダウンロードとして返す
        return send_file(
            latest_log_file, 
            mimetype='text/plain', 
            as_attachment=True, 
            download_name=download_name
        )
        
    except Exception as e:
        app.logger.error(f"ログファイルダウンロードでエラーが発生しました: {str(e)}", exc_info=True)
        return jsonify({'error': f'ログファイルダウンロードに失敗しました: {str(e)}'}), 500

@app.route("/api/transactions/<int:transaction_id>", methods=['PUT', 'PATCH'])
@login_required
def update_transaction(transaction_id):
    """既存取引の編集API"""
    try:
        data = request.get_json()
        # 必須フィールドの検証
        required_fields = ['account', 'date', 'item', 'type', 'amount']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'{field}は必須項目です'}), 400

        # 日付の解析
        try:
            if 'time' in data and data['time'].strip():
                date_str = f"{data['date']} {data['time']}"
                date_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M')
            else:
                date_obj = datetime.strptime(data['date'], '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': '日付形式が正しくありません'}), 400

        # 金額の検証
        try:
            amount = int(data['amount'])
            if amount <= 0:
                return jsonify({'error': '金額は正の数値である必要があります'}), 400
        except (ValueError, TypeError):
            return jsonify({'error': '金額は数値である必要があります'}), 400

        # タイプの検証
        if data['type'] not in ['income', 'expense']:
            return jsonify({'error': 'typeは"income"または"expense"である必要があります'}), 400

        # 既存トランザクション取得
        transaction = Transaction.query.get(transaction_id)
        if not transaction:
            return jsonify({'error': '該当取引が見つかりません'}), 404

        # 変更前の情報
        old_account = transaction.account

        # トランザクション内容を更新
        transaction.account = data['account']
        transaction.date = date_obj
        transaction.item = data['item']
        transaction.type = data['type']
        transaction.amount = amount
        db.session.commit()

        # 残高の再計算（同じ口座の全取引、日付昇順）
        for account in set([old_account, data['account']]):
            txs = Transaction.query.filter_by(account=account).order_by(Transaction.date, Transaction.id).all()
            running_balance = 0
            for tx in txs:
                if tx.type == 'income':
                    running_balance += tx.amount
                else:
                    running_balance -= tx.amount
                tx.balance = running_balance
            db.session.commit()

        app.logger.info(f"取引を更新しました: ID {transaction_id} - {data['account']} - {data['item']}")

        return jsonify({'message': '取引が更新されました', 'transaction': transaction.to_dict()})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"取引の更新に失敗しました: {str(e)}", exc_info=True)
        return jsonify({'error': f'取引の更新に失敗しました: {str(e)}'}), 500

@app.route("/api/transactions/<int:transaction_id>", methods=['DELETE'])
@login_required
def delete_transaction(transaction_id):
    """取引の削除API"""
    try:
        transaction = Transaction.query.get(transaction_id)
        if not transaction:
            return jsonify({'error': '該当取引が見つかりません'}), 404
        
        account = transaction.account
        item = transaction.item
        amount = transaction.amount
        
        db.session.delete(transaction)
        db.session.commit()
        
        app.logger.info(f"取引を削除しました: ID {transaction_id} - {account} - {item} - {amount}円")
        # 残高の再計算（同じ口座の全取引、日付昇順）
        txs = Transaction.query.filter_by(account=account).order_by(Transaction.date, Transaction.id).all()
        running_balance = 0
        for tx in txs:
            if tx.type == 'income':
                running_balance += tx.amount
            else:
                running_balance -= tx.amount
            tx.balance = running_balance
        db.session.commit()
        return jsonify({'message': '取引が削除されました'})
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"取引の削除に失敗しました: {str(e)}", exc_info=True)
        return jsonify({'error': f'取引の削除に失敗しました: {str(e)}'}), 500

@app.route("/api/balance_history")
@login_required
def get_balance_history():
    """残高推移データを取得するAPI"""
    app.logger.debug("残高履歴を取得中")
    
    try:
        # 全ての取引を日付順で取得
        transactions = Transaction.query.order_by(Transaction.date, Transaction.id).all()
        
        if not transactions:
            app.logger.debug("取引データが存在しません")
            return jsonify({'accounts': [], 'dates': [], 'balances': {}})
        
        # 口座ごとに残高推移を計算
        account_balances = {}
        all_dates = set()
        
        for transaction in transactions:
            account = transaction.account
            date_str = transaction.date.strftime('%Y-%m-%d')
            
            if account not in account_balances:
                account_balances[account] = {}
            
            account_balances[account][date_str] = transaction.balance
            all_dates.add(date_str)
        
        # 日付を昇順でソート
        sorted_dates = sorted(list(all_dates))
        
        # 各口座の残高データを日付順に整理（データがない日は前の残高を使用）
        result_balances = {}
        for account in account_balances:
            result_balances[account] = []
            last_balance = 0
            
            for date in sorted_dates:
                if date in account_balances[account]:
                    last_balance = account_balances[account][date]
                result_balances[account].append(last_balance)
        
        app.logger.debug(f"残高履歴取得完了: {len(account_balances)}口座, {len(sorted_dates)}日分")
        
        return jsonify({
            'accounts': list(account_balances.keys()),
            'dates': sorted_dates,
            'balances': result_balances
        })
        
    except Exception as e:
        app.logger.error(f"残高履歴の取得に失敗しました: {str(e)}", exc_info=True)
        return jsonify({'error': f'残高履歴の取得に失敗しました: {str(e)}'}), 500


if __name__ == "__main__":
    # 0.0.0.0に設定することで、ローカルホストから以外のアクセスも受け付ける
    # app.run(host='0.0.0.0', port=4000, debug=True)
    try:
        app.logger.info("アプリケーションを開始しています...")
        init_db()
        app.logger.info("サーバーを起動します (host=0.0.0.0, port=4000)")
        serve(app, host='0.0.0.0', port=4000)
    except KeyboardInterrupt:
        app.logger.info("アプリケーションが手動で停止されました")
    except Exception as e:
        app.logger.error(f"アプリケーション実行中にエラーが発生しました: {e}", exc_info=True)
    finally:
        app.logger.info("アプリケーションを終了します")