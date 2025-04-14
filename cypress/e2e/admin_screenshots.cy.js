describe('Admin Interface Screenshots', () => {
  beforeEach(() => {
    // Check if server is running instead of starting it
    cy.request({
      url: 'http://localhost:8000/admin/',
      failOnStatusCode: false
    }).then((response) => {
      if (response.status !== 200) {
        throw new Error('Django server is not running. Please start it with: python manage.py runserver')
      }
    })
  })

  it('captures admin screenshots', () => {
    // Visit the admin interface
    cy.visit('http://localhost:8000/admin/')
    
    // Debug: Log the current URL and page content
    cy.url().then(url => cy.log('Current URL:', url))

    // Login with proper credentials
    cy.get('#id_username').type('josh')
    cy.get('#id_password').type('joshjosh')
    cy.get('input[type="submit"]').click()

    // Wait for login to complete and ensure we're on the admin page
    cy.url().should('include', '/admin/')
    
    // Take screenshot of the admin dashboard first
    cy.screenshot('admin-dashboard')

    // Navigate to each model's admin page
    cy.visit('http://localhost:8000/admin/sync_option/optiongroup/')
    cy.url().should('include', '/admin/sync_option/optiongroup/')
    cy.screenshot('admin-option-groups')

    cy.visit('http://localhost:8000/admin/sync_option/option/')
    cy.url().should('include', '/admin/sync_option/option/')
    cy.screenshot('admin-options')

    cy.visit('http://localhost:8000/admin/sync_option/optionrelation/')
    cy.url().should('include', '/admin/sync_option/optionrelation/')
    cy.screenshot('admin-option-relations')
  })
}) 