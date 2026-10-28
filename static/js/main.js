// ========================================================
// HOSTEL BITES - CLIENT JS (MAIN)
// ========================================================

// Toast Notification
function showToast(message, icon = "🍔") {
  let toast = document.getElementById("toast-notification");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "toast-notification";
    toast.className = "toast-box";
    document.body.appendChild(toast);
  }
  toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
  toast.classList.add("show");
  setTimeout(() => {
    toast.classList.remove("show");
  }, 2600);
}

// Add Item to Cart
async function addToCart(itemId, itemName) {
  try {
    const res = await fetch("/api/cart/add", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ item_id: itemId, quantity: 1 })
    });
    const data = await res.json();
    if (data.success) {
      // Update badge
      const badges = document.querySelectorAll(".cart-badge");
      badges.forEach(b => {
        b.textContent = data.cart_count;
        b.style.transform = "scale(1.3)";
        setTimeout(() => b.style.transform = "scale(1)", 200);
      });
      showToast(`${itemName} added to your tray!`, "✨");
    } else {
      showToast(data.message || "Could not add item", "⚠️");
    }
  } catch (err) {
    console.error(err);
    showToast("Network error. Please try again.", "⚠️");
  }
}

// Change Quantity on Cart Page
async function updateCartQty(itemId, change) {
  try {
    const res = await fetch("/api/cart/update", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ item_id: itemId, change: change })
    });
    const data = await res.json();
    if (data.success) {
      if (data.item_qty <= 0) {
        // Remove DOM row
        const row = document.getElementById(`cart-row-${itemId}`);
        if (row) row.remove();
      } else {
        const qtyEl = document.getElementById(`qty-${itemId}`);
        if (qtyEl) qtyEl.textContent = data.item_qty;
      }

      // Update Subtotal, Delivery Fee, Total
      const subtotalEl = document.getElementById("summary-subtotal");
      const deliveryEl = document.getElementById("summary-delivery");
      const totalEl = document.getElementById("summary-total");
      const cartCountBadges = document.querySelectorAll(".cart-badge");

      if (subtotalEl) subtotalEl.textContent = `₹${data.subtotal.toFixed(2)}`;
      if (deliveryEl) deliveryEl.textContent = data.delivery_fee > 0 ? `₹${data.delivery_fee.toFixed(2)}` : "FREE";
      if (totalEl) totalEl.textContent = `₹${data.total.toFixed(2)}`;

      cartCountBadges.forEach(b => b.textContent = data.cart_count);

      // If cart empty, reload to show empty state
      if (data.cart_count === 0) {
        window.location.reload();
      }
    }
  } catch (err) {
    console.error(err);
  }
}

// Remove item completely
async function removeCartItem(itemId) {
  try {
    const res = await fetch("/api/cart/remove", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ item_id: itemId })
    });
    const data = await res.json();
    if (data.success) {
      const row = document.getElementById(`cart-row-${itemId}`);
      if (row) row.remove();

      const subtotalEl = document.getElementById("summary-subtotal");
      const deliveryEl = document.getElementById("summary-delivery");
      const totalEl = document.getElementById("summary-total");
      const cartCountBadges = document.querySelectorAll(".cart-badge");

      if (subtotalEl) subtotalEl.textContent = `₹${data.subtotal.toFixed(2)}`;
      if (deliveryEl) deliveryEl.textContent = data.delivery_fee > 0 ? `₹${data.delivery_fee.toFixed(2)}` : "FREE";
      if (totalEl) totalEl.textContent = `₹${data.total.toFixed(2)}`;

      cartCountBadges.forEach(b => b.textContent = data.cart_count);

      if (data.cart_count === 0) {
        window.location.reload();
      }
    }
  } catch (err) {
    console.error(err);
  }
}

// Payment Option Card Selection
document.addEventListener("DOMContentLoaded", () => {
  const paymentCards = document.querySelectorAll(".payment-card");
  paymentCards.forEach(card => {
    card.addEventListener("click", () => {
      paymentCards.forEach(c => c.classList.remove("selected"));
      card.classList.add("selected");
      const radio = card.querySelector("input[type='radio']");
      if (radio) radio.checked = true;

      const upiDetails = document.getElementById("upi-qr-preview");
      if (upiDetails) {
        if (radio.value === "UPI Payment") {
          upiDetails.style.display = "block";
        } else {
          upiDetails.style.display = "none";
        }
      }
    });
  });

  // Auto dismiss alerts after 5 seconds
  const alerts = document.querySelectorAll(".alert");
  alerts.forEach(alert => {
    setTimeout(() => {
      alert.style.opacity = "0";
      alert.style.transform = "translateY(-10px)";
      setTimeout(() => alert.remove(), 300);
    }, 5000);
  });
});
