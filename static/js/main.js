// Vue.js アプリケーションのロジック

const { createApp } = Vue;

createApp({
    data() {
        return {
            transactions: [],
            fundItemNames: [],
            itemNames: // 項目名リスト
            [],
            selectedFundItem: 'すべて',
            dateSortOrder: 'desc',
            showAccountDropdown: false,
            loading: true,
            searchQuery: '',
            searchTimeout: null,
            showAddTransactionModal: false,
            showFundItemDropdown: false, // 資金項目ドロップダウンの表示状態
            isEditMode: false, // 追加: 編集モードかどうか
            editTransactionId: null, // 追加: 編集中の取引ID
            newTransaction: {
                fundItem: '',
                date: '',
                time: '',
                item: '',
                type: 'expense',
                amount: ''
            },
            showMenu: false, // ハンバーガーメニューの表示状態
            showGraph: false, // グラフモーダルの表示状態
            showRatioModal: false, // 収支比率モーダル表示状態
            showItemizedModal: false, // 項目別収支モーダル表示状態
            ratioChartInstance: null, // 収支比率チャートインスタンス
            incomeItemChartInstance: null, // 収入項目別チャートインスタンス
            expenseItemChartInstance: null, // 支出項目別チャートインスタンス
            graphFundItem: 'すべて', // グラフ用のフィルタ資金項目
            graphDisplayUnit: 'day', // グラフ表示単位: 'day','month','year'
            ratioFundItem: 'すべて', // 収支比率用フィルタ資金項目
            itemizedFundItem: 'すべて', // 項目別収支用フィルタ資金項目
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
                    params.append('account', this.selectedFundItem); // バックエンドは'account'パラメータを期待
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
                const blob = await response.blob();
                const contentDisposition = response.headers.get('Content-Disposition');
                let filename = 'transactions_backup.csv';
                if (contentDisposition && contentDisposition.includes('filename=')) {
                    filename = contentDisposition.split('filename=')[1].split(';')[0].replace(/"/g, '').trim();
                }
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(url);
                this.showMenu = false;
            } catch (error) {
                console.error('CSVバックアップエラー:', error);
                alert('バックアップに失敗しました。');
            }
        },
        async downloadLog() {
            try {
                const response = await fetch('/api/download_log');
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || 'ログファイルのダウンロードに失敗しました');
                }
                const blob = await response.blob();
                const contentDisposition = response.headers.get('Content-Disposition');
                let filename = 'money_tracker.log';
                if (contentDisposition && contentDisposition.includes('filename=')) {
                    filename = contentDisposition.split('filename=')[1].split(';')[0].replace(/"/g, '').trim();
                }
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(url);
                this.showMenu = false;
            } catch (error) {
                console.error('ログファイルダウンロードエラー:', error);
                alert('ログファイルのダウンロードに失敗しました: ' + error.message);
            }
        },
        openRatioModal() {
            this.showMenu = false;
            this.showRatioModal = true;
            this.$nextTick(() => { this.renderRatioChart(); });
        },
        hideRatioModal() { this.showRatioModal = false; if (this.ratioChartInstance) this.ratioChartInstance.destroy(); },
        openItemizedModal() {
            this.showMenu = false;
            this.showItemizedModal = true;
            this.$nextTick(() => { this.renderItemizedCharts(); });
        },
        hideItemizedModal() { this.showItemizedModal = false; if (this.incomeItemChartInstance) this.incomeItemChartInstance.destroy(); if (this.expenseItemChartInstance) this.expenseItemChartInstance.destroy(); },
        async renderRatioChart() {
            // 既存チャートを破棄
            if (this.ratioChartInstance) {
                this.ratioChartInstance.destroy();
                this.ratioChartInstance = null;
            }
            const ctx = document.getElementById('ratioChart').getContext('2d');
            // 全取引を再取得
            let allTxs = [];
            try {
                const res = await fetch('/api/transactions');
                allTxs = await res.json();
            } catch (e) {
                console.error('取引データ取得エラー:', e);
            }
            // 選択中の資金項目でフィルタ
            const filteredTxs = allTxs.filter(t => this.ratioFundItem === 'すべて' || ((t.fundItem || t.account) === this.ratioFundItem));
            const totalIncome = filteredTxs.filter(t => t.type === 'income').reduce((sum, t) => sum + t.amount, 0);
            const totalExpense = filteredTxs.filter(t => t.type === 'expense').reduce((sum, t) => sum + t.amount, 0);
            const data = {
                labels: ['収入','支出'],
                datasets: [{ data:[totalIncome,totalExpense], backgroundColor:['#4caf50','#f44336'] }]
            };
            this.ratioChartInstance = new Chart(ctx, { type:'pie', data });
        },
        async renderItemizedCharts() {
            // destroy existing
            if (this.incomeItemChartInstance) { this.incomeItemChartInstance.destroy(); this.incomeItemChartInstance = null; }
            if (this.expenseItemChartInstance) { this.expenseItemChartInstance.destroy(); this.expenseItemChartInstance = null; }
            // fetch fresh transactions
            let allTxs = [];
            try {
                const res = await fetch('/api/transactions'); allTxs = await res.json();
            } catch (e) { console.error('取引データ取得エラー:', e); }
            // filter by selected fund item
            const filtered = allTxs.filter(t => this.itemizedFundItem === 'すべて' || ((t.fundItem||t.account) === this.itemizedFundItem));
            // aggregate by item
            const incomeItems = {}, expenseItems = {};
            filtered.forEach(t => {
                const key = t.item || '未指定';
                if (t.type==='income') incomeItems[key] = (incomeItems[key]||0) + t.amount;
                else expenseItems[key] = (expenseItems[key]||0) + t.amount;
            });
            // sort entries by descending value
            const inEntries = Object.entries(incomeItems).sort((a,b) => b[1] - a[1]);
            const exEntries = Object.entries(expenseItems).sort((a,b) => b[1] - a[1]);
            const inLabels = inEntries.map(([key]) => key);
            const inData = inEntries.map(([_, val]) => val);
            const exLabels = exEntries.map(([key]) => key);
            const exData = exEntries.map(([_, val]) => val);
            // draw charts without legend
            const ctxIn = document.getElementById('incomeItemChart').getContext('2d');
            this.incomeItemChartInstance = new Chart(ctxIn, {
                type:'doughnut', data:{ labels:inLabels, datasets:[{ data:inData, backgroundColor:inLabels.map((_,i)=>`hsl(${i*40%360},70%,50%)`)}]},
                options:{ plugins:{ legend:{ display:false } } }
            });
            const ctxEx = document.getElementById('expenseItemChart').getContext('2d');
            this.expenseItemChartInstance = new Chart(ctxEx, {
                type:'doughnut', data:{ labels:exLabels, datasets:[{ data:exData, backgroundColor:exLabels.map((_,i)=>`hsl(${i*40%360},70%,50%)`)}]},
                options:{ plugins:{ legend:{ display:false } } }
            });
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
        async onEditTransaction(transaction) {
            // 編集用にモーダルを開く
            await this.loadFundItems();
            this.isEditMode = true;
            this.editTransactionId = transaction.id;
            // 日付・時刻分割
            let date = '', time = '';
            if (transaction.date.includes(' ')) {
                [date, time] = transaction.date.split(' ');
                time = time.slice(0,5); // HH:MM
            } else {
                date = transaction.date;
                time = '';
            }
            this.newTransaction = {
                fundItem: transaction.fundItem || transaction.account,
                date: date,
                time: time,
                item: transaction.item,
                type: transaction.type,
                amount: transaction.amount.toString()
            };
            this.showAddTransactionModal = true;
        },
        hideAddModal() {
            this.showAddTransactionModal = false;
            this.showFundItemDropdown = false;
            this.isEditMode = false;
            this.editTransactionId = null;
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
            let pastedData = '';
            if (event.clipboardData) {
                pastedData = event.clipboardData.getData('text');
            } else if (window.clipboardData) {
                // IE対応（型エラーを避けるためtry-catchで囲む）
                try {
                    pastedData = window.clipboardData.getData('text');
                } catch (e) {
                    pastedData = '';
                }
            }

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
        },
        async addOrUpdateTransaction() {
            // 追加・編集を分岐
            if (this.isEditMode) {
                await this.updateTransaction();
            } else {
                await this.addTransaction();
            }
        },
        async updateTransaction() {
            try {
                if (!this.newTransaction.fundItem || !this.newTransaction.date ||
                    !this.newTransaction.item || !this.newTransaction.amount) {
                    alert('日付、資金項目、項目、金額は必須項目です。');
                    return;
                }
                const convertedAmount = this.convertToHalfWidth(this.newTransaction.amount);
                const amount = parseInt(convertedAmount.replace(/[^\d]/g, ''));
                if (isNaN(amount) || amount <= 0) {
                    alert('金額は正の数値を入力してください。');
                    return;
                }
                const transactionData = {
                    account: this.newTransaction.fundItem,
                    date: this.newTransaction.date,
                    time: this.newTransaction.time,
                    item: this.newTransaction.item,
                    type: this.newTransaction.type,
                    amount: amount
                };
                const response = await fetch(`/api/transactions/${this.editTransactionId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(transactionData)
                });
                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.error || '取引の編集に失敗しました');
                }
                const result = await response.json();
                alert(result.message);
                this.hideAddModal();
                await this.loadFundItems();
                await this.loadTransactions();
            } catch (error) {
                console.error('取引編集エラー:', error);
                alert(`エラー: ${error.message}`);
            }
        },
        async onDeleteTransaction() {
            if (!this.isEditMode || !this.editTransactionId) return;
            if (!confirm('本当にこの取引を削除しますか？')) return;
            try {
                const response = await fetch(`/api/transactions/${this.editTransactionId}`, {
                    method: 'DELETE'
                });
                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.error || '削除に失敗しました');
                }
                const result = await response.json();
                alert(result.message);
                this.hideAddModal();
                await this.loadFundItems();
                await this.loadTransactions();
            } catch (error) {
                console.error('取引削除エラー:', error);
                alert(`エラー: ${error.message}`);
            }
        },
        toggleMenu() {
            this.showMenu = !this.showMenu;
        },
        showGraphModal() {
            this.showGraph = true;
            this.showMenu = false;
            this.$nextTick(() => {
                this.renderBalanceChart();
            });
        },
        hideGraphModal() {
            this.showGraph = false;
        },
        async logout() {
            if (!confirm('ログアウトしますか？')) {
                return;
            }
            
            try {
                const response = await fetch('/api/logout', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                const data = await response.json();
                
                if (response.ok && data.success) {
                    // ログアウト成功 - ログイン画面にリダイレクト
                    window.location.href = '/login';
                } else {
                    alert('ログアウトに失敗しました');
                }
            } catch (error) {
                console.error('Logout error:', error);
                alert('ネットワークエラーが発生しました');
            }
        },
        renderBalanceChart() {
            // 既存のグラフがあれば破棄
            if (this._balanceChartInstance) {
                this._balanceChartInstance.destroy();
            }
            // グラフの親要素サイズにcanvasを合わせる
            const wrapper = document.querySelector('.graph-scroll-wrapper');
            const canvas = document.getElementById('balanceChart');
            if (wrapper && canvas) {
                // スクロールバー分を考慮して少し余裕を持たせる
                const w = Math.max(wrapper.clientWidth - 15, 800); // 最小幅を800pxに維持、余白を減らす
                const h = Math.max(wrapper.clientHeight - 15, 350); // 最小高さを350pxに拡大、余白を減らす
                canvas.width = w;
                canvas.height = h;
                canvas.style.width = w + 'px';
                canvas.style.height = h + 'px';
            }
            // 資金項目フィルタリングと残高再計算
            let txsRaw;
            if (this.graphFundItem && this.graphFundItem !== 'すべて') {
                txsRaw = this.transactions.filter(tx => (tx.fundItem || tx.account) === this.graphFundItem);
            } else {
                txsRaw = [...this.transactions];
            }
            // 日付順にソート（古い順）
            txsRaw.sort((a, b) => new Date(a.date) - new Date(b.date));
            // 残高を再計算
            let runBal = 0;
            const txs = txsRaw.map(tx => {
                runBal += (tx.type === 'income' ? tx.amount : -tx.amount);
                return { ...tx, balance: runBal };
            });
            // データを表示単位で集計
            const grouped = {};
            txs.forEach(tx => {
                const d = new Date(tx.date);
                let key;
                if (this.graphDisplayUnit === 'month') {
                    key = `${d.getFullYear()}-${('0'+(d.getMonth()+1)).slice(-2)}`;
                } else if (this.graphDisplayUnit === 'year') {
                    key = `${d.getFullYear()}`;
                } else {
                    key = `${d.getFullYear()}-${('0'+(d.getMonth()+1)).slice(-2)}-${('0'+d.getDate()).slice(-2)}`;
                }
                // 同じキーの場合は最新バランスを上書き
                grouped[key] = tx.balance;
            });
            const labels = Object.keys(grouped);
            const data = labels.map(label => grouped[label]);
             const ctx = canvas.getContext('2d');
             this._balanceChartInstance = new Chart(ctx, {
                 type: 'line',
                 data: {
                     labels: labels,
                     datasets: [{
                         label: '残高',
                         data: data,
                         borderColor: 'rgba(54, 162, 235, 1)',
                         backgroundColor: 'rgba(54, 162, 235, 0.1)',
                         fill: true,
                         tension: 0.2,
                         pointRadius: 2
                     }]
                 },
                 options: {
                     responsive: false,
                     maintainAspectRatio: false,
                     plugins: {
                         legend: { display: false },
                         title: { display: false }
                     },
                     scales: {
                         x: { 
                             title: { display: true, text: this.graphDisplayUnit==='month' ? '年月' : this.graphDisplayUnit==='year' ? '年' : '日付' },
                             grid: { display: true }
                         },
                         y: { 
                             title: { display: true, text: '残高(円)' }, 
                             beginAtZero: true,
                             grid: { display: true }
                         }
                     },
                     interaction: {
                         intersect: false,
                         mode: 'index'
                     }
                 }
             });
        },
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
