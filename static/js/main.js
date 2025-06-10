// Vue.js アプリケーションのロジック

const { createApp } = Vue;

createApp({
    data() {
        return {
            transactions: [], // APIから取得するため、初期値は空配列
            accountNames: ['メイン口座', 'クレジットカード', '予備費'],
            selectedAccount: 'メイン口座', // 初期選択口座
            dateSortOrder: 'desc',
            showAccountDropdown: false, // 口座選択ドロップダウンの表示状態
            loading: true // データロード中のフラグ
        }
    },
    computed: {
        filteredTransactionsByAccount() {
            return this.transactions.filter(tx => tx.account === this.selectedAccount);
        },
        currentBalance() {
            const accountTransactions = this.filteredTransactionsByAccount;
            if (accountTransactions.length === 0) {
                return 0;
            }
            const sortedForBalance = [...accountTransactions].sort((a, b) => {
                const dateA = new Date(a.date.split(' ')[0]); // 日付部分のみで比較
                const dateB = new Date(b.date.split(' ')[0]);
                if (dateA - dateB !== 0) {
                    return dateA - dateB;
                }
                 // 同じ日付の場合はIDでソートして安定性を確保 (時刻を考慮しない場合)
                // もし時刻まで厳密に考慮してその日の最終残高とするなら、date全体でソート
                const fullDateA = new Date(a.date);
                const fullDateB = new Date(b.date);
                return fullDateA - fullDateB; 
            });
            return sortedForBalance[sortedForBalance.length - 1].balance;
        },
        sortedTransactions() {
            const transactionsToDisplay = [...this.filteredTransactionsByAccount];
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
        formatAmount(amount, type) {
            const formattedAmount = amount.toLocaleString();
            return type === 'income' ? `+${formattedAmount}` : `-${formattedAmount}`;
        },
        toggleDateSort() {
            this.dateSortOrder = this.dateSortOrder === 'asc' ? 'desc' : 'asc';
        },
        selectAccount(account) {
            this.selectedAccount = account;
            this.showAccountDropdown = false; // 選択したらドロップダウンを閉じる
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
        },
        async loadTransactions() {
            try {
                this.loading = true;
                const response = await fetch('/api/transactions');
                if (!response.ok) {
                    throw new Error('データの取得に失敗しました');
                }
                this.transactions = await response.json();
                console.log('Loaded transactions from API:', this.transactions);
            } catch (error) {
                console.error('取引データの読み込みエラー:', error);
                alert('データの読み込みに失敗しました。');
            } finally {
                this.loading = false;
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
        }
    },
    mounted() {
        // ドロップダウンの外側をクリックした時に閉じる
        document.addEventListener('click', this.handleClickOutside);
        // アプリ起動時にAPIからデータを読み込む
        this.loadTransactions();
    },
    beforeUnmount() {
        // イベントリスナーをクリーンアップ
        document.removeEventListener('click', this.handleClickOutside);
    },
    created() {
        console.log('Vue app created');
        console.log('Account names:', this.accountNames);
        console.log('Selected account:', this.selectedAccount);
    }
}).mount('#app');
