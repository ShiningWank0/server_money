// Vue.js アプリケーションのロジック

const { createApp } = Vue;

createApp({
    data() {
        return {
            transactions: [],
            fundItemNames: [],
            itemNames: [], // 項目名リスト
            selectedFundItem: 'すべて',
            dateSortOrder: 'desc',
            showAccountDropdown: false,
            loading: true,
            searchQuery: '',
            searchTimeout: null,
            showAddTransactionModal: false,
            showFundItemDropdown: false,  // 資金項目ドロップダウンの表示状態
            newTransaction: {
                fundItem: '',
                date: '',
                time: '',
                item: '',
                type: 'expense',
                amount: ''
            }
        }
    },
    computed: {
        // 検索結果に基づいてフィルタリングされた取引
        filteredTransactions() {
            let filtered = this.transactions;
            
            // 資金項目によるフィルタリング
            if (this.selectedFundItem !== 'すべて') {
                filtered = filtered.filter(tx => {
                    const fundItem = tx.fundItem || tx.account;
                    return fundItem === this.selectedFundItem;
                });
            }
            
            // 検索クエリによるフィルタリング
            if (this.searchQuery.trim()) {
                const query = this.searchQuery.trim().toLowerCase();
                filtered = filtered.filter(tx => {
                    return (
                        tx.item.toLowerCase().includes(query) ||
                        (tx.fundItem || tx.account || '').toLowerCase().includes(query) ||
                        tx.date.includes(query) ||
                        tx.amount.toString().includes(query)
                    );
                });
            }
            
            return filtered;
        },
        // 検索・フィルタリング結果に基づいて残高を再計算する
        transactionsWithRecalculatedBalance() {
            const transactions = [...this.filteredTransactions];
            
            if (transactions.length === 0) {
                return [];
            }
            
            // 日付順にソート（古い順）
            transactions.sort((a, b) => {
                const dateA = new Date(a.date);
                const dateB = new Date(b.date);
                return dateA - dateB;
            });
            
            // 残高を0から再計算（検索結果だけの推移として計算）
            let runningBalance = 0;
            const recalculatedTransactions = transactions.map((tx) => {
                // 現在の取引を適用
                const currentAmount = tx.type === 'income' ? tx.amount : -tx.amount;
                runningBalance += currentAmount;
                
                return {
                    ...tx,
                    balance: runningBalance
                };
            });
            
            return recalculatedTransactions;
        },
        currentBalance() {
            const recalculatedTransactions = this.transactionsWithRecalculatedBalance;
            if (recalculatedTransactions.length === 0) {
                return 0;
            }
            // 最新の残高を返す（日付順ソート済みなので最後の要素）
            return recalculatedTransactions[recalculatedTransactions.length - 1].balance;
        },
        sortedTransactions() {
            const transactionsToDisplay = [...this.transactionsWithRecalculatedBalance];
            transactionsToDisplay.sort((a, b) => {
                const dateA = new Date(a.date);
                const dateB = new Date(b.date);
                if (this.dateSortOrder === 'asc') {
                    return dateA - dateB;
                }
                return dateB - dateA;
            });
            return transactionsToDisplay;
        }
    },
    methods: {
        formatCurrency(amount) {
            return '¥' + amount.toLocaleString();
        },
        formatDateTime(dateTimeString) {
            if (!dateTimeString) return '';
            const date = new Date(dateTimeString);
            const year = date.getFullYear();
            const month = ('0' + (date.getMonth() + 1)).slice(-2);
            const day = ('0' + date.getDate()).slice(-2);
            if (dateTimeString.includes(' ') || dateTimeString.includes('T')) {
                const hours = ('0' + date.getHours()).slice(-2);
                const minutes = ('0' + date.getMinutes()).slice(-2);
                return `${year}-${month}-${day} ${hours}:${minutes}`;
            }
            return `${year}-${month}-${day}`;
        },
        getAmountCellClass(type) {
            return type === 'income' ? 'income-cell' : 'expense-cell';
        },
        getAmountInputClass(type) {
            return type === 'income' ? 'amount-input-income' : 'amount-input-expense';
        },
        formatAmount(amount, type) {
            const formattedAmount = amount.toLocaleString();
            return type === 'income' ? `+${formattedAmount}` : `-${formattedAmount}`;
        },
        toggleDateSort() {
            this.dateSortOrder = this.dateSortOrder === 'asc' ? 'desc' : 'asc';
        },
        selectFundItem(fundItem) {
            this.selectedFundItem = fundItem;
            this.showAccountDropdown = false; // 選択したらドロップダウンを閉じる
            this.loadTransactions(); // 資金項目変更時にデータを再読み込み
        },
        toggleAccountDropdown() {
            this.showAccountDropdown = !this.showAccountDropdown;
        },
        positionDropdown() {
            // CSSのposition: absoluteとtop: 100%, left: 0を使用するため、
            // JavaScriptでの位置調整は不要
            // ドロップダウンは自動的に.project-selectorの真下に表示される
        },
        handleClickOutside(event) {
            const projectSelector = document.querySelector('.project-selector');
            if (projectSelector && !projectSelector.contains(event.target)) {
                this.showAccountDropdown = false;
            }
            
            // 資金項目ドロップダウンのクリック外処理
            const fundItemGroup = document.querySelector('.funditem-input-group');
            if (fundItemGroup && !fundItemGroup.contains(event.target)) {
                this.showFundItemDropdown = false;
            }
        },
        async loadTransactions() {
            try {
                this.loading = true;
                // 検索パラメータを構築
                const params = new URLSearchParams();
                // 検索とフィルタリングはフロントエンドで行うため、全データを取得
                if (this.selectedFundItem !== 'すべて') {
                    params.append('account', this.selectedFundItem);  // バックエンドは'account'パラメータを期待
                }
                const url = `/api/transactions${params.toString() ? '?' + params.toString() : ''}`;
                const response = await fetch(url);
                if (!response.ok) {
                    throw new Error('データの取得に失敗しました');
                }
                this.transactions = await response.json();
            } catch (error) {
                console.error('取引データの読み込みエラー:', error);
                alert('データの読み込みに失敗しました。');
            } finally {
                this.loading = false;
            }
        },
        async loadFundItems() {
            try {
                const response = await fetch('/api/accounts');
                if (!response.ok) {
                    throw new Error('資金項目データの取得に失敗しました');
                }
                const fundItems = await response.json();
                // 「すべて」を先頭に追加
                this.fundItemNames = ['すべて', ...fundItems];
            } catch (error) {
                console.error('資金項目データの読み込みエラー:', error);
                alert('資金項目データの読み込みに失敗しました。');
                // エラーの場合はデフォルト値を設定
                this.fundItemNames = ['すべて'];
            }
        },
        async loadItemNames() {
            try {
                const response = await fetch('/api/items');
                if (!response.ok) {
                    throw new Error('項目データの取得に失敗しました');
                }
                const items = await response.json();
                this.itemNames = items;
            } catch (error) {
                console.error('項目データの読み込みエラー:', error);
                this.itemNames = [];
            }
        },
        async backupToCSV() {
            try {
                const response = await fetch('/api/backup_csv');
                if (!response.ok) {
                    throw new Error('バックアップに失敗しました');
                }
                const result = await response.json();
                alert(result.message);
            } catch (error) {
                console.error('CSVバックアップエラー:', error);
                alert('バックアップに失敗しました。');
            }
        },
        onSearchInput() {
            // 検索はフロントエンドで行うため、すぐに結果を更新
            // デバウンスは不要（計算処理が軽いため）
        },
        async showAddModal() {
            // 常に最新の資金項目リストを取得
            await this.loadFundItems();
            const today = new Date();
            this.newTransaction.date = today.toISOString().split('T')[0];
            this.newTransaction.time = today.toTimeString().slice(0, 5);
            // 「すべて」以外の最初の資金項目を初期値に
            const firstFundItem = this.fundItemNames.find(name => name !== 'すべて') || '';
            this.newTransaction.fundItem = firstFundItem;
            this.newTransaction.item = '';
            this.newTransaction.type = 'expense';
            this.newTransaction.amount = '';
            this.showAddTransactionModal = true;
        },
        hideAddModal() {
            this.showAddTransactionModal = false;
            this.showFundItemDropdown = false;  // モーダルを閉じるときにドロップダウンも閉じる
        },
        // 資金項目ドロップダウンの表示/非表示を切り替え
        toggleFundItemDropdown() {
            this.showFundItemDropdown = !this.showFundItemDropdown;
        },
        // 資金項目を選択
        selectFundItemInModal(fundItem) {
            this.newTransaction.fundItem = fundItem;
            this.showFundItemDropdown = false;
        },
        // 資金項目入力フィールドのクリック処理
        onFundItemInputClick() {
            this.showFundItemDropdown = true;
        },
        // 全角数字を半角数字に変換する関数
        convertToHalfWidth(str) {
            return str.replace(/[０-９]/g, function(s) {
                return String.fromCharCode(s.charCodeAt(0) - 0xFEE0);
            });
        },
        // 数字以外の文字を除去する関数
        filterNumericOnly(str) {
            // 全角・半角の数字とカンマのみを許可
            return str.replace(/[^0-9０-９,，]/g, '');
        },
        // 金額欄の入力変換イベント
        onAmountInput(event) {
            let value = event.target.value;
            
            // 数字以外の文字を除去
            value = this.filterNumericOnly(value);
            
            // 全角数字を半角数字に変換
            value = this.convertToHalfWidth(value);
            
            // カンマを除去して純粋な数字のみにする
            const numericValue = value.replace(/[,，]/g, '');
            
            // 値を更新
            this.newTransaction.amount = numericValue;
            
            // 入力欄の値も同期（カーソル位置を保持）
            const cursorPos = event.target.selectionStart;
            event.target.value = numericValue;
            
            // カーソル位置を調整（フィルタリングで文字が削除された場合に対応）
            const newPos = Math.min(cursorPos, numericValue.length);
            setTimeout(() => {
                event.target.setSelectionRange(newPos, newPos);
            }, 0);
        },
        // 金額欄のキーダウンイベント（無効なキーを防ぐ）
        onAmountKeydown(event) {
            const key = event.key;
            const code = event.code;
            
            // 許可するキー
            const allowedKeys = [
                'Backspace', 'Delete', 'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown',
                'Home', 'End', 'Tab', 'Escape', 'Enter'
            ];
            
            // Ctrl/Cmd + キーの組み合わせを許可（コピー、ペースト、全選択など）
            if (event.ctrlKey || event.metaKey) {
                return true;
            }
            
            // 許可されたキーの場合は通す
            if (allowedKeys.includes(key)) {
                return true;
            }
            
            // 半角数字
            if (key >= '0' && key <= '9') {
                return true;
            }
            
            // 全角数字
            if (key >= '０' && key <= '９') {
                return true;
            }
            
            // それ以外のキーは無効
            event.preventDefault();
            return false;
        },
        // 金額欄のペーストイベント
        onAmountPaste(event) {
            event.preventDefault();
            
            // クリップボードからデータを取得
            const pastedData = (event.clipboardData || window.clipboardData).getData('text');
            
            // 数字以外を除去して処理
            const filteredData = this.filterNumericOnly(pastedData);
            const convertedData = this.convertToHalfWidth(filteredData);
            const numericData = convertedData.replace(/[,，]/g, '');
            
            // 現在の入力欄の値と組み合わせる
            const input = event.target;
            const start = input.selectionStart;
            const end = input.selectionEnd;
            const currentValue = this.newTransaction.amount || '';
            
            // 新しい値を作成
            const newValue = currentValue.substring(0, start) + numericData + currentValue.substring(end);
            
            // 値を更新
            this.newTransaction.amount = newValue;
            
            // カーソル位置を調整
            setTimeout(() => {
                const newPos = start + numericData.length;
                input.setSelectionRange(newPos, newPos);
            }, 0);
        },
        // 新しい資金項目かどうかを判定
        isNewFundItem(fundItemName) {
            return fundItemName && !this.fundItemNames.includes(fundItemName);
        },
        isNewItem(itemName) {
            return itemName && !this.itemNames.includes(itemName);
        },
        async addTransaction() {
            try {
                // バリデーション（時刻は除外）
                if (!this.newTransaction.fundItem || !this.newTransaction.date || 
                    !this.newTransaction.item || !this.newTransaction.amount) {
                    alert('日付、資金項目、項目、金額は必須項目です。');
                    return;
                }

                // 金額の変換と検証
                const convertedAmount = this.convertToHalfWidth(this.newTransaction.amount);
                const amount = parseInt(convertedAmount.replace(/[^\d]/g, ''));
                if (isNaN(amount) || amount <= 0) {
                    alert('金額は正の数値を入力してください。');
                    return;
                }

                // 新しい資金項目または項目の場合は確認
                let confirmMessage = '';
                if (this.isNewFundItem(this.newTransaction.fundItem)) {
                    confirmMessage = `「${this.newTransaction.fundItem}」は新しい資金項目です。作成しますか？`;
                } else if (this.isNewItem(this.newTransaction.item)) {
                    confirmMessage = `「${this.newTransaction.item}」は新しい項目です。作成しますか？`;
                }
                if (confirmMessage && !confirm(confirmMessage)) {
                    return;
                }

                // APIに送信するデータを準備
                const transactionData = {
                    account: this.newTransaction.fundItem, // バックエンドのDBフィールドは'account'
                    date: this.newTransaction.date,
                    time: this.newTransaction.time,
                    item: this.newTransaction.item,
                    type: this.newTransaction.type,
                    amount: amount
                };

                const response = await fetch('/api/transactions', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(transactionData)
                });

                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.error || '取引の追加に失敗しました');
                }

                const result = await response.json();
                alert(result.message);
                
                // モーダルを閉じて、データを再読み込み
                this.hideAddModal();
                await this.loadFundItems(); // 新しい資金項目が追加された可能性があるため
                await this.loadTransactions();

            } catch (error) {
                console.error('取引追加エラー:', error);
                alert(`エラー: ${error.message}`);
            }
        }
    },
    mounted() {
        // ドロップダウンの外側をクリックした時に閉じる
        document.addEventListener('click', this.handleClickOutside);
        // アプリ起動時にAPIからデータを読み込む
        this.loadFundItems().then(() => {
            // 資金項目データ読み込み完了後に取引データを読み込む
            this.loadTransactions();
        });
        this.loadItemNames();
    },
    beforeUnmount() {
        // イベントリスナーをクリーンアップ
        document.removeEventListener('click', this.handleClickOutside);
    },
    created() {
        // Vue app created
    }
}).mount('#app');
