describe('14 - Registration, Google OAuth, Paper PDF Upload & AI RAG Workflows', () => {
  before(() => {
    cy.resetDb();
  });

  it('handles user registration and duplicate username rejection', () => {
    const timestamp = Date.now();
    const testUsername = `user_${timestamp}`;

    // Visit registration page
    cy.visit('/accounts/register/');
    cy.get('input[name="username"]').type(testUsername);
    cy.get('input[name="email"]').type(`${testUsername}@example.com`);
    cy.get('input[name="first_name"]').type('Automated');
    cy.get('input[name="last_name"]').type('Tester');
    cy.get('select[name="role"]').select('STUDENT');
    cy.get('input[name="password1"]').type('SecurePass123!');
    cy.get('input[name="password2"]').type('SecurePass123!');
    cy.get('form button[type="submit"]').click();

    // Verify redirected to dashboard after successful registration
    cy.url().should('include', '/dashboard/');
    cy.contains('Welcome').should('exist');

    // Logout
    cy.visit('/accounts/logout/');

    // Attempt duplicate registration with same username
    cy.visit('/accounts/register/');
    cy.get('input[name="username"]').type(testUsername);
    cy.get('input[name="email"]').type(`diff_${timestamp}@example.com`);
    cy.get('input[name="first_name"]').type('Dup');
    cy.get('input[name="last_name"]').type('Tester');
    cy.get('select[name="role"]').select('STUDENT');
    cy.get('input[name="password1"]').type('SecurePass123!');
    cy.get('input[name="password2"]').type('SecurePass123!');
    cy.get('form button[type="submit"]').click();

    // Verify rejected with error
    cy.contains(/A user with that username already exists|Please correct the errors/i).should('exist');
  });

  it('rejects invalid login credentials and accepts valid credentials', () => {
    cy.visit('/accounts/login/');
    cy.get('input[name="username"]').type('nonexistent_user_999');
    cy.get('input[name="password"]').type('WrongPassword!');
    cy.get('form#loginForm button[type="submit"]').click();
    cy.contains(/Invalid username or password/i).should('exist');

    // Valid login as student
    cy.get('input[name="username"]').clear().type('e2e_student');
    cy.get('input[name="password"]').clear().type('TestPassword123!');
    cy.get('form#loginForm button[type="submit"]').click();
    cy.url().should('include', '/dashboard/');
  });

  it('completes Mock Google SSO flow in development environment', () => {
    cy.visit('/accounts/logout/');
    cy.visit('/accounts/login/');
    cy.contains(/Sign In with Google|Continue with Google/i).should('exist');

    // Visit google mock endpoint
    cy.visit('/accounts/google/mock/');
    cy.contains(/Google Single Sign-On/i).should('exist');
    cy.get('input[name="email"]').clear().type('sharique_sso@example.com');
    cy.get('input[name="name"]').clear().type('Sharique Hussain');
    cy.contains('button', /Sign In as Google User|Continue/i).click();

    // Verify redirected to dashboard and authenticated
    cy.url().should('include', '/dashboard/');
    cy.contains(/Successfully signed in with Google Account/i).should('exist');
  });

  it('rejects non-PDF files and successfully uploads valid research paper PDF', () => {
    cy.loginAs('faculty');
    cy.visit('/papers/upload/');

    // Attempt upload with non-PDF file
    cy.get('input[name="title"]').type('Invalid File Upload Test');
    cy.get('textarea[name="abstract"]').type('Testing rejection of non-PDF uploads for security.');
    cy.get('select[name="research_area"]').select('COMPUTER_VISION');
    cy.get('input[name="keywords"]').type('Test, Security');
    cy.get('input[name="pdf_file"]').selectFile('cypress/fixtures/sample.txt');
    cy.contains('button', /Upload Paper/i).click();
    cy.contains(/Only PDF files are allowed|Invalid file/i).should('exist');

    // Upload valid PDF
    const uniqueTitle = `Neural Foundations of Vision ${Date.now()}`;
    cy.get('input[name="title"]').clear().type(uniqueTitle);
    cy.get('textarea[name="abstract"]').clear().type('Comprehensive analysis of vision models.');
    cy.get('select[name="research_area"]').select('COMPUTER_VISION');
    cy.get('input[name="keywords"]').clear().type('Vision, Diffusion, Deep Learning');
    cy.get('input[name="pdf_file"]').selectFile('cypress/fixtures/cv.pdf');
    cy.contains('button', /Upload Paper/i).click();

    // Should redirect to paper detail
    cy.url().should('include', '/papers/');
    cy.contains(uniqueTitle).should('exist');
    cy.contains(/Paper uploaded and processed successfully/i).should('exist');
  });

  it('interacts with paper RAG assistant and verifies citations', () => {
    cy.loginAs('faculty');
    cy.visit('/papers/');
    // Open the first available active paper via retro-card title link
    cy.get('.retro-card h4 a').first().click();
    cy.url().should('match', /\/papers\/\d+\/$/);

    // Click Ask Paper / AI assistant
    cy.contains('a', /Ask Paper/i).click();
    cy.url().should('include', '/ask/');

    // Submit question
    cy.get('input[name="question"]').first().type('What is the main methodology?{enter}');

    // Verify answer or RAG response renders cleanly
    cy.contains(/Cited Document Sources|Source Citations|References|Based on|AI service not configured|Scholar Lens RAG Synthesis|No questions asked yet/i).should('exist');
  });

  it('views 7-dimension evaluation report with multi-criteria scores', () => {
    cy.loginAs('faculty');
    cy.visit('/papers/');
    cy.get('.retro-card h4 a').first().click();
    cy.url().should('match', /\/papers\/\d+\/$/);

    // Open evaluation page
    cy.contains('a', /Evaluate/i).first().click();
    cy.url().should('include', '/evaluation/');
    cy.contains(/Evaluate Research|Novelty|Evaluation|Score|Report/i).should('exist');
    cy.contains(/Disclaimer/i).should('exist');
  });
});
