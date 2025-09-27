using System;
using System.Globalization;
using System.Windows.Forms;

namespace SalesTransactionSystem
{
    public partial class MainForm : Form
    {
        public MainForm()
        {
            InitializeComponent();
        }

        private void btnAddItem_Click(object sender, EventArgs e)
        {
            if (!ValidateInputs(out string itemName, out int quantity, out decimal price))
                return;

            decimal amount = quantity * price;
            dataGridView1.Rows.Add(itemName, quantity, price.ToString("N2"), amount.ToString("N2"));
            ClearInputs();
            UpdateTotal();
        }

        private void btnDeleteSelected_Click(object sender, EventArgs e)
        {
            foreach (DataGridViewRow row in dataGridView1.SelectedRows)
            {
                if (!row.IsNewRow)
                    dataGridView1.Rows.Remove(row);
            }
            UpdateTotal();
        }

        private bool ValidateInputs(out string itemName, out int quantity, out decimal price)
        {
            itemName = txtItemName.Text.Trim();
            if (string.IsNullOrWhiteSpace(itemName))
            {
                MessageBox.Show("Item Name is required.", "Validation", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                quantity = 0; price = 0;
                return false;
            }

            if (!int.TryParse(txtQuantity.Text.Trim(), NumberStyles.Integer, CultureInfo.InvariantCulture, out quantity) || quantity <= 0)
            {
                MessageBox.Show("Quantity must be a positive integer.", "Validation", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                price = 0;
                return false;
            }

            if (!decimal.TryParse(txtPrice.Text.Trim(), NumberStyles.Number, CultureInfo.InvariantCulture, out price) || price < 0)
            {
                MessageBox.Show("Price must be a non-negative decimal.", "Validation", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return false;
            }

            return true;
        }

        private void ClearInputs()
        {
            txtItemName.Clear();
            txtQuantity.Clear();
            txtPrice.Clear();
            txtItemName.Focus();
        }

        private void dataGridView1_CellEndEdit(object sender, DataGridViewCellEventArgs e)
        {
            RecomputeRowAmount(e.RowIndex);
            UpdateTotal();
        }

        private void dataGridView1_CellValueChanged(object sender, DataGridViewCellEventArgs e)
        {
            if (e.RowIndex >= 0) RecomputeRowAmount(e.RowIndex);
            UpdateTotal();
        }

        private void dataGridView1_RowsRemoved(object sender, DataGridViewRowsRemovedEventArgs e)
        {
            UpdateTotal();
        }

        private void dataGridView1_UserDeletedRow(object sender, DataGridViewRowEventArgs e)
        {
            UpdateTotal();
        }

        private void RecomputeRowAmount(int rowIndex)
        {
            if (rowIndex < 0 || rowIndex >= dataGridView1.Rows.Count) return;
            var row = dataGridView1.Rows[rowIndex];
            if (row.IsNewRow) return;

            if (TryGetDecimal(row.Cells["Price"]?.Value, out decimal price) &&
                TryGetInt(row.Cells["Quantity"]?.Value, out int qty))
            {
                row.Cells["Amount"].Value = (qty * price).ToString("N2");
            }
        }

        private static bool TryGetInt(object value, out int result)
        {
            result = 0;
            if (value == null) return false;
            return int.TryParse(Convert.ToString(value)?.Trim(), out result);
        }

        private static bool TryGetDecimal(object value, out decimal result)
        {
            result = 0;
            if (value == null) return false;
            return decimal.TryParse(Convert.ToString(value)?.Trim(), NumberStyles.Number, CultureInfo.InvariantCulture, out result);
        }

        private void UpdateTotal()
        {
            decimal total = 0m;
            foreach (DataGridViewRow row in dataGridView1.Rows)
            {
                if (row.IsNewRow) continue;
                if (row.Cells["Amount"].Value != null &&
                    decimal.TryParse(Convert.ToString(row.Cells["Amount"].Value), NumberStyles.Number, CultureInfo.InvariantCulture, out decimal amt))
                {
                    total += amt;
                }
            }
            lblTotal.Text = "Total: " + total.ToString("N2");
        }
    }
}


