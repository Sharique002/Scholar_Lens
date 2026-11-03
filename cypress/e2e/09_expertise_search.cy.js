describe('09 - Faceted Full-Text Expertise Search', () => {
  before(() => {
    cy.resetDb();
  });

  it('displays hint text when query is empty', () => {
    cy.loginAs('student');
    cy.visit('/search/expertise/');

    cy.contains(/Hint|search across/i).should('exist');
  });

  it('searches "machine learning" and returns researchers from both CSE and Biotechnology', () => {
    cy.loginAs('student');
    cy.visit('/search/expertise/?q=machine+learning');

    // Vikram Singh from CSE and Meera Iyer from BTB both have machine learning interests
    cy.contains('Vikram Singh').should('exist');
    cy.contains('Meera Iyer').should('exist');
    cy.contains('CSE').should('exist');
    cy.contains('BTB').should('exist');
  });

  it('narrows results using department facet filter', () => {
    cy.loginAs('student');
    cy.visit('/search/expertise/?q=machine+learning');

    // Click on Biotechnology department facet
    cy.contains('.card a', 'Biotechnology').click();

    // Now only Biotech researchers should show
    cy.contains('Meera Iyer').should('exist');
    cy.contains('Vikram Singh').should('not.exist');
  });

  it('filters results with Verified-only toggle', () => {
    cy.loginAs('student');
    // Initially unverified Asha Rao is in CSE
    cy.visit('/search/expertise/?department=CSE');
    cy.get('.row-cols-1').contains('Asha Rao').should('exist');

    // Toggle Verified only
    cy.contains('.card a', /Verified only/i).click();

    // Asha Rao is unverified, so she should be filtered out from results
    cy.get('.row-cols-1').should('not.contain', 'Asha Rao');
    cy.get('.row-cols-1').contains('Vikram Singh').should('exist');
  });
});
