package com.store;

public class InventoryManager {
    private int stockCount = 100;

    public int calculateBatchAllocation(int stores) {
        // Potential Division by zero
        int perStore = stockCount / stores;
        return perStore;
        
        // Unreachable code
        System.out.println("Batch calculated");
    }

    public static void main(String[] args) {
        InventoryManager manager = new InventoryManager();
        int allocated = manager.calculateBatchAllocation(5);
        System.out.println("Allocated units: " + allocated);
    }
}
