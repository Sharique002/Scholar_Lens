describe('10 - Collaboration Suggestions & Network Graph', () => {
  before(() => {
    cy.resetDb();
  });

  it('computes collaboration suggestions and displays "Suggested for you" with reasons', () => {
    cy.runCommand('compute_collaboration_suggestions');

    cy.loginAs('student');
    cy.visit('/collaboration/recommendations/');

    cy.contains('Suggested for you').should('exist');
    cy.contains(/Adjacency|Co-authorship Gap/i).should('exist');
    cy.contains(/Collaboration Potential/i).should('exist');
  });

  it('allows student to dismiss a suggestion via "Not interested"', () => {
    cy.loginAs('student');
    cy.visit('/collaboration/recommendations/');

    cy.get('button').contains(/Not interested/i).first().click();
    cy.contains(/Dismissed|Removed/i).should('exist');
  });

  it('opens collaboration request form when clicking "Send request"', () => {
    cy.loginAs('student');
    cy.visit('/collaboration/recommendations/');

    cy.contains('a', /Send request/i).first().click();
    cy.url().should('include', '/collaboration/send/');
    cy.get('form').should('exist');
  });

  it('renders Cytoscape graph canvas and accessible fallback table on graph page', () => {
    cy.loginAs('student');
    cy.visit('/collaboration/graph/');

    // Cytoscape visualization container
    cy.get('#cy').should('exist').and('be.visible');

    // Accessible fallback table
    cy.get('table').should('exist');
    cy.contains('th', 'Researcher').should('exist');
  });
});
