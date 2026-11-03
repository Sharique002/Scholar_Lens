describe('06 - Project Milestones, Risk Detection & At-Risk Board', () => {
  before(() => {
    cy.resetDb();
  });

  it('allows faculty member to add a milestone and view it on the timeline', () => {
    cy.loginAs('faculty');
    cy.visit('/projects/');
    cy.contains('a', 'Edge AI Lab').first().click();
    cy.contains('a', /timeline/i).click();

    cy.contains('a', /Add Milestone/i).click();
    cy.get('input[name="title"]').type('E2E Verification Milestone');
    cy.get('input[name="due_date"]').type('2026-12-15');
    cy.get('input[name="progress"]').clear().type('25');
    cy.get('select[name="status"]').select('IN_PROGRESS');
    cy.get('main button[type="submit"]').click();

    cy.url().should('include', '/milestones/');
    cy.contains('E2E Verification Milestone').should('exist');
  });

  it('detects dependency cycles and prevents loop creation', () => {
    cy.loginAs('faculty');

    // In seeded data: 'Model Training Pipeline' depends on 'Dataset Collection'.
    // Editing 'Dataset Collection' to depend on 'Model Training Pipeline' must fail with loop error.
    cy.visit('/projects/');
    cy.contains('a', 'Edge AI Lab').first().click();
    cy.contains('a', /timeline/i).click();

    // Click edit on Dataset Collection
    cy.contains('tr', 'Dataset Collection')
      .contains('a', /edit/i)
      .click();

    // Attempt to make it depend on Model Training Pipeline
    cy.get('select[name="depends_on"]').find('option').contains(/Model Training Pipeline/).then(($opt) => {
      cy.get('select[name="depends_on"]').select($opt.val());
    });
    cy.get('main button[type="submit"]').click();

    cy.contains(/That would create a loop/i).should('exist');
  });

  it('runs check_milestone_risk and verifies risk status and notifications', () => {
    // Run the risk evaluation management command
    cy.runCommand('check_milestone_risk');

    // Faculty (leader) sees notifications
    cy.loginAs('faculty');
    cy.visit('/dashboard/notifications/');
    cy.contains(/milestone|risk|overdue/i).should('exist');

    // Research Office sees at-risk milestones on the At-risk board
    cy.loginAs('office');
    cy.visit('/projects/at-risk/');
    cy.contains('Hardware Architecture Design').should('exist');
    cy.contains(/OVERDUE|At risk/i).should('exist');
  });

  it('forbids students from accessing the At-risk board (403)', () => {
    cy.loginAs('student');
    cy.request({
      url: '/projects/at-risk/',
      failOnStatusCode: false,
    }).then((resp) => {
      expect(resp.status).to.eq(403);
    });
  });
});
