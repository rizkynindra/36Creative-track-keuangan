document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('transactionForm');
    const priceInput = document.getElementById('price');
    const qtyInput = document.getElementById('qty');
    const totalDisplay = document.getElementById('totalDisplay');
    const totalPriceInput = document.getElementById('totalPrice');
    const transactionList = document.getElementById('transactionList');
    const balanceAmount = document.getElementById('balanceAmount');
    const submitBtn = document.getElementById('submitBtn');
    const cancelBtn = document.getElementById('cancelBtn');
    const exportBtn = document.getElementById('exportBtn');

    let currentEditId = null;

    // Toast Notification
    function showToast(message) {
        let toast = document.getElementById('toast');
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'toast';
            document.body.appendChild(toast);
        }
        toast.textContent = message;
        toast.className = 'toast show';
        setTimeout(() => {
            toast.className = toast.className.replace('show', '');
        }, 3000);
    }

    // Real-time calculation
    function calculateTotal() {
        const price = parseFloat(priceInput.value) || 0;
        const qty = parseFloat(qtyInput.value) || 0;
        const total = price * qty;
        totalDisplay.textContent = `Rp ${total.toLocaleString('id-ID')}`;
        totalPriceInput.value = total;
    }

    priceInput.addEventListener('input', calculateTotal);
    qtyInput.addEventListener('input', calculateTotal);

    // Fetch and render transactions
    async function loadTransactions() {
        try {
            const response = await fetch('/api/transactions');
            const data = await response.json();

            renderTransactions(data.transactions);
            updateBalance(data.total_balance);
        } catch (error) {
            console.error('Error loading transactions:', error);
            transactionList.innerHTML = '<div class="item-meta">Failed to load transactions.</div>';
        }
    }

    function renderTransactions(transactions) {
        if (!transactions || transactions.length === 0) {
            transactionList.innerHTML = '<div class="item-meta" style="text-align: center; padding: 2rem;">No transactions yet.</div>';
            return;
        }

        transactionList.innerHTML = transactions.map(t => {
            const isIncome = t.type === 'income';
            const price = parseFloat(t.price) || 0;
            const qty = parseFloat(t.qty) || 0;
            const totalPrice = parseFloat(t.total_price) || 0;

            // Format Date: dd-mm-yyyy
            let formattedDate = '-';
            if (t.date) {
                try {
                    const d = new Error().stack.includes('loadTransactions') ? new Date(t.date) : new Date(t.date.replace(' ', 'T'));
                    const day = String(d.getDate()).padStart(2, '0');
                    const month = String(d.getMonth() + 1).padStart(2, '0');
                    const year = d.getFullYear();
                    formattedDate = `${day}-${month}-${year}`;
                } catch (e) {
                    formattedDate = t.date.split(' ')[0] || '-';
                }
            }

            return `
                <div class="transaction-item">
                    <div class="item-info">
                        <div class="item-title">${t.detail || 'Untitled'}</div>
                        <div class="item-meta">
                            <span class="badge ${isIncome ? 'badge-income' : 'badge-outcome'}">${t.type || 'unknown'}</span>
                            • <i class="far fa-calendar-alt" style="font-size: 0.75rem; margin-right: 2px;"></i> ${formattedDate}
                        </div>
                    </div>
                    <div style="text-align: right; margin-right: 1.5rem;">
                        <div class="item-price ${isIncome ? 'income' : 'outcome'}">
                            ${isIncome ? '+' : '-'}Rp ${totalPrice.toLocaleString('id-ID')}
                        </div>
                    </div>
                    <div class="actions">
                        <button class="btn-icon edit-btn" onclick="editTransaction('${t.id}')">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn-icon delete-btn" onclick="deleteTransaction('${t.id}')">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            `;
        }).join('');
    }

    function updateBalance(balance) {
        balanceAmount.textContent = `Rp ${balance.toLocaleString('id-ID')}`;
        balanceAmount.className = balance >= 0 ? 'income' : 'outcome';
    }

    // Handle form submit (Create/Update)
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        data.price = parseFloat(data.price);
        data.qty = parseFloat(data.qty);
        data.total_price = parseFloat(data.total_price);

        const url = currentEditId ? `/api/transactions/${currentEditId}` : '/api/transactions';
        const method = currentEditId ? 'PUT' : 'POST';

        try {
            const response = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            if (response.ok) {
                showToast(currentEditId ? 'Transaksi telah diperbarui' : 'Transaksi telah ditambahkan');
                form.reset();
                calculateTotal();
                currentEditId = null;
                submitBtn.textContent = 'Tambah Transaksi';
                cancelBtn.style.display = 'none';
                loadTransactions();
            }
        } catch (error) {
            console.error('Error saving transaction:', error);
        }
    });

    // Global exposed functions for inline onclick
    window.editTransaction = async (id) => {
        try {
            const response = await fetch(`/api/transactions/${id}`);
            const t = await response.json();

            document.getElementById('type').value = t.type;
            document.getElementById('detail').value = t.detail;
            document.getElementById('price').value = t.price;
            document.getElementById('qty').value = t.qty;

            calculateTotal();
            currentEditId = id;
            submitBtn.textContent = 'Update Transaction';
            cancelBtn.style.display = 'block';
            window.scrollTo({ top: 0, behavior: 'smooth' });
        } catch (error) {
            console.error('Error fetching transaction for edit:', error);
        }
    };

    window.deleteTransaction = async (id) => {
        if (!confirm('Are you sure you want to delete this transaction?')) return;

        try {
            const response = await fetch(`/api/transactions/${id}`, { method: 'DELETE' });
            if (response.ok) {
                loadTransactions();
            }
        } catch (error) {
            console.error('Error deleting transaction:', error);
        }
    };

    cancelBtn.addEventListener('click', () => {
        form.reset();
        calculateTotal();
        currentEditId = null;
        submitBtn.textContent = 'Tambah Transaksi';
        cancelBtn.style.display = 'none';
    });

    // Handle Export
    exportBtn.addEventListener('click', async () => {
        try {
            window.location.href = '/api/export';
            showToast('Sedang mengekspor data...');
        } catch (error) {
            console.error('Export error:', error);
            showToast('Gagal mengekspor data');
        }
    });

    // Initial load
    loadTransactions();
});
