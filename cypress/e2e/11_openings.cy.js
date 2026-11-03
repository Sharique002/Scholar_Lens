describe('11 - Research Opportunities Board & Application Workflow', () => {
  before(() => {
    cy.resetDb();
  });

  it('displays recommended opening with matching percentage and notification for student', () => {
    cy.loginAs('student');
    cy.visit('/opportunities/');

    // Recommended section with matching score
    cy.contains('Recommended for You').should('exist');
    cy.contains('Undergraduate ML Researcher').should('exist');
    cy.contains(/You match 100%/i).should('exist');

    // Notification check
    cy.visit('/dashboard/notifications/');
    cy.contains(/Undergraduate ML Researcher/i).should('exist');
  });

  it('rejects invalid file upload (.txt) and accepts PDF upload (cv.pdf)', () => {
    cy.loginAs('student');
    cy.visit('/opportunities/');
    cy.get('main').contains('a', 'Undergraduate ML Researcher').first().click();

    // 1. Attempt upload with .txt file
    cy.get('textarea[name="statement"]').clear().type('My statement of interest for ML research.');
    cy.get('input[name="cv_pdf"]').selectFile('cypress/fixtures/sample.txt');
    cy.contains('button', /Submit Application/i).click();

    // Error about PDF file
    cy.contains(/PDF/i).should('exist');

    // 2. Submit valid PDF upload
    cy.get('textarea[name="statement"]').clear().type('My statement of interest with PDF CV.');
    cy.get('input[name="cv_pdf"]').selectFile('cypress/fixtures/cv.pdf');
    cy.contains('button', /Submit Application/i).click();

    cy.contains(/submitted successfully/i).should('exist');
    cy.contains('PENDING').should('exist');
  });

  it('rejects duplicate application to the same opening', () => {
    cy.loginAs('student');
    cy.visit('/opportunities/1/');
    // When already applied, the form is not displayed and status is visible
    cy.contains('Application Status:').should('exist');
    cy.contains('PENDING').should('exist');
    cy.get('textarea[name="statement"]').should('not.exist');
  });

  it('faculty member shortlists then accepts applicant; opening shows Filled and member appears in project', () => {
    cy.loginAs('faculty');
    cy.visit('/opportunities/1/');

    // Candidate application table
    cy.contains('Asha Rao').should('exist');

    // 1. Shortlist
    cy.contains('button', /Shortlist/i).click();
    cy.contains('SHORTLISTED').should('exist');

    // 2. Select / Accept
    cy.contains('button', /Accept/i).click();
    cy.contains('ACCEPTED').should('exist');

    // Opening shows Filled
    cy.visit('/opportunities/1/');
    cy.contains('Filled').should('exist');

    // Verify student appears in Edge AI Lab project members
    cy.visit('/projects/');
    cy.get('main').contains('a', 'Edge AI Lab').first().click();
    cy.contains(/Asha Rao|e2e_student/i).should('exist');
  });

  it('allows student to withdraw a different application', () => {
    cy.loginAs('student');
    // Seeded second application is on opening 2 (Junior Systems Assistant)
    cy.visit('/opportunities/2/');
    cy.contains('Junior Systems Assistant').should('exist');
    cy.contains('button', 'Withdraw Application').click();

    cy.contains(/withdrawn/i).should('exist');
  });
});
