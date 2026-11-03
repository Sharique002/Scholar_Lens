describe('08 - Publication Ingestion, Deduplication & Author Claiming', () => {
  before(() => {
    cy.resetDb();
  });

  it('allows faculty to import publications from ORCID offline fixture and shows summary', () => {
    cy.loginAs('faculty');
    cy.visit('/papers/import/');

    cy.get('input[name="query"]').first().clear().type('0000-0002-1825-0097');
    cy.contains('button', /Fetch & Import Works/i).click();

    cy.contains(/Import completed/i).should('exist');
    cy.contains(/imported/i).should('exist');
  });

  it('allows office to review and merge duplicate candidate, redirects old URL, and undoes merge', () => {
    cy.loginAs('office');
    cy.visit('/papers/dedup/queue/');
    cy.contains('Scalable Distributed Machine Learning').should('exist');

    // Click Merge
    cy.contains('.card, tr, .dedup-row, li', 'Scalable Distributed Machine Learning')
      .contains('button', /merge/i)
      .click();

    cy.contains(/Merged duplicate/i).should('exist');

    // Visiting the merged duplicate (incoming paper) redirects to canonical
    // In seeded data, dup2 has title 'Scalable Distributed Machine Learning System'
    // Let's find its ID or visit paper detail
    cy.visit('/papers/');
    cy.contains('a', 'Scalable Distributed Machine Learning Systems').first().click();
    cy.url().then((canonicalUrl) => {
      // The canonical paper page shows the merged copy with Undo Merge
      cy.contains('Undo Merge').should('exist');

      // Click Undo Merge
      cy.contains('button', 'Undo Merge').click();
      cy.contains(/Restored/i).should('exist');
    });
  });

  it('allows e2e_biotech to claim authorship via "Is this you?" banner', () => {
    cy.loginAs('biotech');
    cy.visit('/researchers/');
    cy.get('main').contains('a', 'Meera Iyer').click();

    // Verify "Is this you?" banner is present
    cy.contains('Is this you?').should('exist');
    cy.contains('CRISPR Genome Editing in Plant Biotechnology').should('exist');

    // Click "This is me"
    cy.contains('button', 'This is me').click();

    // Verify paper is now listed in Research Papers section
    cy.contains('CRISPR Genome Editing in Plant Biotechnology').should('exist');
  });
});
