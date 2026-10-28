// ========================================================
// HOSTEL BITES - ADMIN JS
// ========================================================

// Open Add Food Item Modal
function openAddModal() {
  const modal = document.getElementById("addFoodModal");
  if (modal) modal.style.display = "flex";
}

function closeAddModal() {
  const modal = document.getElementById("addFoodModal");
  if (modal) modal.style.display = "none";
}

// Open Edit Food Item Modal with prefilled values
function openEditModal(item) {
  const modal = document.getElementById("editFoodModal");
  if (!modal) return;

  document.getElementById("edit-form").action = `/admin/menu/${item.id}/edit`;
  document.getElementById("edit-name").value = item.name;
  document.getElementById("edit-category").value = item.category;
  document.getElementById("edit-price").value = item.price;
  document.getElementById("edit-desc").value = item.description || "";
  document.getElementById("edit-veg").value = item.is_veg ? "1" : "0";
  document.getElementById("edit-prep").value = item.prep_time || "15 min";
  document.getElementById("edit-img").value = item.image_url || "";

  modal.style.display = "flex";
}

function closeEditModal() {
  const modal = document.getElementById("editFoodModal");
  if (modal) modal.style.display = "none";
}

// Live Search in Admin Orders / Table
function filterAdminTable(inputId, tableId) {
  const input = document.getElementById(inputId);
  const filter = input.value.toLowerCase();
  const table = document.getElementById(tableId);
  if (!table) return;
  const rows = table.getElementsByTagName("tr");

  for (let i = 1; i < rows.length; i++) {
    const text = rows[i].textContent.toLowerCase();
    if (text.includes(filter)) {
      rows[i].style.display = "";
    } else {
      rows[i].style.display = "none";
    }
  }
}
