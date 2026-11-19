package com.bank;

import java.time.Instant;

public class Transaction {
    private final String transactionId;
    private final double amount;
    private final String type;
    private final Instant timestamp;

    public Transaction(String transactionId, double amount, String type) {
        if (transactionId == null || transactionId.trim().isEmpty()) {
            throw new IllegalArgumentException("Transaction ID cannot be null or empty");
        }
        if (amount <= 0.0) {
            throw new IllegalArgumentException("Transaction amount must be positive");
        }
        this.transactionId = transactionId;
        this.amount = amount;
        this.type = type != null ? type : "TRANSFER";
        this.timestamp = Instant.now();
    }

    public String getTransactionId() { return transactionId; }
    public double getAmount() { return amount; }
    public String getType() { return type; }
    public Instant getTimestamp() { return timestamp; }
}
