"""
Server Money - API関連ルート

このファイルは、取引管理、データ分析、バックアップなどの
メインAPI エンドポイントを定義します。
"""

import csv
import os
import glob
from datetime import datetime
from flask import Blueprint, jsonify, request, send_file
from auth import login_required
from models import db, Transaction
from utils import (
    ensure_table_exists, cleanup_old_backups, 
    generate_unique_filename, validate_transaction_data, 
    parse_transaction_date
)

# Blueprintの作成
api_bp = Blueprint('api', __name__)

@api_bp.route("/api/accounts")
@login_required
def get_accounts():
    """データベースから口座名（資金項目名）のリストを取得するAPI"""
    from flask import current_app
    
    current_app.logger.debug("口座リストを取得中")
    ensure_table_exists()
    
    # Get distinct accounts from transactions in the database
    db_accounts_query = db.session.query(Transaction.account.distinct()).all()
    # Use a set for efficient addition and uniqueness
    fund_items_set = {acc[0] for acc in db_accounts_query if acc[0]} 
    
    # Convert set to list and sort alphabetically
    sorted_fund_item_list = sorted(list(fund_items_set))
    
    current_app.logger.debug(f"口座リスト取得完了: {len(sorted_fund_item_list)}件")
    return jsonify(sorted_fund_item_list)

@api_bp.route("/api/items")
@login_required
def get_items():
    """データベースから項目名（item）のリストを取得するAPI"""
    from flask import current_app
    
    current_app.logger.debug("項目リストを取得中")
    ensure_table_exists()
    
    items = db.session.query(Transaction.item.distinct()).order_by(Transaction.item).all()
    item_list = [item[0] for item in items]
    
    current_app.logger.debug(f"項目リスト取得完了: {len(item_list)}件")
    return jsonify(item_list)

@api_bp.route("/api/transactions")
@login_required
def get_transactions():
    """取引履歴をJSON形式で返すAPI"""
    from flask import current_app
    
    search_query = request.args.get('search', '').strip()
    account = request.args.get('account', '').strip()
    
    current_app.logger.debug(f"取引履歴を取得中 - 検索: '{search_query}', 口座: '{account}'")
    
    ensure_table_exists()
    
    query = Transaction.query
    
    # 検索クエリがある場合、項目名で部分一致検索
    if search_query:
        query = query.filter(Transaction.item.like(f'%{search_query}%'))
    
    # 口座指定がある場合、口座でフィルタ
    if account:
        query = query.filter(Transaction.account == account)
    
    transactions = query.all()
    current_app.logger.debug(f"取引履歴取得完了: {len(transactions)}件")
    return jsonify([t.to_dict() for t in transactions])

@api_bp.route("/api/transactions", methods=['POST'])
@login_required
def add_transaction():
    """新しい取引を追加するAPI"""
    from flask import current_app
    
    try:
        data = request.get_json()
        
        # データバリデーション
        is_valid, error_message = validate_transaction_data(data)
        if not is_valid:
            return jsonify({'error': error_message}), 400
        
        # 日付の解析
        try:
            date_obj = parse_transaction_date(data['date'], data.get('time'))
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        
        # 金額の変換
        amount = int(data['amount'])
        
        # 指定された口座の最新残高を取得
        account = data['account']
        latest_transaction = Transaction.query.filter_by(account=account).order_by(
            Transaction.date.desc(), Transaction.id.desc()).first()
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
        
        current_app.logger.info(f"新しい取引を追加しました: {account} - {data['item']} - {amount}円")
        
        return jsonify({
            'message': '取引が正常に追加されました',
            'transaction': transaction.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"取引の追加に失敗しました: {str(e)}", exc_info=True)
        return jsonify({'error': f'取引の追加に失敗しました: {str(e)}'}), 500

@api_bp.route("/api/transactions/<int:transaction_id>", methods=['PUT', 'PATCH'])
@login_required
def update_transaction(transaction_id):
    """既存取引の編集API"""
    from flask import current_app
    
    try:
        data = request.get_json()
        
        # データバリデーション
        is_valid, error_message = validate_transaction_data(data)
        if not is_valid:
            return jsonify({'error': error_message}), 400

        # 日付の解析
        try:
            date_obj = parse_transaction_date(data['date'], data.get('time'))
        except ValueError as e:
            return jsonify({'error': str(e)}), 400

        # 金額の変換
        amount = int(data['amount'])

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
            _recalculate_balance_for_account(account)

        current_app.logger.info(f"取引を更新しました: ID {transaction_id} - {data['account']} - {data['item']}")

        return jsonify({'message': '取引が更新されました', 'transaction': transaction.to_dict()})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"取引の更新に失敗しました: {str(e)}", exc_info=True)
        return jsonify({'error': f'取引の更新に失敗しました: {str(e)}'}), 500

@api_bp.route("/api/transactions/<int:transaction_id>", methods=['DELETE'])
@login_required
def delete_transaction(transaction_id):
    """取引の削除API"""
    from flask import current_app
    
    try:
        transaction = Transaction.query.get(transaction_id)
        if not transaction:
            return jsonify({'error': '該当取引が見つかりません'}), 404
        
        account = transaction.account
        item = transaction.item
        amount = transaction.amount
        
        db.session.delete(transaction)
        db.session.commit()
        
        current_app.logger.info(f"取引を削除しました: ID {transaction_id} - {account} - {item} - {amount}円")
        
        # 残高の再計算
        _recalculate_balance_for_account(account)
        
        return jsonify({'message': '取引が削除されました'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"取引の削除に失敗しました: {str(e)}", exc_info=True)
        return jsonify({'error': f'取引の削除に失敗しました: {str(e)}'}), 500

@api_bp.route("/api/balance_history")
@login_required
def get_balance_history():
    """残高推移データを取得するAPI"""
    from flask import current_app
    
    current_app.logger.debug("残高履歴を取得中")
    
    try:
        # 全ての取引を日付順で取得
        transactions = Transaction.query.order_by(Transaction.date, Transaction.id).all()
        
        if not transactions:
            current_app.logger.debug("取引データが存在しません")
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
        
        current_app.logger.debug(f"残高履歴取得完了: {len(account_balances)}口座, {len(sorted_dates)}日分")
        
        return jsonify({
            'accounts': list(account_balances.keys()),
            'dates': sorted_dates,
            'balances': result_balances
        })
        
    except Exception as e:
        current_app.logger.error(f"残高履歴の取得に失敗しました: {str(e)}", exc_info=True)
        return jsonify({'error': f'残高履歴の取得に失敗しました: {str(e)}'}), 500

@api_bp.route("/api/backup_csv")
@login_required
def backup_to_csv():
    """データベースのデータをCSVファイルにバックアップ"""
    from flask import current_app
    
    current_app.logger.info("CSVバックアップを開始しています")
    
    transactions = Transaction.query.order_by(Transaction.date).all()
    
    # バックアップディレクトリがなければ作成
    backup_dir = 'backups'
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        current_app.logger.info(f"バックアップディレクトリを作成しました: {backup_dir}")
    
    # 古いバックアップファイルを先にクリーンアップ（最新3件のみ保持）
    cleanup_old_backups(backup_dir, max_files=2)  # 新しいファイルを作成するので2件に制限
    
    # ユニークなCSVファイル名を生成
    csv_filename = generate_unique_filename(backup_dir, 'transactions_backup', 'csv')
    
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
    
    current_app.logger.info(f"CSVバックアップファイルを作成しました: {csv_filename}")
    
    # ファイルをダウンロードとして返す
    return send_file(csv_filename, mimetype='text/csv', as_attachment=True, download_name=os.path.basename(csv_filename))

@api_bp.route("/api/download_log")
@login_required
def download_log():
    """最新のログファイルをダウンロードするAPI"""
    from flask import current_app
    
    current_app.logger.info("ログファイルダウンロードを開始しています")
    
    try:
        # ログディレクトリの確認
        log_dir = 'logs'
        if not os.path.exists(log_dir):
            current_app.logger.warning("ログディレクトリが存在しません")
            return jsonify({'error': 'ログファイルが見つかりません'}), 404
        
        # ログファイルの検索パターン
        log_pattern = os.path.join(log_dir, 'money_tracker.log*')
        log_files = glob.glob(log_pattern)
        
        if not log_files:
            current_app.logger.warning("ログファイルが見つかりません")
            return jsonify({'error': 'ログファイルが見つかりません'}), 404
        
        # 最新のログファイルを取得（ファイル名でソート）
        # money_tracker.logが最新、money_tracker.log.1が次に新しい
        log_files.sort(key=lambda x: (
            0 if x.endswith('money_tracker.log') else int(x.split('.')[-1])
        ))
        
        latest_log_file = log_files[0]
        
        # ファイルの存在確認
        if not os.path.exists(latest_log_file):
            current_app.logger.error(f"ログファイルが存在しません: {latest_log_file}")
            return jsonify({'error': 'ログファイルにアクセスできません'}), 500
        
        # ダウンロード用のファイル名を生成（タイムスタンプ付き）
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        download_name = f'money_tracker_log_{timestamp}.log'
        
        current_app.logger.info(f"ログファイルをダウンロード提供: {latest_log_file}")
        
        # ファイルをダウンロードとして返す
        return send_file(
            latest_log_file, 
            mimetype='text/plain', 
            as_attachment=True, 
            download_name=download_name
        )
        
    except Exception as e:
        current_app.logger.error(f"ログファイルダウンロードでエラーが発生しました: {str(e)}", exc_info=True)
        return jsonify({'error': f'ログファイルダウンロードに失敗しました: {str(e)}'}), 500

def _recalculate_balance_for_account(account):
    """指定口座の残高を再計算する内部関数
    
    Args:
        account (str): 口座名
    """
    txs = Transaction.query.filter_by(account=account).order_by(Transaction.date, Transaction.id).all()
    running_balance = 0
    for tx in txs:
        if tx.type == 'income':
            running_balance += tx.amount
        else:
            running_balance -= tx.amount
        tx.balance = running_balance
    db.session.commit()