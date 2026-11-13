describe('15 - Redesigned shell interactions', () => {
  before(() => {
    cy.resetDb();
  });

  it('groups navigation and shows labels as tooltips when collapsed', () => {
    cy.loginAs('student');
    cy.visit('/dashboard/');
    cy.get('aside.ums-sidebar .sb-group-label').should('contain', 'Research').and('contain', 'People');
    cy.get('aside.ums-sidebar a.ums-nav-link[data-tip="Papers"]').should('exist');
    cy.get('.ums-role-badge').should('contain', 'Student');
    cy.get('#sidebarCollapse').click();
    cy.get('html').should('have.class', 'sb-collapsed');
    cy.get('aside.ums-sidebar .ums-nav-label').first().should('not.be.visible');
    cy.get('#sidebarCollapse').click(); // leave expanded for later tests
  });

  it('mobile drawer closes with the backdrop and with Escape', () => {
    cy.viewport(375, 812);
    cy.loginAs('student');
    cy.visit('/dashboard/');
    cy.get('#mobileMenuBtn').click();
    cy.get('aside.ums-sidebar').should('have.class', 'active');
    cy.get('#mobileMenuBtn').should('have.attr', 'aria-expanded', 'true');
    cy.get('#sidebarBackdrop').click({ force: true });
    cy.get('aside.ums-sidebar').should('not.have.class', 'active');
    cy.get('#mobileMenuBtn').click();
    cy.get('body').type('{esc}');
    cy.get('aside.ums-sidebar').should('not.have.class', 'active');
  });

  it('"/" focuses global search', () => {
    cy.loginAs('student');
    cy.visit('/dashboard/');
    cy.get('body').type('/');
    cy.focused().should('have.attr', 'id', 'globalSearch');
  });

  it('dashboard shows live summary counts and no invented scores', () => {
    cy.loginAs('faculty');
    cy.visit('/dashboard/');
    cy.get('.stat-card').should('have.length', 6);
    cy.contains('94.8').should('not.exist');
    cy.contains('85.0 / 100').should('not.exist');
    cy.contains('h2', 'Upcoming deadlines').should('exist');
  });

  it('confirmation dialog can be dismissed without submitting', () => {
    cy.loginAs('faculty');
    cy.visit('/projects/1/milestones/');
    cy.get('form[data-confirm] button[type="submit"]').first().click({ force: true });
    cy.get('#confirmDialog').should('be.visible');
    cy.contains('#confirmDialog button', 'Go back').click();
    cy.get('#confirmDialog').should('not.be.visible');
    cy.url().should('include', '/projects/1/milestones/');
  });

  it('paper detail tabs switch panels', () => {
    cy.loginAs('faculty');
    cy.visit('/papers/');
    cy.get('main a[href^="/papers/"]').filter((i, a) => /^\/papers\/\d+\/$/.test(a.getAttribute('href'))).first().click();
    cy.get('[data-bs-toggle="tab"]').then(($tabs) => {
      if ($tabs.length < 2) return; // some papers have a single panel
      cy.wrap($tabs.eq(1)).click().should('have.attr', 'aria-selected', 'true');
      cy.get($tabs.eq(1).attr('data-bs-target')).should('be.visible');
      cy.get($tabs.eq(0).attr('data-bs-target')).should('not.be.visible');
    });
  });

  it('no horizontal overflow at tablet width', () => {
    cy.viewport(768, 1024);
    cy.loginAs('office');
    ['/dashboard/', '/researchers/', '/projects/1/milestones/', '/facilities/my-bookings/', '/dashboard/office/'].forEach((url) => {
      cy.visit(url);
      cy.window().then((win) => {
        expect(win.document.documentElement.scrollWidth, url).to.be.at.most(768);
      });
    });
  });
});
