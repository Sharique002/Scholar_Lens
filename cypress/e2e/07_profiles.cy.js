describe('07 - Researcher Profiles, Taxonomy & Verification Workflow', () => {
  before(() => {
    cy.resetDb();
  });

  it('validates ORCID checksum, updates profile, and submits verification request', () => {
    cy.loginAs('student');
    cy.visit('/researchers/profile/edit/');

    // Select department
    cy.get('select[name="department"]').find('option').contains(/CSE/).then(($opt) => {
      cy.get('select[name="department"]').select($opt.val());
    });

    // Enter invalid ORCID
    cy.get('input[name="orcid_id"]').clear().type('0000-0002-1825-0000');
    cy.contains('button', 'Save Profile').click();

    // Verify error is shown
    cy.contains(/Enter a valid ORCID iD/i).should('exist');

    // Enter valid ORCID
    cy.get('input[name="orcid_id"]').clear().type('0000-0002-1825-0097');
    cy.contains('button', 'Save Profile').click();

    cy.contains(/Profile updated successfully/i).should('exist');

    // Request verification
    cy.contains('button', /Request Verification/i).click();
    cy.contains('Verification pending').should('exist');
  });

  it('allows Research Office to approve verification from the review queue', () => {
    cy.loginAs('office');
    cy.visit('/researchers/verification/queue/');
    cy.contains('Asha Rao').should('exist');

    // Approve verification
    cy.contains('.ums-card, tr, .verification-row, li', 'Asha Rao')
      .contains('button', /approve/i)
      .click();

    cy.visit('/researchers/verification/queue/');
    cy.contains('Asha Rao').should('not.exist');

    // Student profile now displays verified badge
    cy.loginAs('student');
    cy.visit('/dashboard/');
    cy.get('.dropdown-toggle').click();
    cy.contains('a', /Researcher Profile/i).click();
    cy.contains('Verified').should('exist');
  });

  it('forbids students from accessing the verification review queue (403)', () => {
    cy.loginAs('student');
    cy.request({
      url: '/researchers/verification/queue/',
      failOnStatusCode: false,
    }).then((resp) => {
      expect(resp.status).to.eq(403);
    });
  });
});
