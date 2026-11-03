describe('05 - Funding Calls & Deadline Reminders', () => {
  before(() => {
    cy.resetDb();
  });

  it('renders countdown pills and closed section, and filters by research area', () => {
    cy.loginAs('student');
    cy.visit('/funding/');

    // Countdown pills
    cy.contains(/3 days left/i).should('exist');
    cy.contains(/10 days left/i).should('exist');

    // Closed call in Closed section
    cy.contains(/Closed Opportunities/i).should('exist');
    cy.contains('Past Robotics Challenge').should('exist');

    // Filter by research area (AI)
    cy.get('select[name="area"]').select('AI');
    cy.contains('button', 'Filter').click();
    cy.contains('AI for Healthcare Initiative').should('exist');
    cy.contains('Quantum Computing Seed Grant').should('not.exist');
  });

  it('allows student to toggle watch on the 25-day call', () => {
    cy.loginAs('student');
    cy.visit('/funding/');

    // Open detail of Clean Energy Innovation Fund (the 25-day call)
    cy.contains('a', 'Clean Energy Innovation Fund').first().click();
    cy.contains('button', /Watch/i).click();

    cy.contains("You'll get deadline reminders").should('exist');
  });

  it('sends funding alerts without duplicates', () => {
    cy.loginAs('student');

    // Run management command
    cy.runCommand('send_funding_alerts');

    // Check notifications
    cy.visit('/dashboard/notifications/');
    cy.contains(/funding|deadline|initiative/i).should('exist');

    // Capture count of notifications
    cy.get('.activity-item-retro').then(($items) => {
      const initialCount = $items.length;

      // Run second time (idempotent)
      cy.runCommand('send_funding_alerts');
      cy.visit('/dashboard/notifications/');
      cy.get('.activity-item-retro').should('have.length', initialCount);
    });
  });

  it('forbids students from creating calls (403) while allowing staff', () => {
    cy.loginAs('student');
    cy.request({
      url: '/funding/create/',
      failOnStatusCode: false,
    }).then((resp) => {
      expect(resp.status).to.eq(403);
    });

    cy.loginAs('office');
    cy.visit('/funding/create/');
    cy.contains(/Add Funding Call|Create/i).should('exist');
  });
});
