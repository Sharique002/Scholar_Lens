describe('01 - Institutional Shell & Navigation', () => {
  before(() => {
    cy.resetDb();
  });

  it('shows guest header with Sign In and Register, and no sidebar for guests', () => {
    ['/', '/accounts/login/', '/accounts/register/'].forEach((url) => {
      cy.visit(url);
      cy.get('aside.ums-sidebar').should('not.exist');
      cy.contains('a', /sign in|login/i).should('exist');
      cy.contains('a', /register/i).should('exist');
    });
  });

  it('shows exactly 9 sidebar links in flat order for students without Reports', () => {
    cy.loginAs('student');
    cy.visit('/dashboard/');
    cy.sidebar().should('exist');

    const expectedOrder = [
      'Dashboard',
      'Papers',
      'Projects',
      'Openings',
      'Researchers',
      'Collaboration',
      'Facilities',
      'Funding',
      'Search',
    ];

    cy.get('aside.ums-sidebar a.ums-nav-link').then(($links) => {
      expect($links).to.have.length(9);
      expectedOrder.forEach((label, idx) => {
        expect($links.eq(idx).text()).to.include(label);
      });
    });

    cy.sidebar().should('not.contain', 'Reports');
  });

  it('shows Reports link for staff and Dean', () => {
    cy.loginAs('office');
    cy.visit('/dashboard/');
    cy.sidebar().should('contain', 'Reports');

    cy.loginAs('dean');
    cy.visit('/dashboard/');
    cy.sidebar().should('contain', 'Reports');
  });

  it('highlights active navigation item and displays breadcrumbs', () => {
    cy.loginAs('student');
    cy.visit('/papers/upload/');
    cy.get('aside.ums-sidebar a.ums-nav-link.is-active').should('contain', 'Papers');
    cy.get('.ums-breadcrumbs').should('exist').and('contain', 'Home').and('contain', 'Papers');
  });

  it('opens account dropdown menu with role-appropriate items', () => {
    cy.loginAs('student');
    cy.visit('/dashboard/');
    cy.get('.dropdown-toggle').click();
    cy.get('.nav-dropdown').should('be.visible');
    cy.get('.nav-dropdown').should('contain', 'My Profile');
    cy.get('.nav-dropdown').should('not.contain', 'Admin Panel');

    cy.loginAs('office');
    cy.visit('/dashboard/');
    cy.get('.dropdown-toggle').click();
    cy.get('.nav-dropdown').should('be.visible').and('contain', 'Admin Panel');
  });

  it('notification bell links to notifications', () => {
    cy.loginAs('student');
    cy.visit('/dashboard/');
    cy.get('a[aria-label="Notifications"], a.ums-bell-btn').first().click();
    cy.url().should('include', '/dashboard/notifications/');
  });

  it('header search for "learning" redirects to search results', () => {
    cy.loginAs('student');
    cy.visit('/dashboard/');
    cy.get('.ums-header-search input[name="q"], input[aria-label="Search papers and researchers"]')
      .first()
      .type('learning{enter}');
    cy.url().should('include', '/search/?q=learning');
  });

  it('toggles sidebar collapse state and persists across page reload', () => {
    cy.loginAs('student');
    cy.visit('/dashboard/');
    cy.get('#sidebarCollapse').click();
    cy.get('aside.ums-sidebar').should('have.class', 'is-collapsed');

    cy.reload();
    cy.get('aside.ums-sidebar').should('have.class', 'is-collapsed');

    // Uncollapse
    cy.get('#sidebarCollapse').click();
    cy.get('aside.ums-sidebar').should('not.have.class', 'is-collapsed');
  });

  it('ensures footer has no public ratings or fake scores', () => {
    cy.visit('/');
    cy.contains('PUBLIC RATINGS').should('not.exist');
    cy.contains('9.85/10').should('not.exist');
  });
});
