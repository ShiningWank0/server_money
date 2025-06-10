// Vue.js アプリケーションのロジック

const { createApp } = Vue;

createApp({
    data() {
        return {
            transactions: [
                // デモデータに口座情報を追加し、データを拡充
                { id: 1, account: 'メイン口座', date: '2025-06-10 09:00:00', item: '給与', type: 'income', amount: 300000, balance: 0 },
                { id: 2, account: 'メイン口座', date: '2025-06-09', item: '家賃', type: 'expense', amount: 80000, balance: 0 },
                { id: 3, account: 'メイン口座', date: '2025-06-08 14:15:00', item: 'スーパーマーケット', type: 'expense', amount: 5500, balance: 0 },
                { id: 4, account: 'メイン口座', date: '2025-06-07', item: '書籍購入', type: 'expense', amount: 2400, balance: 0 },
                { id: 5, account: 'メイン口座', date: '2025-06-05 10:00:00', item: 'フリマ売上', type: 'income', amount: 3000, balance: 0 },
                { id: 6, account: 'メイン口座', date: '2025-06-04', item: '通信費', type: 'expense', amount: 6000, balance: 0 },
                { id: 7, account: 'メイン口座', date: '2025-06-03 18:30:00', item: '外食', type: 'expense', amount: 1800, balance: 0 },

                { id: 8, account: 'クレジットカード', date: '2025-06-10 10:00:00', item: 'オンラインショッピング', type: 'expense', amount: 12000, balance: 0 },
                { id: 9, account: 'クレジットカード', date: '2025-06-08', item: 'カフェ', type: 'expense', amount: 800, balance: 0 },
                { id: 10, account: 'クレジットカード', date: '2025-06-05 20:00:00', item: '映画', type: 'expense', amount: 1900, balance: 0 },

                { id: 11, account: '予備費', date: '2025-06-01', item: '初期資金', type: 'income', amount: 50000, balance: 0 },
                { id: 12, account: '予備費', date: '2025-06-06', item: '友人への貸付', type: 'expense', amount: 5000, balance: 0 },
            ],
            accountNames: ['メイン口座', 'クレジットカード', '予備費'],
            selectedAccount: 'メイン口座', // 初期選択口座
            dateSortOrder: 'desc',
            showAccountDropdown: false // 口座選択ドロップダウンの表示状態
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
        }
    },
    mounted() {
        // ドロップダウンの外側をクリックした時に閉じる
        document.addEventListener('click', this.handleClickOutside);
    },
    beforeUnmount() {
        // イベントリスナーをクリーンアップ
        document.removeEventListener('click', this.handleClickOutside);
    },
    created() {
        console.log('Vue app created, initial transactions:', this.transactions);
        console.log('Account names:', this.accountNames);
        console.log('Selected account:', this.selectedAccount);
        
        // 各口座ごとに残高を計算
        const allTransactions = [];
        this.accountNames.forEach(account => {
            let runningBalance = 0;
            const accountTransactions = this.transactions
                .filter(tx => tx.account === account)
                .sort((a, b) => { // 日付と時刻でソートして正しい順序で残高計算
                    const dateA = new Date(a.date);
                    const dateB = new Date(b.date);
                    return dateA - dateB;
                })
                .map(tx => {
                    if (tx.type === 'income') {
                        runningBalance += tx.amount;
                    } else {
                        runningBalance -= tx.amount;
                    }
                    return { ...tx, balance: runningBalance };
                });
            allTransactions.push(...accountTransactions);
        });
        // 元のtransactions配列を、残高計算済みのものに置き換える
        // ただし、この方法だと元のid順と変わってしまう可能性があるため、
        // 本来はidをキーにしたオブジェクトなどで管理するか、
        // mapで更新する際に元の配列の要素を直接更新する方が良いが、簡略化のためこうする
        this.transactions = allTransactions.sort((a,b) => a.id - b.id);
        
        console.log('Final transactions with balance:', this.transactions);
        console.log('Filtered transactions for selected account:', this.filteredTransactionsByAccount);
    }
}).mount('#app');
