from flask import Flask, render_template, jsonify, request, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import csv
import os
import glob

app = Flask(__name__)

# データベース設定
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///money_tracker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

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
            print(f"古いバックアップファイルを削除しました: {file_path}")
        except OSError as e:
            print(f"バックアップファイルの削除に失敗しました: {file_path}, エラー: {e}")

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

@app.route("/")
def hello_world():
    return render_template('index.html')

@app.route("/api/accounts")
def get_accounts():
    """データベースから口座名（資金項目名）のリストを取得するAPI"""
    # Get distinct accounts from transactions in the database
    db_accounts_query = db.session.query(Transaction.account.distinct()).all()
    # Use a set for efficient addition and uniqueness
    fund_items_set = {acc[0] for acc in db_accounts_query if acc[0]} 
    
    # Convert set to list and sort alphabetically
    sorted_fund_item_list = sorted(list(fund_items_set))
    
    return jsonify(sorted_fund_item_list)

@app.route("/api/items")
def get_items():
    """データベースから項目名（item）のリストを取得するAPI"""
    items = db.session.query(Transaction.item.distinct()).order_by(Transaction.item).all()
    item_list = [item[0] for item in items]
    return jsonify(item_list)

@app.route("/api/transactions")
def get_transactions():
    """取引履歴をJSON形式で返すAPI"""
    search_query = request.args.get('search', '').strip()
    account = request.args.get('account', '').strip()
    
    query = Transaction.query
    
    # 検索クエリがある場合、項目名で部分一致検索
    if search_query:
        query = query.filter(Transaction.item.like(f'%{search_query}%'))
    
    # 口座指定がある場合、口座でフィルタ
    if account:
        query = query.filter(Transaction.account == account)
    
    transactions = query.all()
    return jsonify([t.to_dict() for t in transactions])

@app.route("/api/transactions", methods=['POST'])
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
        
        return jsonify({
            'message': '取引が正常に追加されました',
            'transaction': transaction.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'取引の追加に失敗しました: {str(e)}'}), 500

@app.route("/api/backup_csv")
def backup_to_csv():
    """データベースのデータをCSVファイルにバックアップ"""
    transactions = Transaction.query.order_by(Transaction.date).all()
    
    # バックアップディレクトリがなければ作成
    backup_dir = 'backups'
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
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
    
    print(f"CSVバックアップファイルを作成しました: {csv_filename}")
    
    # ファイルをダウンロードとして返す
    return send_file(csv_filename, mimetype='text/csv', as_attachment=True, download_name=os.path.basename(csv_filename))

@app.route("/api/transactions/<int:transaction_id>", methods=['PUT', 'PATCH'])
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
        old_date = transaction.date

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

        return jsonify({'message': '取引が更新されました', 'transaction': transaction.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'取引の更新に失敗しました: {str(e)}'}), 500

@app.route("/api/transactions/<int:transaction_id>", methods=['DELETE'])
def delete_transaction(transaction_id):
    """取引の削除API"""
    try:
        transaction = Transaction.query.get(transaction_id)
        if not transaction:
            return jsonify({'error': '該当取引が見つかりません'}), 404
        account = transaction.account
        db.session.delete(transaction)
        db.session.commit()
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
        return jsonify({'error': f'取引の削除に失敗しました: {str(e)}'}), 500

@app.route("/api/balance_history")
def get_balance_history():
    """残高推移データを取得するAPI"""
    try:
        # 全ての取引を日付順で取得
        transactions = Transaction.query.order_by(Transaction.date, Transaction.id).all()
        
        if not transactions:
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
        
        return jsonify({
            'accounts': list(account_balances.keys()),
            'dates': sorted_dates,
            'balances': result_balances
        })
        
    except Exception as e:
        return jsonify({'error': f'残高履歴の取得に失敗しました: {str(e)}'}), 500

# 起動時(各ワーカーの最初のリクエスト時)にテーブルを作成
@app.before_first_request
def initialize_database():
    try:
        db.create_all()
    except Exception:
        pass

# # モデル定義の後にテーブルを自動作成
# with app.app_context():
#     db.create_all()

if __name__ == "__main__":
    # 0.0.0.0に設定することで、ローカルホストから以外のアクセスも受け付ける
    app.run(host='0.0.0.0', port=4000, debug=True)