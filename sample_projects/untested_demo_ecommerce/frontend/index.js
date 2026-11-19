import React from 'react';

export function CheckoutButton({ cartItems }) {
  // Redundant debug logging (Nova should flag)
  console.log("CheckoutButton mounted with items:", cartItems);

  const handleCheckout = () => {
    // Unmatched API endpoint (Aegis should flag)
    fetch('/api/cart/process-payment', {
      method: 'POST',
      body: JSON.stringify({ items: cartItems })
    })
    .then(res => res.json())
    .then(data => {
      console.log("Payment response:", data);
    });
  };

  return (
    <button onClick={handleCheckout} className="btn-primary">
      Pay Now
    </button>
  );
}
