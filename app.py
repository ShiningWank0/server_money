from flask import Flask, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import csv
import os

app = Flask(__name__)

# データベース設定
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///money_tracker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

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
            'account': self.account,
            'date': self.date.strftime('%Y-%m-%d %H:%M:%S') if self.date.time() != datetime.min.time() else self.date.strftime('%Y-%m-%d'),
            'item': self.item,
            'type': self.type,
            'amount': self.amount,
            'balance': self.balance
        }

@app.route("/")
def hello_world():
    return render_template('index.html')

@app.route("/api/transactions")
def get_transactions():
    """取引履歴をJSON形式で返すAPI"""
    transactions = Transaction.query.all()
    return jsonify([t.to_dict() for t in transactions])

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

if __name__ == "__main__":
    with app.app_context():
        # データベーステーブルを作成
        db.create_all()
        # デモデータを初期投入
        init_demo_data()
    
    # 0.0.0.0に設定することで、ローカルホストから以外のアクセスも受け付ける
    app.run(host='0.0.0.0', port=4000, debug=True)