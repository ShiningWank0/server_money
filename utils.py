"""
Server Money - ユーティリティ関数

このファイルは、バックアップ管理、データベース初期化など
の共通機能を提供します。
"""

import os
import glob
from datetime import datetime
from sqlalchemy import text, inspect
from models import db

def cleanup_old_backups(backup_dir, max_files=3):
    """バックアップディレクトリ内の古いCSVファイルを削除し、最新のmax_files件のみを保持する
    
    Args:
        backup_dir (str): バックアップディレクトリのパス
        max_files (int): 保持する最大ファイル数（デフォルト: 3）
    """
    from flask import current_app
    
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
            current_app.logger.info(f"古いバックアップファイルを削除しました: {file_path}")
        except OSError as e:
            current_app.logger.error(f"バックアップファイルの削除に失敗しました: {file_path}, エラー: {e}")

def init_db(app):
    """データベースを初期化する(SQLAlchemy 2.0対応)
    
    Args:
        app: Flaskアプリケーションインスタンス
    """
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

def ensure_table_exists():
    """テーブルが存在しない場合に作成する(SQLAlchemy 2.0対応)"""
    from flask import current_app
    
    try:
        # テーブルの存在確認（簡単なクエリを実行）
        with db.engine.connect() as conn:
            conn.execute(text("SELECT 1 FROM transaction LIMIT 1"))
    except Exception:
        # テーブルが存在しない場合は作成
        current_app.logger.info("テーブルが存在しないため、作成します...")
        with current_app.app_context():
            db.create_all()
        current_app.logger.info("テーブルを作成しました")

def generate_unique_filename(directory, base_name, extension):
    """ユニークなファイル名を生成
    
    Args:
        directory (str): ディレクトリパス
        base_name (str): ベースファイル名
        extension (str): 拡張子
        
    Returns:
        str: ユニークなファイルパス
    """
    # タイムスタンプ付きファイル名（マイクロ秒も含めて重複を防ぐ）
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    filename = f'{directory}/{base_name}_{timestamp}.{extension}'
    
    # 既に同じファイル名が存在する場合は、追加のカウンターを付ける
    counter = 1
    original_filename = filename
    while os.path.exists(filename):
        base_part = original_filename.rsplit('.', 1)[0]
        filename = f'{base_part}_{counter}.{extension}'
        counter += 1
    
    return filename

def validate_transaction_data(data, required_fields=None):
    """取引データのバリデーション
    
    Args:
        data (dict): バリデーション対象のデータ
        required_fields (list): 必須フィールドのリスト
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if required_fields is None:
        required_fields = ['account', 'date', 'item', 'type', 'amount']
    
    # 必須フィールドの検証
    for field in required_fields:
        if field not in data or not data[field]:
            return False, f'{field}は必須項目です'
    
    # タイプの検証
    if data.get('type') not in ['income', 'expense']:
        return False, 'typeは"income"または"expense"である必要があります'
    
    # 金額の検証
    try:
        amount = int(data['amount'])
        if amount <= 0:
            return False, '金額は正の数値である必要があります'
    except (ValueError, TypeError):
        return False, '金額は数値である必要があります'
    
    return True, None

def parse_transaction_date(date_str, time_str=None):
    """取引日時の解析
    
    Args:
        date_str (str): 日付文字列
        time_str (str, optional): 時刻文字列
        
    Returns:
        datetime: 解析された日時
        
    Raises:
        ValueError: 日付形式が正しくない場合
    """
    try:
        if time_str and time_str.strip():
            date_time_str = f"{date_str} {time_str}"
            return datetime.strptime(date_time_str, '%Y-%m-%d %H:%M')
        else:
            return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        raise ValueError('日付形式が正しくありません')