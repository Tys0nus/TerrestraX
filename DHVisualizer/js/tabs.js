/**
 * Tab Navigation System & Bottom Panel Control
 * Provides clean, organized UI
 */

export function initializeTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetTab = button.dataset.tab;
            
            // Remove active class from all tabs
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabPanes.forEach(pane => pane.classList.remove('active'));
            
            // Add active class to clicked tab
            button.classList.add('active');
            document.getElementById(`${targetTab}-tab`).classList.add('active');
        });
    });
    
    // Initialize bottom panel toggle
    initializeBottomPanel();
}

/**
 * Initialize bottom panel collapse/expand
 */
function initializeBottomPanel() {
    const toggleBtn = document.getElementById('toggleBottomPanel');
    const bottomPanel = document.getElementById('bottom-panel');
    
    if (toggleBtn && bottomPanel) {
        toggleBtn.addEventListener('click', () => {
            bottomPanel.classList.toggle('collapsed');
            toggleBtn.textContent = bottomPanel.classList.contains('collapsed') ? '▲ Show' : '▼ Hide';
        });
    }
}

/**
 * Switch to a specific tab programmatically
 */
export function switchToTab(tabName) {
    const targetButton = document.querySelector(`.tab-btn[data-tab="${tabName}"]`);
    if (targetButton) {
        targetButton.click();
    }
}

/**
 * Show badge on tab button (e.g., to indicate changes)
 */
export function setTabBadge(tabName, text) {
    const button = document.querySelector(`.tab-btn[data-tab="${tabName}"]`);
    if (button) {
        let badge = button.querySelector('.tab-badge');
        if (!badge) {
            badge = document.createElement('span');
            badge.className = 'tab-badge';
            button.appendChild(badge);
        }
        badge.textContent = text;
        badge.style.display = text ? 'inline-block' : 'none';
    }
}
