describe('12 - Institutional Analytics, Dean Confidentiality & CSV Export', () => {
  before(() => {
    cy.resetDb();
  });

  it('forbids students from accessing reports (403) and hides Reports sidebar link', () => {
    cy.loginAs('student');
    cy.visit('/dashboard/');
    cy.sidebar().should('not.contain', 'Reports');

    cy.request({
      url: '/analytics/research/',
      failOnStatusCode: false,
    }).then((resp) => {
      expect(resp.status).to.eq(403);
    });
  });

  it('allows office staff to view departmental reports without researcher productivity', () => {
    cy.loginAs('office');
    cy.visit('/analytics/research/');

    cy.contains('Departmental Productivity').should('exist');
    cy.contains('Individual Researcher Productivity').should('not.exist');
  });

  it('allows Dean of Research to view confidential researcher productivity with caution note', () => {
    cy.loginAs('dean');
    cy.visit('/analytics/research/');

    cy.contains('Departmental Productivity').should('exist');
    cy.contains('Individual Researcher Productivity').should('exist');
    cy.contains(/Caution|Confidential/i).should('exist');
  });

  it('switches academic years using the year selector', () => {
    cy.loginAs('office');
    cy.visit('/analytics/research/?year=2024-2025');

    cy.url().should('include', 'year=2024-2025');
    cy.contains(/Academic Year.*2024-2025/i).should('exist');
  });

  it('exports section=all CSV with departmental metrics and restricts researcher rows for office', () => {
    cy.loginAs('office');
    cy.request('/analytics/research/?section=all').then((resp) => {
      expect(resp.status).to.eq(200);
      expect(resp.headers['content-type']).to.include('text/csv');
      expect(resp.body).to.include('Departmental Productivity Report');
      expect(resp.body).to.not.include('Individual Researcher Productivity');
    });

    cy.loginAs('dean');
    cy.request('/analytics/research/?section=all').then((resp) => {
      expect(resp.status).to.eq(200);
      expect(resp.body).to.include('Individual Researcher Productivity');
    });
  });
});
