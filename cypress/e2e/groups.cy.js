describe('Groups Page', () => {
  beforeEach(() => {
    // Clear IndexedDB before each test
    cy.window().then((win) => {
      return new Promise((resolve, reject) => {
        const request = win.indexedDB.deleteDatabase('optionsDB');
        request.onsuccess = resolve;
        request.onerror = reject;
      });
    });

    // Visit the groups page
    cy.visit('/groups/');
  });

  it('should load the page and display the table', () => {
    // Check if the page title exists
    cy.get('h1').should('contain', 'Option Groups');

    // Check if the table exists with correct headers
    cy.get('table#groupsTable').should('exist');
    cy.get('th').should('have.length', 4);
    cy.get('th').eq(0).should('contain', 'Name');
    cy.get('th').eq(1).should('contain', 'English Name');
    cy.get('th').eq(2).should('contain', 'English Description');
    cy.get('th').eq(3).should('contain', 'Last Updated');

    // Check if last sync time is displayed
    cy.get('#lastSync').should('exist');
  });

  it('should initialize IndexedDB', () => {
    // Check if IndexedDB is initialized
    cy.window().then((win) => {
      const request = win.indexedDB.open('optionsDB');
      request.onsuccess = () => {
        const db = request.result;
        expect(db.objectStoreNames.contains('optionGroups')).to.be.true;
        db.close();
      };
    });
  });

  it('should fetch and display groups from the API', () => {
    // Wait for the table to be populated
    cy.get('#groupsTableBody tr', { timeout: 10000 }).should('exist');

    // Check if the table has rows
    cy.get('#groupsTableBody tr').should('have.length.gt', 0);

    // Check if each row has the correct number of cells
    cy.get('#groupsTableBody tr').each(($row) => {
      cy.wrap($row).find('td').should('have.length', 4);
    });
  });

  it('should update the last sync time', () => {
    // Wait for initial sync
    cy.get('#lastSyncTime', { timeout: 10000 }).should('not.contain', 'Never');

    // Get the initial sync time
    cy.get('#lastSyncTime').then(($time) => {
      const initialTime = $time.text();

      // Wait for the next sync (5 seconds)
      cy.wait(6000);

      // Check if the sync time has updated
      cy.get('#lastSyncTime').should('not.contain', initialTime);
    });
  });

  it('should handle API errors gracefully', () => {
    // Intercept the API request and force an error
    cy.intercept('GET', '/api/options/groups*', {
      statusCode: 500,
      body: { error: 'Internal Server Error' }
    });

    // Check if the error is logged in the console
    cy.window().then((win) => {
      cy.spy(win.console, 'error').as('consoleError');
    });

    // Wait for the error to be logged
    cy.get('@consoleError').should('have.been.called');
  });
}); 