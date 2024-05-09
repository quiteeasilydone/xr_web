// Function to add an item
function addItem() {
    const container = document.getElementById('itemsContainer');
    const itemNumber = container.children.length + 1;
    container.innerHTML += `
      <div class="item">
        <label>Description of Item ${itemNumber}:</label>
        <textarea required></textarea>
        
        <label>Multiple Choices:</label>
        <select>
          <option value="">Please select</option>
          <option value="option1">Option 1</option>
          <option value="option2">Option 2</option>
          <!-- Add more options as needed -->
        </select>
        
        <label>Numerical Input:</label>
        <input type="number" required>
        
        <label>Yes/No:</label>
        <select>
          <option value="">Please select</option>
          <option value="yes">Yes</option>
          <option value="no">No</option>
        </select>
        
        <label>Upload Photo:</label>
        <input type="file" accept="image/*">
        
        <span class="remove-item" onclick="removeItem(this)">Remove Item</span>
      </div>
    `;
  }
  
  // Function to remove an item
  function removeItem(element) {
    const item = element.parentNode;
    item.remove();
  }
  
  // Add initial item
  document.addEventListener('DOMContentLoaded', (event) => {
      addItem();
  });
  