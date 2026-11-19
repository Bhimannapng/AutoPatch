package com.bank;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class AccountService {
    private final String accountNumber;
    private double balance;
    private final List<Transaction> transactionHistory;

    public AccountService(String accountNumber, double initialDeposit) {
        if (accountNumber == null || accountNumber.trim().isEmpty()) {
            throw new IllegalArgumentException("Account number is required");
        }
        if (initialDeposit < 0.0) {
            throw new IllegalArgumentException("Initial deposit cannot be negative");
        }
        this.accountNumber = accountNumber;
        this.balance = initialDeposit;
        this.transactionHistory = new ArrayList<>();
    }

    public synchronized void deposit(double amount) {
        if (amount <= 0.0) {
            throw new IllegalArgumentException("Deposit amount must be strictly positive");
        }
        this.balance += amount;
        String txId = "TX-" + System.currentTimeMillis();
        this.transactionHistory.add(new Transaction(txId, amount, "DEPOSIT"));
    }

    public synchronized boolean withdraw(double amount) {
        if (amount <= 0.0) {
            throw new IllegalArgumentException("Withdrawal amount must be strictly positive");
        }
        if (this.balance < amount) {
            return false;
        }
        this.balance -= amount;
        String txId = "TX-" + System.currentTimeMillis();
        this.transactionHistory.add(new Transaction(txId, amount, "WITHDRAWAL"));
        return true;
    }

    public synchronized double getBalance() {
        return this.balance;
    }

    public synchronized List<Transaction> getHistory() {
        return Collections.unmodifiableList(new ArrayList<>(this.transactionHistory));
    }

    public static void main(String[] args) {
        AccountService account = new AccountService("ACC-98214", 500.0);
        account.deposit(250.0);
        boolean success = account.withdraw(100.0);
        System.out.println("Account: " + account.accountNumber);
        System.out.println("Final Balance: $" + account.getBalance());
        System.out.println("Withdrawal Successful: " + success);
    }
}
