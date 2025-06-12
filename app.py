from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import csv
import os

app = Flask(__name__)

# データベース設定
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///money_tracker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Base fund items that should always be available
BASE_FUND_ITEMS = ['メイン口座', 'クレジットカード', '予備費']

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
    """データベースから口座名（資金項目名）のリストを取得するAPI。基本項目も含む。"""
    # Get distinct accounts from transactions in the database
    db_accounts_query = db.session.query(Transaction.account.distinct()).all()
    # Use a set for efficient addition and uniqueness
    fund_items_set = {acc[0] for acc in db_accounts_query if acc[0]} 

    # Add predefined base accounts to the set
    for item_name in BASE_FUND_ITEMS:
        fund_items_set.add(item_name)
    
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
    
    # CSVファイル名（タイムスタンプ付き）
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_filename = f'{backup_dir}/transactions_backup_{timestamp}.csv'
    
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['id', 'account', 'date', 'item', 'type', 'amount', 'balance']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for transaction in transactions:
            writer.writerow(transaction.to_dict())
    
    return jsonify({'message': f'バックアップが完了しました: {csv_filename}', 'filename': csv_filename})

def init_demo_data():
    """デモデータをデータベースに初期投入"""
    # 既にデータがあるかチェック
    if Transaction.query.first():
        print("データベースに既にデータが存在します。初期データの投入をスキップします。")
        return
    
    # デモデータ（main.jsと同じデータ）
    demo_transactions = [
        {'id': 1, 'account': 'メイン口座', 'date': '2025-06-10 09:00:00', 'item': '給与', 'type': 'income', 'amount': 300000},
        {'id': 2, 'account': 'メイン口座', 'date': '2025-06-09', 'item': '家賃', 'type': 'expense', 'amount': 80000},
        {'id': 3, 'account': 'メイン口座', 'date': '2025-06-08 14:15:00', 'item': 'スーパーマーケット', 'type': 'expense', 'amount': 5500},
        {'id': 4, 'account': 'メイン口座', 'date': '2025-06-07', 'item': '書籍購入', 'type': 'expense', 'amount': 2400},
        {'id': 5, 'account': 'メイン口座', 'date': '2025-06-05 10:00:00', 'item': 'フリマ売上', 'type': 'income', 'amount': 3000},
        {'id': 6, 'account': 'メイン口座', 'date': '2025-06-04', 'item': '通信費', 'type': 'expense', 'amount': 6000},
        {'id': 7, 'account': 'メイン口座', 'date': '2025-06-03 18:30:00', 'item': '外食', 'type': 'expense', 'amount': 1800},
        {'id': 8, 'account': 'クレジットカード', 'date': '2025-06-10 10:00:00', 'item': 'オンラインショッピング', 'type': 'expense', 'amount': 12000},
        {'id': 9, 'account': 'クレジットカード', 'date': '2025-06-08', 'item': 'カフェ', 'type': 'expense', 'amount': 800},
        {'id': 10, 'account': 'クレジットカード', 'date': '2025-06-05 20:00:00', 'item': '映画', 'type': 'expense', 'amount': 1900},
        {'id': 11, 'account': '予備費', 'date': '2025-06-01', 'item': '初期資金', 'type': 'income', 'amount': 50000},
        {'id': 12, 'account': '予備費', 'date': '2025-06-06', 'item': '友人への貸付', 'type': 'expense', 'amount': 5000},
    ]
    
    # 各口座ごとに残高を計算してデータベースに追加
    account_names = ['メイン口座', 'クレジットカード', '予備費']
    all_transactions = []
    
    for account in account_names:
        running_balance = 0
        account_transactions = [tx for tx in demo_transactions if tx['account'] == account]
        account_transactions.sort(key=lambda x: datetime.strptime(
            x['date'] if ' ' in x['date'] else x['date'] + ' 00:00:00', 
            '%Y-%m-%d %H:%M:%S'
        ))
        
        for tx_data in account_transactions:
            if tx_data['type'] == 'income':
                running_balance += tx_data['amount']
            else:
                running_balance -= tx_data['amount']
            
            # 日付文字列をdatetimeオブジェクトに変換
            date_str = tx_data['date'] if ' ' in tx_data['date'] else tx_data['date'] + ' 00:00:00'
            date_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
            
            transaction = Transaction(
                id=tx_data['id'],  # 元のIDを保持
                account=tx_data['account'],
                date=date_obj,
                item=tx_data['item'],
                type=tx_data['type'],
                amount=tx_data['amount'],
                balance=running_balance
            )
            all_transactions.append(transaction)
    
    # データベースに一括追加
    db.session.add_all(all_transactions)
    db.session.commit()
    print(f"デモデータ {len(all_transactions)} 件をデータベースに追加しました。")

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

if __name__ == "__main__":
    with app.app_context():
        # データベーステーブルを作成
        db.create_all()
        # デモデータを初期投入
        init_demo_data()
    
    # 0.0.0.0に設定することで、ローカルホストから以外のアクセスも受け付ける
    app.run(host='0.0.0.0', port=4000, debug=True)