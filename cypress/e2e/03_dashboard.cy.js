describe('03 - Dashboard Quick Actions & Research Marquee', () => {
  before(() => {
    cy.resetDb();
  });

  beforeEach(() => {
    cy.loginAs('student');
    cy.visit('/dashboard/');
  });

  it('renders research marquee strip with ticker track and content', () => {
    cy.get('.top-marquee-strip').should('exist');
    cy.get('.marquee-track').should('exist');
    cy.contains(/LATEST RESEARCH/i).should('exist');
  });

  it('renders all 5 quick action cards with direct navigation links', () => {
    cy.get('.ums-quick-actions').should('exist');

    const expectedActions = [
      { text: 'Upload a Paper', href: '/papers/upload/' },
      { text: 'Start a Project', href: '/projects/create/' },
      { text: 'Book a Facility', href: '/facilities/' },
      { text: 'Find Collaborators', href: '/collaboration/recommendations/' },
      { text: 'Search Papers', href: '/search/' },
    ];

    expectedActions.forEach(({ text, href }) => {
      cy.get('.ums-quick-actions')
        .contains('a', text)
        .should('have.attr', 'href', href);
    });
  });

  it('navigates correctly from each quick action card', () => {
    cy.get('.ums-quick-actions').contains('a', 'Upload a Paper').click();
    cy.url().should('include', '/papers/upload/');

    cy.visit('/dashboard/');
    cy.get('.ums-quick-actions').contains('a', 'Start a Project').click();
    cy.url().should('include', '/projects/create/');

    cy.visit('/dashboard/');
    cy.get('.ums-quick-actions').contains('a', 'Book a Facility').click();
    cy.url().should('include', '/facilities/');

    cy.visit('/dashboard/');
    cy.get('.ums-quick-actions').contains('a', 'Find Collaborators').click();
    cy.url().should('include', '/collaboration/recommendations/');

    cy.visit('/dashboard/');
    cy.get('.ums-quick-actions').contains('a', 'Search Papers').click();
    cy.url().should('include', '/search/');
  });
});
