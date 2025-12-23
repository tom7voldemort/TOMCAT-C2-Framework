// TOMCAT C2 - Navigation & Menu Management

// Toggle burger menu
function toggleMenu() {
    const sidebar = document.getElementById('sidebar');
    const mainWrapper = document.getElementById('mainWrapper');
    const burgerIcon = document.querySelector('.burger-icon');
    
    sidebar.classList.toggle('active');
    mainWrapper.classList.toggle('shifted');
    burgerIcon.classList.toggle('active');
}

// Show specific section
function showSection(sectionName) {
    // Hide all sections
    const sections = document.querySelectorAll('.content-section');
    sections.forEach(section => {
        section.classList.remove('active');
    });
    
    // Remove active class from all menu items
    const menuItems = document.querySelectorAll('.sidebar-item');
    menuItems.forEach(item => {
        item.classList.remove('active');
    });
    
    // Show selected section
    const targetSection = document.getElementById('section-' + sectionName);
    if (targetSection) {
        targetSection.classList.add('active');
    }
    
    // Add active class to clicked menu item
    event.currentTarget.classList.add('active');
    
    // Close sidebar on mobile
    if (window.innerWidth <= 768) {
        toggleMenu();
    }
}

// Close sidebar when clicking outside
document.addEventListener('click', function(event) {
    const sidebar = document.getElementById('sidebar');
    const burgerMenu = document.getElementById('burgerMenu');
    
    if (sidebar.classList.contains('active')) {
        if (!sidebar.contains(event.target) && !burgerMenu.contains(event.target)) {
            toggleMenu();
        }
    }
});

// Initialize
window.onload = function() {
    // Show dashboard by default
    showSection('dashboard');
};