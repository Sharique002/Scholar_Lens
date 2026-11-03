describe('02 - Mobile Responsive Layout', () => {
  before(() => {
    cy.resetDb();
  });

  beforeEach(() => {
    cy.viewport(375, 812);
  });

  it('hides sidebar by default and toggles via hamburger button', () => {
    cy.loginAs('student');
    cy.visit('/dashboard/');

    // In mobile, sidebar does not have .active class
    cy.get('aside.ums-sidebar').should('not.have.class', 'active');

    // Click hamburger button to open
    cy.get('#mobileMenuBtn').click();
    cy.get('aside.ums-sidebar').should('have.class', 'active');

    // Clicking a link navigates and closes drawer
    cy.get('aside.ums-sidebar a[href*="/papers/"]').first().click();
    cy.url().should('include', '/papers/');
    cy.get('aside.ums-sidebar').should('not.have.class', 'active');
  });

  it('hides header search in mobile view while retaining search in sidebar', () => {
    cy.loginAs('student');
    cy.visit('/dashboard/');
    cy.get('.ums-header-search').should('not.be.visible');

    // Sidebar search is available
    cy.get('#mobileMenuBtn').click();
    cy.get('aside.ums-sidebar').should('contain', 'Search');
  });

  it('guarantees no horizontal scrolling on 375px mobile viewport across key views', () => {
    cy.loginAs('office');

    const urls = [
      '/dashboard/',
      '/papers/',
      '/facilities/1/',
      '/funding/',
      '/analytics/research/',
    ];

    urls.forEach((url) => {
      cy.visit(url);
      cy.window().then((win) => {
        expect(win.document.documentElement.scrollWidth).to.be.at.most(375);
      });
    });
  });
});
